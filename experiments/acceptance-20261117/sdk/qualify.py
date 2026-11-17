#!/usr/bin/env python3
"""Local native JSON span writer qualification; no network/inference/production writes."""
from pathlib import Path
import argparse, hashlib, html, json, os, platform, random, statistics, subprocess, sys, time, tempfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
COMPILER_HASH = '4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
SDK_HASHES = {'io.flow':'c4b7d01a681b619a20adaccff698a353185ba4bfbe80272b5c60cf72f871d264', 'text.flow':'5d0ef4fd5cd34d40c3be21b5b334e607227fe80fd5c036bf2abefc144e209b5b'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def raw_oracle(data,cap,initial=0,error=0):
    out = bytearray(b'~'*initial)
    def add(value):
        nonlocal error
        if error: return
        if len(out)<=cap and len(value)<=cap-len(out):out.extend(value)
        else:error=28
    add(b'"')
    for c in data:
        if c in (34,92):add(bytes([92,c]))
        elif c in (10,13,9):add({10:b'\\n',13:b'\\r',9:b'\\t'}[c])
        elif c<32:
            add(b'\\u00'); add(b'0123456789abcdef'[c>>4:c//16+1]); add(b'0123456789abcdef'[c&15:(c&15)+1])
        else:add(bytes([c]))
    add(b'"')
    return (2 if error else 0, bytes(out), f'{len(out)}:{error}\n'.encode())
def report_oracle(data):
    text=data.decode('utf-8')
    escaped=text.replace('&','&amp;').replace("'",'&#39;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
    return (json.dumps(dict(schema='rf2-document.v1',bytes=len(data),text=text,html=escaped),ensure_ascii=False,separators=(',',':'))+'\n').encode()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('compiler',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--correctness-only',action='store_true');args=parser.parse_args()
    if sha(args.compiler)!=COMPILER_HASH:raise ValueError('Unexpected compiler; no fallback')
    if sys.platform!='darwin' or platform.machine()!='arm64':raise ValueError('Qualified only on Darwin ARM64')
    for name,digest in SDK_HASHES.items():
        if sha(ROOT/'sdk/v1'/name)!=digest:raise ValueError('SDK baseline changed: '+name)
    args.output.mkdir(parents=True,exist_ok=False); d=args.output.resolve(); (d/'inputs').mkdir()
    result=dict(schema='rf2.sdk-json-spans.v1',host=platform.platform(),compiler=str(args.compiler.resolve()),compilerSHA256=sha(args.compiler),sources={str(p.relative_to(ROOT)):sha(p) for p in [HERE/'json_spans.flow',HERE/'task.flow.in',Path(__file__),ROOT/'sdk/v1/io.flow',ROOT/'sdk/v1/text.flow']},builds=[],checks=[],benchmarks=[],failures=[],limits=['Local native serialization throughput only; no billed token or AI authoring reduction established.','HTML conversion is performed once before repeated JSON document serialization.','Ordinary write buffering/transport is unchanged; production SDK untouched.'])
    def save(): (d/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    events=(d/'CHECKS.jsonl').open('w',buffering=1)
    def check(name,condition,detail=None):
        row=dict(name=name,passed=bool(condition),detail=detail)
        result['checks'].append(row);events.write(json.dumps(row)+'\n')
        if not condition:
            save();raise AssertionError(name)
    programs={}
    binary_root=Path(tempfile.mkdtemp(prefix='sdk-native-',dir=os.environ['TMPDIR']))
    for optimization in ['plain','opt']:
      for variant in ['baseline','candidate']:
        build=d/(optimization+'-'+variant);build.mkdir();entry=build/'task.flow';exe=binary_root/(optimization+'-'+variant)
        entry.write_text((HERE/'task.flow.in').read_text().replace('__CANDIDATE_IMPORT__','use "json_spans.flow"' if variant=='candidate' else '').replace('__JSON__','writer_json_spans' if variant=='candidate' else 'writer_json'))
        if variant=='candidate':(build/'json_spans.flow').write_bytes((HERE/'json_spans.flow').read_bytes())
        command=[str(args.compiler.resolve()),str(entry),str(exe),'--sdk-root',str(ROOT/'sdk/v1')]+(['--opt'] if optimization=='opt' else [])
        began=time.perf_counter(); proc=subprocess.run(command,capture_output=True,timeout=30); elapsed=time.perf_counter()-began
        (build/'compile.stdout').write_bytes(proc.stdout);(build/'compile.stderr').write_bytes(proc.stderr)
        result['builds'].append(dict(command=command,exit=proc.returncode,seconds=elapsed));save()
        check(optimization+' '+variant+' compiles',proc.returncode==0,proc.stderr.decode(errors='replace'))
        subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],check=True,capture_output=True)
        result['builds'][-1]['programSHA256']=sha(exe);programs[optimization,variant]=exe
    sequence=0
    def fixture(data):
        nonlocal sequence
        sequence+=1;p=d/'inputs'/str(sequence);p.write_bytes(data);return p
    def run(exe,p,*,mode=0,repeats=1,cap=16777216,initial=0,error=0,raw=1,**kw):
        return subprocess.run([str(exe),str(mode),str(p),str(repeats),str(cap),str(initial),str(error),str(raw)],capture_output=True,timeout=60,**kw)
    rng=random.Random(419284)
    cases=[b'',bytes(range(256)),b'abc"\\\n\r\t\0xyz',b'normal text'*67,'中文 தமிழ் gold 🪙'.encode(),b'\0'*33]
    cases += [bytes(rng.randrange(256) for _ in range(n)) for n in [1,7,8,9,15,16,17,63,64,65,255,256,257,4096]]
    for idx,data in enumerate(cases):
        p=fixture(data); caps={0,1,2,3,7,8,9,len(data),len(data)+2,len(raw_oracle(data,16777216)[1])}
        if idx<4:caps.update(range(min(80,len(data)*6+4)))
        for cap in sorted(caps):
          for initial,error in [(0,0),(3,0),(0,7),(3,7),(min(cap+1,16),0)]:
            expected=raw_oracle(data,cap,initial,error)
            for (optimization,variant),exe in programs.items():
                q=run(exe,p,cap=cap,initial=initial,error=error)
                check(f'raw {idx} cap{cap} start{initial} error{error} {optimization}/{variant}',(q.returncode,q.stdout,q.stderr)==expected, None if (q.returncode,q.stdout,q.stderr)==expected else {'actual':[q.returncode,q.stdout.hex(),q.stderr.hex()],'expected':[expected[0],expected[1].hex(),expected[2].hex()]})
    for data in [b'',b'One <article> & "quote"\nsecond\tline','中文 தமிழ் 🪙'.encode(),b'plain'*10000]:
        p=fixture(data);expected=report_oracle(data)
        for (optimization,variant),exe in programs.items():
            q=run(exe,p,mode=1,raw=0)
            check('report oracle '+str(p.name)+' '+optimization+'/'+variant,q.returncode==0 and q.stdout==expected)
            check('report parse '+str(p.name)+' '+optimization+'/'+variant,json.loads(q.stdout)['bytes']==len(data))
    p=fixture(b'bad\x00text')
    for key,exe in programs.items():
        q=run(exe,p,mode=1,raw=0);check('invalid text refusal '+str(key),q.returncode==2 and not q.stdout)
        q=run(exe,d/'absent');check('missing file refusal '+str(key),q.returncode==2 and not q.stdout)
        q=run(exe,p,repeats=0);check('zero repeats refusal '+str(key),q.returncode==2 and not q.stdout)
        q=run(exe,p,cap=16777217);check('over-limit capacity refusal '+str(key),q.returncode==2 and not q.stdout)
    # Pipe/descriptor failures are real subprocess conditions, not source hooks.
    p=fixture(b'safe text')
    for key,exe in programs.items():
        command=[str(exe),'1',str(p),'1','16777216','0','0','0']
        q=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=lambda:os.close(1),timeout=10)
        check('closed stdout '+str(key),q.returncode==2)
        readfd,writefd=os.pipe();os.close(readfd)
        q=subprocess.run(command,stdout=writefd,stderr=subprocess.PIPE,timeout=10);os.close(writefd)
        check('broken stdout pipe '+str(key),q.returncode==2)
    if args.correctness_only:
        result['allPassed']=all(c['passed'] for c in result['checks']);result['complete']=True;result['correctnessOnly']=True;save();print(json.dumps({'receipt':str(d/'RESULTS.json'),'checks':len(result['checks'])}));return
    # Warmed, randomized AB/BA pairs; mixed sizes and escape densities; all outputs verified.
    for size in [0,32,1024,16384,262144]:
      for density in ['plain','mixed','escaped']:
        seed={'plain':b'alpha beta gamma 0123456789 ', 'mixed':b'alpha "beta" <gamma> & line\nsecond\tline ', 'escaped':b'"\\\n\t\r'}[density]
        data=(seed*((size+len(seed)-1)//len(seed)))[:size];p=fixture(data);expected=report_oracle(data)
        repeats=min(2000,max(1,1048576//max(size,256)))
        # 11 paired trials, each fresh process; retain raw times and matched output hashes.
        for optimization in ['plain','opt']:
          times={'baseline':[],'candidate':[]};order=[]
          for variant in times:
            q=run(programs[optimization,variant],p,mode=1,raw=0,repeats=repeats)
            check('benchmark warm output '+optimization+'/'+variant+f' {size}/{density}',q.returncode==0 and q.stdout==expected)
          for trial in range(11):
            variants=['baseline','candidate'];rng.shuffle(variants);order.append(variants)
            for variant in variants:
              start=time.perf_counter_ns();q=run(programs[optimization,variant],p,mode=1,raw=0,repeats=repeats);elapsed=(time.perf_counter_ns()-start)/1e9
              check('benchmark output '+optimization+'/'+variant+f' {size}/{density}/{trial}',q.returncode==0 and q.stdout==expected)
              times[variant].append(elapsed)
          base=statistics.median(times['baseline']);candidate=statistics.median(times['candidate'])
          row=dict(size=size,density=density,optimization=optimization,repeats=repeats,pairs=11,order=order,seconds=times,baselineMedian=base,candidateMedian=candidate,speedup=base/candidate,outputSHA256=hashlib.sha256(expected).hexdigest())
          result['benchmarks'].append(row);save()
    result['allPassed']=all(c['passed'] for c in result['checks']);result['complete']=True;save()
    print(json.dumps({'receipt':str(d/'RESULTS.json'),'checks':len(result['checks']),'benchmarks':len(result['benchmarks'])}))
if __name__=='__main__':main()
