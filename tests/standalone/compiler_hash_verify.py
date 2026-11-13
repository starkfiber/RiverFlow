"""Compiler SHA feature/fallback controls and independent digest/seed encoders."""
from pathlib import Path
import hashlib,json,os,random,re,subprocess,sys,time
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
D=R/'artifacts/hash-029'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
source=(R/'native/compiler/compiler.rf2').read_text()
names=['rotate','sha256_software','sha256_initialize','sha256_arm_available','sha256_accelerated','sha256']
parts=[]
for name in names:
 m=re.search(r'^fn '+name+r'\(',source,re.M);assert m,name
 n=re.search(r'^fn ',source[m.end():],re.M);parts.append(source[m.start():m.end()+n.start()]if n else source[m.start():])
harness='profile RF2_SYSTEM_A64_V1\n'+''.join(parts)+'''fn main(argc,argv)
 if argc != 3
  return 1
 end
 let fd = open(load64(argv+8),0,0)
 if fd >= 9223372036854775808
  return 2
 end
 let input = buffer("hash_input",1048577)
 let n = 0
 let got = 1
 while got != 0
  set got = read(fd,input+n,1048577-n)
  if got >= 9223372036854775808
   return 3
  end
  set n = n+got
  if n > 1048576
   return 4
  end
 end
 do close(fd)
 let mode = load8(load64(argv+16))
 if (mode == 115) | (mode == 118)
  do store64(buffer("sha_feature",16),2)
 end
 let offset = 0
 if (mode == 117) | (mode == 118)
  if n == 0
   return 5
  end
  set offset = 1
 end
 let digest = sha256(input+offset,n-offset)
 do write(1,digest,32)
 do write(1,buffer("sha_feature",16),8)
 return 0
end
'''
p=D/'harness.rf2';p.write_text(harness);sys.path.insert(0,str(R/'bootstrap'));from seed import Compiler
# Default output must match a separate Python instruction encoder exactly.
seed=Compiler().compile(harness)[0];(D/'seed-unsigned').write_bytes(seed)
cases=[];bins=[]
for opt in [False,True]:
 binary=D/f'hash-{opt}';q=subprocess.run([str(C),str(p),str(binary),*(['--opt']if opt else[])],capture_output=True,timeout=30);assert q.returncode==0,q.stderr
 if not opt:assert binary.read_bytes()==seed,'seed/default encoder mismatch'
 subprocess.run(['/usr/bin/codesign','-s','-',str(binary)],capture_output=True,check=True);bins.append(binary)
lengths=sorted(set([*range(0,137),255,256,257,511,512,513,4095,4096,4097,65535,65536,65537,1048576]))
rng=random.Random(29014)
feature=set()
for n in lengths:
 data=bytes(rng.randrange(256) for _ in range(n));inp=D/'input';inp.write_bytes(data)
 for binary in bins:
  for mode in ['a','s','u','v']:
   if mode in ['u','v']and n==0:continue
   q=subprocess.run([str(binary),str(inp),mode],capture_output=True,timeout=15);assert q.returncode==0 and len(q.stdout)==40,(n,mode,q.returncode,q.stderr)
   expected=hashlib.sha256(data[1:]if mode in ['u','v']else data).digest();assert q.stdout[:32]==expected,(n,mode,binary)
   state=int.from_bytes(q.stdout[32:],'little');feature.add(state)
   if mode in ['s','v']:assert state==2,'software override was not used'
   else:assert state in [2,3]
   cases.append(dict(bytes=n,mode=mode,optimized=binary==bins[1],featureState=state,digest=expected.hex()))
report=dict(passed=True,schema='rf2.compiler.hash.verification.v1',cases=len(cases),rows=cases,featureStates=sorted(feature),seedDefaultByteMatch=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),sourceSHA256=hashlib.sha256(source.encode()).hexdigest(),seedSHA256=hashlib.sha256((R/'bootstrap/seed.py').read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits='One Darwin ARM64 host; automatic feature discovery and forced-software state tested. Forced state is an implementation control, not execution on hardware lacking SHA instructions. Buffers and helper state remain single-threaded. No timing, energy or general hardware claim.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'passed':True,'cases':len(cases),'featureStates':sorted(feature)}))
