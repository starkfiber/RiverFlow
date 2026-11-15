"""Independent integer oracle and immutable native black-box cases, no model calls."""
from pathlib import Path
import argparse, ast, hashlib, json, os, random, re, subprocess, tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
HEADER=b'sensor_id,timestamp_ms,temperature_mC'
U64=2**64-1

def canonical(raw,minimum,maximum):
    if not re.fullmatch(rb'0|[1-9][0-9]*|-[1-9][0-9]*',raw):raise ValueError('canonical integer')
    value=int(raw)
    if not minimum<=value<=maximum:raise ValueError('range')
    return value

def oracle(data,low=0,high=50000):
    if len(data)>1048576:raise ValueError('input bound')
    # Only LF or CRLF is accepted; final bare CR is not a line terminator.
    lines=data.split(b'\n')
    if lines[-1]==b'':lines.pop()
    normalized=[]
    for i,line in enumerate(lines):
        has_lf=i<len(lines)-1 or data.endswith(b'\n')
        normalized.append(line[:-1]if has_lf and line.endswith(b'\r')else line)
    if not normalized or normalized[0]!=HEADER:raise ValueError('header')
    if len(normalized)-1>4096:raise ValueError('row count')
    sensors={}
    for line in normalized[1:]:
        if not 0<len(line)<=128:raise ValueError('record size')
        fields=line.split(b',')
        if len(fields)!=3:raise ValueError('shape')
        ident=canonical(fields[0],1,32);stamp=canonical(fields[1],0,U64);temp=canonical(fields[2],-100000,200000)
        row=sensors.setdefault(ident,[])
        if row and stamp<=row[-1][0]:raise ValueError('sensor time order')
        row.append((stamp,temp))
    result=[]
    for ident,rows in sorted(sensors.items()):
        temps=[row[1]for row in rows];total=sum(temps)
        result.append(dict(id=ident,count=len(rows),first_ms=rows[0][0],last_ms=rows[-1][0],minimum_mC=min(temps),maximum_mC=max(temps),sum_mC=total,mean=dict(numerator_mC=total,denominator=len(rows)),below_low=sum(v<low for v in temps),above_high=sum(v>high for v in temps)))
    return dict(schema='rf2.sensor-audit.v1',rows=len(normalized)-1,low_mC=low,high_mC=high,sensors=result)

def cases():
    yield 'header-only',HEADER+b'\n',None
    yield 'signed-and-interleaved',HEADER+b'\n1,0,-100000\n2,0,200000\n1,1,0\n2,1,50000\n',None
    yield 'maximum-timestamp',HEADER+b'\n32,18446744073709551614,-1\n32,18446744073709551615,1',(-1,1)
    yield 'javascript-precision-boundary',HEADER+b'\n1,9007199254740991,-1\n1,9007199254740992,0\n1,9007199254740993,1\n',None
    yield 'crlf',HEADER+b'\r\n1,0,0\r\n1,1,50000\r\n',None
    yield 'signed-thresholds',HEADER+b'\n1,0,-2000\n1,1,-1000\n1,2,0\n1,3,1000\n1,4,2000\n',(-1000,1000)
    rng=random.Random(49017)
    for case in range(100):
        last={};lines=[]
        for _ in range(rng.randrange(1,250)):
            ident=rng.randrange(1,33);stamp=last.get(ident,0)+rng.randrange(1,5000);last[ident]=stamp
            lines.append(f'{ident},{stamp},{rng.randrange(-100000,200001)}'.encode())
        low=rng.randrange(-100000,100000);high=rng.randrange(low,200001)
        ending=b'\n'if case%2 else b''
        yield 'generated-'+str(case),HEADER+b'\n'+b'\n'.join(lines)+ending,(low,high)
    rows=[b'1,'+str(i).encode()+b',-100000'for i in range(4096)]
    yield '4096-row-bound',HEADER+b'\n'+b'\n'.join(rows)+b'\n',None
    yield '4097-row-refusal',HEADER+b'\n'+b'\n'.join(rows+[b'1,4096,0'])+b'\n',None
    invalid=[b'',b'\n',b'bad\n',HEADER+b'\n\n',HEADER+b'\n1,0,0\r',HEADER+b'\n1,0,0\n1,0,1',HEADER+b'\n1,10,0\n1,9,1',HEADER+b'\n1,0,0\n1,1,1\nBAD']
    invalid += [HEADER+b'\n'+row for row in [b'0,0,0',b'33,0,0',b'01,0,0',b'1,-1,0',b'1,01,0',b'1,18446744073709551616,0',b'1,0,-100001',b'1,0,200001',b'1,0,-0',b'1,0,+1',b'1,0,00',b'1,0,1.5',b'1,0,NaN',b'1,0,0,',b'1,,0',b',0,0',b'1,0,',b'1,0,\x00',b'1,0,\xff',b'1,0, 0',b'1,0,0 ',b'1,0,"0"',b'1,0,'+b'1'*129]]
    invalid.append(HEADER+b'\n'+b'A'*1048576)
    for i,data in enumerate(invalid):yield 'invalid-'+str(i),data,None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('binary');parser.add_argument('--label',default='epoch');parser.add_argument('--python-reference',action='store_true');args=parser.parse_args();binary=Path(args.binary).resolve()
    launch=[os.sys.executable,str(binary)]if args.python_reference else[str(binary)]
    out=Path(tempfile.mkdtemp(prefix='sensor-'+args.label+'-',dir=ROOT/'artifacts'));results=[]
    for name,data,bounds in cases():
        path=out/(name+'.csv');path.write_bytes(data);before=hashlib.sha256(data).hexdigest()
        command=[*launch,str(path)]+([str(v)for v in bounds]if bounds else[])
        try:expected=oracle(data,*(bounds or(0,50000)))
        except ValueError:expected=None
        q=subprocess.run(command,capture_output=True,timeout=5)
        try:actual=json.loads(q.stdout)if q.stdout else None
        except ValueError:actual='invalid JSON'
        # Mathematical oracle is unchanged from epoch1. V2 explicitly changes
        # the wire schema: validate canonical strings, then compare exact ints.
        wire=True;normalized=actual
        if expected is not None:
            normalized=json.loads(json.dumps(actual))if isinstance(actual,dict)else actual
            wire=isinstance(actual,dict)and actual.get('schema')=='rf2.sensor-audit.v2'
            if wire:
                normalized['schema']='rf2.sensor-audit.v1'
                for sensor in normalized.get('sensors',[]):
                    for key in ('first_ms','last_ms'):
                        value=sensor.get(key)
                        if not isinstance(value,str)or not re.fullmatch(r'0|[1-9][0-9]*',value):
                            wire=False;break
                        if int(value)>U64:wire=False;break
                        sensor[key]=int(value)
        good=(q.returncode==0 and wire and normalized==expected)if expected is not None else(q.returncode==2 and q.stdout==b'')
        good=good and hashlib.sha256(path.read_bytes()).hexdigest()==before
        results.append(dict(name=name,passed=good,wireFormatPassed=wire,exit=q.returncode,inputSHA256=before,inputBytes=len(data),outputSHA256=hashlib.sha256(q.stdout).hexdigest(),stderr=q.stderr.decode(errors='replace'),expected=expected,actual=actual))
    for low,high in [('-0','1'),('0','-1'),('01','1'),('-100001','1'),('0','200001'),('0.0','1')]:
        path=out/'header-only.csv';q=subprocess.run([*launch,str(path),low,high],capture_output=True,timeout=5)
        results.append(dict(name='bad-thresholds-'+low+'-'+high,passed=q.returncode==2 and q.stdout==b'',exit=q.returncode))
    q=subprocess.run([*launch,str(out/'does-not-exist')],capture_output=True,timeout=5)
    results.append(dict(name='missing-file',passed=q.returncode==2 and q.stdout==b'',exit=q.returncode))
    link=out/'symlink.csv';link.symlink_to(out/'header-only.csv');q=subprocess.run([*launch,str(link)],capture_output=True,timeout=5)
    results.append(dict(name='symlink-refusal',passed=q.returncode==2 and q.stdout==b'',exit=q.returncode))
    q=subprocess.run([*launch,str(out)],capture_output=True,timeout=5)
    results.append(dict(name='directory-refusal',passed=q.returncode==2 and q.stdout==b'',exit=q.returncode))
    source=Path(__file__).read_text();tree=ast.parse(source);mathematics=next(node for node in tree.body if isinstance(node,ast.FunctionDef)and node.name=='oracle');math_source=ast.get_source_segment(source,mathematics)
    report=dict(schema='rf2.sensor-audit.tests.v2',label=args.label,runtime='Python reference'if args.python_reference else'native RF2',launch=launch,binarySHA256=hashlib.sha256(binary.read_bytes()).hexdigest(),oracleSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),mathematicalOracleSHA256=hashlib.sha256(math_source.encode()).hexdigest(),checks=len(results),passed=sum(x['passed']for x in results),allPassed=all(x['passed']for x in results),results=results,limits='Generated recorded-data cases on one native Mac. Epoch2 wire schema intentionally versions timestamps as canonical strings; mathematical oracle unchanged. No physical sensor, model-token or runtime-speed claim.')
    (out/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(directory=str(out),checks=len(results),passed=report['passed'],allPassed=report['allPassed'])))
    if not report['allPassed']:raise SystemExit(1)

if __name__=='__main__':main()
