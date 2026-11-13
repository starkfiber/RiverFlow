"""Independent SHA/compression oracles. Controllers are development tools only."""
from pathlib import Path
import subprocess,struct,random,hashlib,json,time,os
R=Path(__file__).resolve().parents[2];D=R/'artifacts/sha-next'/('verify-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-sha-next-self'));rng=random.Random(231113)
sha=(R/'examples/evidence-contract/lib/sha256.rf2').read_text().split('\n',1)[1]
def build(name,text,opt):
 p=D/(name+'.rf2');p.write_text('profile RF2_SYSTEM_A64_V1\n'+text);exe=D/name;q=subprocess.run([C,p,exe,*(['--opt']if opt else[])],capture_output=True);assert q.returncode==0,(name,q.stdout,q.stderr);subprocess.run(['/usr/bin/codesign','-s','-',exe],check=True,capture_output=True);return exe
harness='''fn main(argc,argv)
 let p=buffer("message",1048577)
 let fd=open(load64(argv+8),0,0)
 let n=read(fd,p,1048577)
 do close(fd)
 if n>1048576
  return 1
 end
 do write(1,sha256(p,n),32)
 return 0
end
'''
# Exercise selected hardware, explicitly forced software and an unavailable query.
checks=[];lens=list(range(140))+[255,256,511,512,513,1024,4096,32768,65536,1048576]
for mode in ['auto','software','query-failure']:
 source=sha
 if mode=='software':source=source.replace('if sha256_arm_available()','if 0')
 if mode=='query-failure':source=source.replace('hw.optional.arm.FEAT_SHA256','hw.optional.arm.RF2_NONEXISTENT')
 for opt in [False,True]:
  exe=build(mode+('-opt'if opt else'-plain'),source+harness,opt)
  for n in lens:
   data=rng.randbytes(n);(D/'message').write_bytes(data);q=subprocess.run([exe,D/'message'],capture_output=True,timeout=10);assert q.returncode==0 and q.stdout==hashlib.sha256(data).digest(),(mode,opt,n,q.stdout.hex());checks.append({'mode':mode,'opt':opt,'bytes':n})
# Check actual feature selection and zero-block no-op without dereferencing nulls.
probe=build('probe',sha+'''fn main(argc,argv)
 let v=buffer("probe",16)
 do store64(v,sha256_arm_available())
 do store64(v+8,sha256_blocks_armv8(0,0,0,0))
 do write(1,v,16)
 return 0
end
''',True);q=subprocess.run([probe],capture_output=True,check=True);assert q.stdout==struct.pack('<2Q',1,0),q.stdout.hex()
from sha_reference import compress
raw='''fn main(argc,argv)
 let p=buffer("raw",4096)
 let fd=open(load64(argv+8),0,0)
 let n=read(fd,p,4096)
 do close(fd)
 let offset=load64(p)
 let base=p+8+offset
 let keep=123456789
 do sha256_blocks_armv8(base,base+288,(n-8-offset-288-16)//64,base+32)
 if keep!=123456789
  return 3
 end
 do write(1,p,n)
 return 0
end
'''
rawcases=0
for opt in [False,True]:
 exe=build('raw'+('-opt'if opt else'-plain'),raw,opt)
 for offset in range(16):
  for blocks in range(6):
   state=[rng.getrandbits(32)for _ in range(8)];k=[rng.getrandbits(32)for _ in range(64)];data=rng.randbytes(blocks*64);head=struct.pack('<Q',offset)+b'P'*offset;original=head+struct.pack('<8I',*state)+struct.pack('<64I',*k)+data+b'T'*16;expected=head+struct.pack('<8I',*compress(state,data,k))+original[len(head)+32:];(D/'raw-input').write_bytes(original);q=subprocess.run([exe,D/'raw-input'],capture_output=True,timeout=5);assert q.returncode==0 and q.stdout==expected,(offset,blocks,opt,q.stderr);rawcases+=1
# Compare the native emitter's complete inline sequence with the platform assembler.
obj=D/'oracle.o';subprocess.run(['/usr/bin/clang','-target','arm64-apple-macos11','-march=armv8-a+crypto','-c',R/'tests/standalone/sha256_blocks_armv8.s','-o',obj],check=True,capture_output=True)
blob=obj.read_bytes();off=32;code=None
for _ in range(struct.unpack_from('<I',blob,16)[0]):
 cmd,size=struct.unpack_from('<II',blob,off)
 if cmd==0x19:
  for j in range(struct.unpack_from('<I',blob,off+64)[0]):
   p=off+72+j*80
   if blob[p:p+16].rstrip(b'\0')==b'__text':
    n=struct.unpack_from('<Q',blob,p+40)[0];start=struct.unpack_from('<I',blob,p+48)[0];code=blob[start:start+n]
 off+=size
assert code is not None and probe.read_bytes().count(code)==sha.count('sha256_blocks_armv8(')+1 # library calls plus the explicit no-op probe
# Wrong arity, reserved names, record-to-raw passage and view freeze must reject.
neg=['fn sha256_blocks_armv8(a,b,c,d)\n return 0\nend\nfn main(argc,argv)\nreturn 0\nend','record sha256_blocks_armv8(x:u64)\nfn main(argc,argv)\nreturn 0\nend','fn main(argc,argv)\nreturn sha256_blocks_armv8(1,2,3)\nend','fn main(argc,argv)\nreturn sha256_blocks_armv8(1,2,3,4,5)\nend','record Data(x:u64)\nfn main(argc,argv)\nlet a=Data(0)\nreturn sha256_blocks_armv8(a,0,0,0)\nend','array Data(u8,4)\nview Window(Data)\nfn main(argc,argv)\nlet a=Data()\nlet v=Window(a,0,1)\nreturn sha256_blocks_armv8(0,0,0,0)\nend']
for i,s in enumerate(neg):
 p=D/f'negative{i}.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\n'+s+'\n');exe=D/f'negative{i}';q=subprocess.run([C,p,exe],capture_output=True);assert q.returncode==1 and not exe.exists(),(i,q.stdout,q.stderr)
report={'passed':True,'shaChecks':len(checks),'shaCases':checks,'arbitraryCompressionCases':rawcases,'negativeCases':len(neg),'assemblyOracleByteMatch':True,'featureProbe':{'available':True,'zeroBlockNullNoOp':True},'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'shaSourceSHA256':hashlib.sha256((R/'examples/evidence-contract/lib/sha256.rf2').read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limits':'Finite local checks, trusted raw pointers. ARM FEAT_SHA256 required for direct intrinsic; library queries Darwin and falls back on absent/failed query. Not crypto certification, reentrancy or memory safety.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'passed':True,'shaChecks':len(checks),'compressionCases':rawcases,'negativeCases':len(neg)}))
