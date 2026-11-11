"""Reproduce native compiler bootstrap, code equivalence, execution and refusals.
Development Python is an oracle/controller. PATH-free native stages never run it.
"""
from pathlib import Path
import sys,subprocess,tempfile,hashlib,json,random,struct,os
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'bootstrap'))
from seed import Compiler
ROOT=R/'output/compiler-verification';ROOT.mkdir(parents=True,exist_ok=True)
work=Path(tempfile.mkdtemp(prefix='run-',dir=ROOT))
source=R/'native/compiler/compiler.rf2';seed=R/'output/compiler-stage0/rf2c'
report={'schema':'rf2.compiler.verification.v1','passed':False,'target':'macos-arm64','selfHostingScope':'RF2_SYSTEM_A64_V1 compiler source, bounded documented lexical subset','speedClaim':None,'pythonFreeNativeStages':True,'cases':[],'negativeCases':0,'hashCases':0}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,ok=True,timeout=30):
 r=subprocess.run([str(x)for x in cmd],capture_output=True,timeout=timeout,env={'PATH':'/nonexistent'})
 if ok:assert r.returncode==0,(cmd,r.returncode,r.stderr[:400])
 return r
def sign(p):run(['/usr/bin/codesign','-s','-','--force',p])
def native_build(compiler,path,out):
 r=run([compiler,path,out]);assert b'RF2 native image emitted' in r.stdout
 return out.read_bytes()
def reference(path):return Compiler().compile(path.read_text())[0]
# First native stage from the historical seed; subsequent builds use native RF2 only.
raw=reference(source);(work/'seed.raw').write_bytes(raw)
a=work/'stage1';data=native_build(seed,source,a);assert data==raw
report['stage1UnsignedSHA256']=hashlib.sha256(data).hexdigest();sign(a)
b=work/'stage2';data=native_build(a,source,b);assert data==raw
report['stage2UnsignedSHA256']=hashlib.sha256(data).hexdigest();sign(b)
c=work/'stage3';data=native_build(b,source,c);assert data==raw
report['stage3UnsignedSHA256']=hashlib.sha256(data).hexdigest();sign(c)
report['fixedPointUnsignedImages']=True
# Run the runtime produced by the native-generated compiler, not the retained binary.
runtime_source=work/'runtime.rf2';runtime_source.write_text(''.join((R/name).read_text()for name in ['native/rf2.rf2','native/core.rf2','native/attendance.rf2','native/attendance-kernel.rf2','native/fingerprint.rf2']))
rt=work/'rf2';assert native_build(c,runtime_source,rt)==reference(runtime_source);sign(rt)
assert json.loads(run([rt,'status']).stdout)['version']=='0.6.0'
assert json.loads(run([rt,'run',R/'examples/compact/sum.rf2','[2,3,4]']).stdout)['value']==9
report['runtimeUnsignedMatchesReference']=True;report['generatedRuntime']=str(rt.relative_to(R))
# Independent expected process exits cover unsigned arithmetic, loops, calls, memory and branches.
programs=[
 ('add','return 7 + 11',18),('sub','return 7 - 11',252),('mul','return 17 * 19',67),
 ('and','return 255 & 17',17),('or','return 128 | 3',131),('xor','return 255 ^ 240',15),
 ('shift','return ((1 << 63) >> 60)',8),('division','return 100 // 7',14),('zero-div','return 17 // 0',0),
 ('not','return (~0) & 255',255),('neg','return -7',249),
 ('precedence','return 3 + 4 * 5',23),('parentheses','return (3 + 4) * 5',35),
 ('unsigned','return (-1) > 1',1),('eq','return 9 == 9',1),('ne','return 9 != 9',0),
 ('lt','return 8 < 9',1),('le','return 9 <= 9',1),('ge','return 9 >= 9',1),
 ('branch','let x = 0\n if 3 > 2\n  set x = 17\n else\n  set x = 18\n end\n return x',17),
 ('loop','let x = 0\n while x < 25\n  set x = x + 1\n end\n return x',25),
 ('memory','let p = buffer("probe", 8)\n do store64(p, 81985529216486895)\n return load8(p + 2)',171),
 ('quoted-operators','let p = "-"\n let q = "("\n return load8(p) + load8(q)',85),
]
for name,body,expected in programs:
 p=work/(name+'.rf2');p.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc, argv)\n '+body+'\nend\n')
 out=work/name;assert native_build(c,p,out)==reference(p),name;sign(out);r=run([out],ok=False);assert r.returncode==expected,(name,r.returncode,expected);report['cases'].append({'name':name,'unsignedByteMatch':True,'expectedExit':expected,'actualExit':r.returncode})
# Forward calls and all eight parameter registers.
p=work/'calls.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc, argv)\n return helper(1,2,3,4,5,6,7,8)\nend\nfn helper(a,b,c,d,e,f,g,h)\n return a+b+c+d+e+f+g+h\nend\n')
out=work/'calls';assert native_build(c,p,out)==reference(p);sign(out);assert run([out],ok=False).returncode==36;report['cases'].append({'name':'forward-eight-argument-call','unsignedByteMatch':True,'expectedExit':36,'actualExit':36})
# Native SHA-256: exercise complete digests at padding boundaries and with arbitrary bytes.
# A derived diagnostic main writes the full digest, not merely the 16 UUID bytes.
sha_source=source.read_text().split('fn main(argc, argv)')[0]+'''fn main(argc, argv)
 let p = read_source(load64(argv + 8))
 let h = sha256(p, load64(state() + 8))
 do write(1, h, 32)
 return 0
end
'''
p=work/'hash-probe.rf2';p.write_text(sha_source);out=work/'hash-probe';assert native_build(c,p,out)==reference(p);sign(out)
randomizer=random.Random(20261112)
for size in [0,1,3,55,56,63,64,65,119,120,127,128,1024,524288]:
 data=bytes(randomizer.randrange(256)for _ in range(size));p=work/('hash-input-'+str(size));p.write_bytes(data);assert run([out,p]).stdout==hashlib.sha256(data).digest();report['hashCases']+=1
# Malformed source and source/resource bounds must fail before opening the requested output.
invalid=[
 '', 'profile OTHER\nfn main(argc,argv)\nreturn 0\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return missing\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return 1 < 2 < 3\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return "a" "+" "b"\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n do unknown()\nreturn 0\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n do load8(1,2)\nreturn 0\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n let x = 1\nlet x = 2\nreturn x\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n let x = buffer("a",8)\nlet y = buffer("a",16)\nreturn 0\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n let x = buffer("a",134217728)\nreturn 0\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n if 1\nreturn 1\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return '+('('*70)+'1'+(')'*70)+'\nend\n',
 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return 0\nend\n'+('#'*524289),
]
for i,text in enumerate(invalid):
 p=work/f'invalid-{i}.rf2';p.write_text(text);out=work/f'invalid-{i}';r=run([c,p,out],ok=False);assert r.returncode==1,(i,r.returncode,r.stderr);assert not out.exists();report['negativeCases']+=1
# Refuse existing outputs and symlinks without changing their target bytes.
p=work/'existing';p.write_bytes(b'preserve');r=run([c,R/'native/hello.rf2',p],ok=False);assert r.returncode==1;assert p.read_bytes()==b'preserve';report['negativeCases']+=1
link=work/'link';link.symlink_to(p);r=run([c,R/'native/hello.rf2',link],ok=False);assert r.returncode==1;assert p.read_bytes()==b'preserve';report['negativeCases']+=1
# Runtime result/refusal corpus and official SDK checks against the native-compiled runtime.
env=dict(os.environ,RF2_TEST_BINARY=str(rt),RF2_TEST_REPORT=str(work/'runtime-verification.json'),RF2_TEST_VERSION='0.6.0',RF2_TEST_TOOLS='5');r=subprocess.run(['python3',str(R/'tests/standalone/verify.py')],cwd=R,env=env,capture_output=True,timeout=40);assert r.returncode==0,r.stderr;report['runtimeCorpusPassed']=True
r=subprocess.run(['/opt/homebrew/opt/node@22/bin/node',str(R/'tests/standalone/sdk.mjs')],cwd=R,env=env,capture_output=True,timeout=20);assert r.returncode==0,r.stderr;report['officialSdkPassed']=True
report.update(passed=True,sourceSHA256=digest(source),nativeCompilerSHA256=digest(c),historicalSeedSHA256=digest(R/'bootstrap/seed.py'),generatedRuntimeSHA256=digest(rt),seedEncoderRuntimeByteMatch=True)
(R/'docs/NATIVE-COMPILER-0.6-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
# Candidate copies are separate from the published 0.4 runtime.
import shutil
(R/'output/native-compiler').mkdir(exist_ok=True);shutil.copy2(c,R/'output/native-compiler/rf2c');(R/'output/native-0.6').mkdir(exist_ok=True);shutil.copy2(rt,R/'output/native-0.6/rf2');print('Candidate native compiler and native-built runtime retained')
