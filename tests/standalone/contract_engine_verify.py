"""Independent native Evidence Contract engine tests.

Finite byte-plan oracle. Pure test fixtures, not safety, novelty or speed proof.
Uses a complete binary state/report channel; does not infer full values from an
8-bit process status. Native mutant source is isolated from the original.
"""
from pathlib import Path
import os,subprocess,time,json,hashlib,random,struct,re
R=Path(__file__).resolve().parents[2]
C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c')).resolve()
ENGINE=R/'examples/evidence-contract/lib/engine.rf2'
D=R/'artifacts/top-ten-five-hypotheses/engine-adversarial'/str(time.time_ns());D.mkdir(parents=True)
if not ENGINE.exists():raise SystemExit('Native engine source is not ready; no tests executed.')
raw=ENGINE.read_bytes();(D/'engine-original.rf2').write_bytes(raw)
hashof=lambda b:hashlib.sha256(b).hexdigest()
source='\n'.join(line for line in raw.decode().splitlines()if not line.startswith(('profile ','module ')))+'\n'
PROBE='''
fn main(argc,argv)
 if argc!=2
  return 2
 end
 let fd=open(load64(argv+8),0,0)
 if fd>>63
  return 2
 end
 let input=buffer("probe_input",672)
 let received=0
 let got=0
 while received<672
  set got=read(fd,input+received,672-received)
  if any(got==0,got>>63)
   do close(fd)
   return 2
  end
  set received=received+got
 end
 do close(fd)
 let data=Data()
 let codes=Ops()
 let args=Ops()
 let plan=Plan(load64(input+128),load64(input+136),load64(input+144),load64(input+152))
 let report=Run(0,0,0,0,0,0)
 let i=0
 while i<128
  set data[i]=load8(input+i)
  set i=i+1
 end
 set i=0
 while i<32
  set codes[i]=load64(input+160+i*8)
  set args[i]=load64(input+416+i*8)
  set i=i+1
 end
 let code=execute(data,plan,codes,args,report)
 let output=buffer("probe_output",184)
 set i=0
 while i<128
  do store8(output+i,data[i])
  set i=i+1
 end
 do store64(output+128,code)
 do store64(output+136,report.code)
 do store64(output+144,report.step)
 do store64(output+152,report.index)
 do store64(output+160,report.expected)
 do store64(output+168,report.actual)
 do store64(output+176,report.work)
 return write(1,output,184)!=184
end
'''
def compile_probe(body,path,opt):
 src=path.with_suffix('.rf2');src.write_text('profile RF2_SYSTEM_A64_V1\n'+body+PROBE)
 p=subprocess.run([C,src,path]+(['--opt']if opt else[]),capture_output=True,timeout=60)
 assert p.returncode==0,(str(src),p.stderr.decode())
 subprocess.run(['/usr/bin/codesign','-s','-',path],check=True,capture_output=True)
 return {'source':str(src.relative_to(R)),'sourceSHA256':hashof(src.read_bytes()),'binarySHA256':hashof(path.read_bytes())}
def fixture(data,n,steps,allow,budget,ops):
 assert len(data)==128 and len(ops)<=32
 codes=[p[0]for p in ops]+[0]*(32-len(ops));args=[p[1]for p in ops]+[0]*(32-len(ops))
 return bytes(data)+struct.pack('<4Q',n,steps,allow,budget)+struct.pack('<32Q',*codes)+struct.pack('<32Q',*args)
def oracle(data,n,steps,allow,budget,ops,mutant=False):
 state=list(data);work=0
 if n>128 or steps>32 or allow>7:return state,1,(1,0,0,0,0,0)
 for j in range(steps):
  code,arg=ops[j]
  if code not in [1,2,4]:return state,1,(1,j,0,0,code,0)
  if arg>255 or(code==4 and arg!=0):return state,1,(1,j,0,0,arg,0)
  if allow&code!=code:return state,2,(2,j,0,code,allow,0)
 if budget<2*n*steps:return state,3,(3,0,0,2*n*steps,budget,0)
 stage=list(state[:n])
 for j,(code,arg)in enumerate(ops[:steps]):
  if code==4:stage.reverse();work+=n
  else:
   for i in range(n):
    work+=1
    if code==1:
     total=stage[i]+arg
     if total>255:return state,4,(4,j,i,255,total,work)
     stage[i]=total
    else:stage[i]^=arg
 work=2*n*steps
 if mutant and n:
  return state,5,(5,steps,0,stage[0],stage[0]^1,work)
 state[:n]=stage
 return state,0,(0,0,0,0,0,work)
randomizer=random.Random(180021)
CASES=[]
def add(name,data,ops,n=None,allow=7,budget=None,steps=None):
 d=list(data)+[randomizer.randrange(256)for _ in range(128-len(data))]
 n=len(data)if n is None else n;steps=len(ops)if steps is None else steps
 budget=2*n*steps if budget is None else budget
 CASES.append((name,d,n,steps,allow,budget,ops))
add('empty',[],[]);add('empty-reverse',[],[(4,0)]);add('no-steps',[0,255,65],[])
add('reversal',[1,2,3,4],[(4,0)]);add('reverse-twice',[1,255,0],[(4,0),(4,0)])
add('late-overflow',[1,2,250],[(2,1),(1,5),(1,1)])
add('all-bytes-prefix',list(range(128)),[(2,255),(4,0),(2,127)])
add('max-steps',[0]*128,[(2,17)]*32)
add('byte-max-add',[0],[(1,255)])
add('byte-max-overflow',[255],[(1,1)])
add('late-denial-before-overflow',[255],[(1,1),(4,0)],allow=1,budget=0)
add('late-invalid-before-overflow',[255],[(1,1),(8,0)],budget=0)
add('late-arg-before-budget',[1],[(2,1),(1,256)],budget=0)
add('empty-still-authorized',[],[(1,0)],allow=0)
add('empty-still-validates',[],[(0,0)])
add('budget-zero',[1,2],[(2,1)],budget=0);add('budget-minus-one',[1,2],[(2,1)],budget=3)
add('missing-add',[1],[(1,0)],allow=6);add('missing-xor',[1],[(2,0)],allow=5)
add('missing-reverse',[1],[(4,0)],allow=3);add('empty-no-authority',[],[],allow=0)
add('n-overflow',[1],[],n=129);add('n-max',[1],[],n=2**64-1,budget=0)
add('steps-overflow',[1],[],steps=33);add('steps-max',[1],[],steps=2**64-1,budget=0)
add('mask-unknown',[1],[],allow=8);add('mask-max',[1],[],allow=2**64-1)
for code,arg in [(0,0),(3,0),(8,0),(2**64-1,0),(1,256),(2,2**64-1),(4,1)]:add(f'invalid-{code}-{arg}',[1,2],[(code,arg)])
for i in range(240):
 n=randomizer.randrange(129);ops=[(randomizer.choice([1,2,4]),0)for _ in range(randomizer.randrange(17))]
 ops=[(c,randomizer.randrange(16)if c==1 else randomizer.randrange(256)if c==2 else 0)for c,_ in ops]
 add('random-'+str(i),[randomizer.randrange(256)for _ in range(n)],ops)
(D/'cases.json').write_text(json.dumps(CASES,indent=2)+'\n')
rows=[];binaries=[]
for opt in [False,True]:
 exe=D/('probe-opt'if opt else'probe-default');binaries.append(compile_probe(source,exe,opt))
 for name,data,n,steps,allow,budget,ops in CASES:
  src=fixture(data,n,steps,allow,budget,ops);path=D/'input.bin';path.write_bytes(src)
  p=subprocess.run([exe,path],capture_output=True,timeout=10)
  assert p.returncode==0 and len(p.stdout)==184 and not p.stderr,(name,opt,p.returncode,p.stderr,len(p.stdout))
  actual=list(p.stdout[:128]);code,*run=struct.unpack('<7Q',p.stdout[128:]);expected,ec,er=oracle(data,n,steps,allow,budget,ops)
  assert actual==expected and code==ec and run[0]==ec,(name,opt,code,ec,actual[:n],expected[:n],run)
  assert tuple(run)==er,(name,opt,run,er)
  assert path.read_bytes()==src
  rows.append({'name':name,'optimized':opt,'passed':True,'expectedCode':ec,'fullStateSHA256':hashof(p.stdout[:128]),'inputSHA256':hashof(src),'returnedCode':code,'run':run,'fullStateHex':p.stdout[:128].hex()})
 # Source-level candidate mutation must be detected before any commit.
 marker=re.search(r'(?m)^(\s*)# Candidate output store[^\n]*\n(\s*)set (\w+)\[(\w+)\]\s*=\s*(\w+)',source)
 assert marker,'Engine must retain the agreed candidate output store marker for isolated mutation tests'
 whole=marker.group(0);indent=marker.group(2);index=marker.group(4);value=marker.group(5)
 replacement=whole[:whole.rfind('\n')]+f'\n{indent}if {index}==0\n{indent} set {value}={value}^1\n{indent}end\n'+whole[whole.rfind('\n')+1:]
 mutant=source[:marker.start()]+replacement+source[marker.end():];mutexe=D/('mutant-opt'if opt else'mutant-default');binaries.append(compile_probe(mutant,mutexe,opt))
 for name,data,ops in [('mutant-empty',[],[]),('mutant-one',[17],[]),('mutant-full',[1,2,3],[(1,2),(4,0),(2,3)])]:
  d=list(data)+[239]*(128-len(data));path=D/'input.bin';path.write_bytes(fixture(d,len(data),len(ops),7,2*len(data)*len(ops),ops));p=subprocess.run([mutexe,path],capture_output=True,timeout=10);assert p.returncode==0 and len(p.stdout)==184
  actual=list(p.stdout[:128]);code,*run=struct.unpack('<7Q',p.stdout[128:]);expected,ec,er=oracle(d,len(data),len(ops),7,2*len(data)*len(ops),ops,True)
  assert actual==expected and code==ec and tuple(run)==er,(name,opt,actual,expected,code,run,er)
  rows.append({'name':name,'optimized':opt,'passed':True,'expectedCode':ec,'mutant':True,'fullStateSHA256':hashof(p.stdout[:128]),'returnedCode':code,'run':run,'fullStateHex':p.stdout[:128].hex()})
assert ENGINE.read_bytes()==raw,'Original engine changed during test run'
report={'passed':True,'checks':len(rows),'engineSourceSHA256':hashof(raw),'compilerSHA256':hashof(C.read_bytes()),'testControllerSHA256':hashof(Path(__file__).read_bytes()),'binaries':binaries,'scope':'Independent finite full128-byte state and return/report checks across default/opt. Mutants are isolated source experiments, not a production option. Work is abstract semantic events, not CPU/energy. No formal proof, novelty or broad compiler qualification.','results':rows}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='results'},indent=2));print(D/'report.json')
