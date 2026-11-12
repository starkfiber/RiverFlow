"""Independent finite native CLI/parser/receipt qualification. No speed claims.

A source-bundle receipt is an unkeyed reproducibility checksum, not binary
attestation or authentication. Source-identity mutation occurs in an isolated copy.
"""
from pathlib import Path
import hashlib,json,random,shutil,struct,subprocess,time
R=Path(__file__).resolve().parents[2]
D=R/'artifacts/top-ten-five-hypotheses/cli-adversarial'/str(time.time_ns())
D.mkdir(parents=True)
H=lambda b:hashlib.sha256(b).hexdigest()
rows=[]

def identity(root):
    d=root/'examples/evidence-contract'
    h=hashlib.sha256(b'RF2-CONTRACT-SOURCE-1\0')
    for p in sorted(d.rglob('*.rf2')):
        if p.name=='build_identity.rf2':continue
        name=p.relative_to(d).as_posix().encode();raw=p.read_bytes()
        h.update(struct.pack('<Q',len(name))+name+struct.pack('<Q',len(raw))+raw)
    return h.hexdigest()

def build(root,out,opt=False):
    p=subprocess.run(['python3',root/'tools/build-contract.py',out]+(['--opt']if opt else[]),capture_output=True,timeout=120)
    (out.with_suffix('.build.log')).write_bytes(p.stdout+p.stderr)
    assert p.returncode==0,(out,p.stderr.decode())
    record=json.loads(out.with_suffix('.build.json').read_text())
    assert record['source_identity']==identity(root)
    assert record['binary_sha256']==H(out.read_bytes())
    return record

def canonical(data,ops,allow=7,budget=None):
    if budget is None:budget=2*len(data)*len(ops)
    parts=['RF2E1','allow',str(allow),'budget',str(budget),'input',str(len(data))]+list(map(str,data))+['steps',str(len(ops))]
    for code,arg in ops:
        parts.append({1:'add',2:'xor',4:'reverse'}[code])
        if code!=4:parts.append(str(arg))
    return (' '.join(parts)+'\n').encode()

def oracle(data,ops,allow,budget):
    run=[0]*6
    if allow>7:return list(data),[1,0,0,0,0,0]
    for j,(code,arg) in enumerate(ops):
        if arg>255:return list(data),[1,j,0,0,arg,0]
        if allow&code!=code:return list(data),[2,j,0,code,allow,0]
    need=2*len(data)*len(ops)
    if budget<need:return list(data),[3,0,0,need,budget,0]
    stage=list(data);work=0
    for j,(code,arg) in enumerate(ops):
        if code==4:stage.reverse();work+=len(data)
        else:
            for i,v in enumerate(stage):
                work+=1
                if code==1 and v+arg>255:return list(data),[4,j,i,255,v+arg,work]
                stage[i]=v+arg if code==1 else v^arg
    run[-1]=need
    return stage,run

def invoke(exe,raw,expected=None):
    fixture=D/'plan.rf2e';fixture.write_bytes(raw)
    p=subprocess.run([exe,fixture]+([]if expected is None else[expected]),capture_output=True,timeout=10)
    assert fixture.read_bytes()==raw
    assert not p.stderr,(exe,p.stderr)
    try:obj=json.loads(p.stdout)
    except Exception as e:raise AssertionError((exe,p.returncode,p.stdout))from e
    return p.returncode,obj

def verify(exe,sid,name,data,ops,allow=7,budget=None,raw=None):
    if budget is None:budget=2*len(data)*len(ops)
    raw=canonical(data,ops,allow,budget)if raw is None else raw
    output,run=oracle(data,ops,allow,budget)
    receipt=H(b'RF2-EVIDENCE-CONTRACT-1'+sid.encode()+hashlib.sha256(raw).digest()+hashlib.sha256(bytes(output)).digest()+struct.pack('<6Q',*run))
    expected={'profile':'RF2E1','source_identity':sid,'receipt':receipt,**dict(zip(['code','step','index','expected','actual','work'],run)),'input':list(data),'output':output}
    rc,obj=invoke(exe,raw)
    assert rc==(0 if run[0]==0 else 1)and obj==expected,(name,rc,obj,expected)
    # Fresh process, expected digest never trusted from the executable under test.
    rc2,obj2=invoke(exe,raw,receipt)
    assert rc2==rc and obj2==expected,(name,'receipt replay',rc2,obj2)
    rows.append({'name':name,'binary':exe.name,'passed':True,'receipt':receipt,'inputSHA256':H(raw),'run':run,'output':output})
    return raw,receipt

try:
    source_identity=identity(R)
    binaries=[]
    rng=random.Random(710291)
    cases=[('empty',[],[],7,0),('reverse',[0,127,255],[(4,0)],7,6),('late-overflow',[1,2,250],[(2,1),(1,5),(1,1)],7,18),('all-bytes',list(range(128)),[(2,255),(4,0)],7,512),('32steps',[0]*128,[(2,1)]*32,7,8192),('permission',[1],[(2,1),(4,0)],2,4),('budget',[1,2],[(2,1)],7,3),('max-budget',[1],[(1,0)],7,2**64-1),('max-mask',[],[],2**64-1,0),('max-arg',[1],[(1,2**64-1)],7,2),('empty-permission',[],[(1,0)],0,0)]
    for i in range(100):
        n=rng.randrange(129);ops=[(rng.choice([1,2,4]),0)for _ in range(rng.randrange(33))]
        ops=[(c,rng.randrange(6)if c==1 else rng.randrange(256)if c==2 else 0)for c,_ in ops]
        data=[rng.randrange(256)for _ in range(n)];allow=rng.choice([7,7,7,0,1,2,4]);budget=2*n*len(ops)
        if rng.randrange(5)==0:budget=max(0,budget-1)
        cases.append((f'random-{i}',data,ops,allow,budget))
    base=canonical([1,2],[(2,3)])
    malformed=[b'',b'RF2E1',base+b'junk',base.replace(b'RF2E1',b'RF2E10'),base.replace(b'allow',b'allowx'),base.replace(b'allow 7',b'allow 07'),base.replace(b'budget 4',b'budget +4'),base.replace(b'budget 4',b'budget -4'),base.replace(b'budget 4',b'budget 18446744073709551616'),base.replace(b'input 2 1 2',b'input 1 256'),base.replace(b'input 2 1 2',b'input 129'),base.replace(b'steps 1 xor 3',b'steps 33'),base.replace(b'xor 3',b'xor'),base.replace(b'xor 3',b'XOR 3'),base.replace(b'xor 3',b'reverse 0'),base.replace(b'xor 3',b'add 00'),base.replace(b'xor 3',b'xor 3.0'),base.replace(b'xor 3',b'xor 0x3'),base.replace(b'xor 3',b'xor \xff'),base+b'\x00',base.replace(b' ',b'\x0b'),base.replace(b' 7 ',b' \xd9\xa7 ')]
    (D/'fixtures.json').write_text(json.dumps({'plans':cases,'malformedHex':[v.hex()for v in malformed]},indent=2)+'\n')
    for opt in [False,True]:
        exe=D/('contract-opt'if opt else'contract-default');record=build(R,exe,opt);binaries.append(record)
        assert record['source_identity']==source_identity,'Source changed during tests'
        missing=subprocess.run([exe,D/'does-not-exist'],capture_output=True,timeout=10)
        assert missing.returncode==1 and json.loads(missing.stdout)=={'error':'open'}and not missing.stderr
        rows.append({'name':'missing-file','binary':exe.name,'passed':True})
        for argv in [[],['a','b','c']]:
            usage=subprocess.run([exe,*argv],capture_output=True,timeout=10)
            assert usage.returncode==1 and usage.stdout.startswith(b'Usage:')and not usage.stderr
            rows.append({'name':'usage-'+str(len(argv)),'binary':exe.name,'passed':True})
        for args in cases:verify(exe,source_identity,*args)
        whitespace=base.replace(b' ',b'\t\r\n')
        verify(exe,source_identity,'whitespace',[1,2],[(2,3)],raw=whitespace)
        padded=base+b' '*(8192-len(base));verify(exe,source_identity,'8192-exact',[1,2],[(2,3)],raw=padded)
        for i,raw in enumerate(malformed+[padded+b' ']):
            rc,obj=invoke(exe,raw)
            assert rc==1 and obj.get('error')==('size-or-close'if len(raw)>8192 else'parse')and'output'not in obj,(i,rc,obj)
            rows.append({'name':f'malformed-{i}','binary':exe.name,'passed':True,'inputSHA256':H(raw),'response':obj})
        raw,digest=verify(exe,source_identity,'receipt-control',[1,2],[(2,3)])
        for name,newraw,token,error in [('changed-input',raw+b' ',digest,'stale-receipt'),('wrong-digest',raw,'0'*64,'stale-receipt'),('uppercase',raw,digest.upper(),'stale-receipt'),('short',raw,digest[:-1],'receipt-format')]:
            rc,obj=invoke(exe,newraw,token)
            assert rc==1 and obj.get('error')==error and'output'not in obj,(name,rc,obj)
            rows.append({'name':name,'binary':exe.name,'passed':True,'response':obj})
    # Build a comment-only changed source bundle in a private miniature copy.
    shadow=D/'changed-source';(shadow/'tools').mkdir(parents=True);(shadow/'output/native-compiler').mkdir(parents=True)
    shutil.copytree(R/'examples/evidence-contract',shadow/'examples/evidence-contract')
    shutil.copy2(R/'tools/build-contract.py',shadow/'tools/build-contract.py')
    shutil.copy2(R/'output/native-compiler/rf2c',shadow/'output/native-compiler/rf2c')
    with (shadow/'examples/evidence-contract/main.rf2').open('a')as f:f.write('\n# Independent source identity challenge.\n')
    changed=D/'contract-changed-source';changedrecord=build(shadow,changed);binaries.append(changedrecord)
    assert changedrecord['source_identity']!=source_identity
    rc,obj=invoke(changed,raw,digest)
    assert rc==1 and obj=={'error':'stale-receipt','published':False},(rc,obj)
    rows.append({'name':'changed-source-identity','passed':True,'response':obj})
    verify(changed,changedrecord['source_identity'],'changed-source-fresh-receipt',[1,2],[(2,3)])
    assert identity(R)==source_identity,'Tracked source changed during tests'
    report={'passed':True,'checks':len(rows),'source_identity':source_identity,'testControllerSHA256':H(Path(__file__).read_bytes()),'binaries':binaries,'results':rows,'scope':'Finite macOS ARM64 native default/opt tests using an independent Python oracle and hashlib SHA256. Receipt binds raw plan bytes, output, Run and source-bundle ID; it does not authenticate the running binary or caller. No formal proof, novelty or performance claim.'}
    (D/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k not in ['results','binaries']},indent=2));print(D/'report.json')
except BaseException as e:
    (D/'failure.json').write_text(json.dumps({'passed':False,'completedChecks':len(rows),'error':repr(e),'results':rows},indent=2)+'\n')
    print('Failure retained at',D/'failure.json');raise
