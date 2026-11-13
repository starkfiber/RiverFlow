"""Native32-bit rotation and SHA differential checks; development oracle only."""
from pathlib import Path
import subprocess,struct,random,hashlib,json,time,os
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-0.22-self'));D=R/'artifacts/rotate-0.22'/('verify-'+str(time.time_ns()));D.mkdir(parents=True);rng=random.Random(221113)
pairs=[(x,n)for x in [0,1,0xffffffff,0x80000000,0x12345678,0x100000000,0xffffffffffffffff]for n in [0,1,7,8,16,31,32,33,63,64,0xffffffffffffffff]];pairs += [(1<<bit,n)for bit in range(64)for n in range(33)];pairs +=[(rng.getrandbits(64),rng.getrandbits(64))for _ in range(1800)]
def ror(x,n):x&=0xffffffff;n&=31;return((x>>n)|(x<<((32-n)&31)))&0xffffffff
inp=D/'pairs.bin';inp.write_bytes(b''.join(struct.pack('<2Q',*v)for v in pairs));expected=b''.join(struct.pack('<Q',ror(*v))for v in pairs)
source=D/'rotate.rf2';source.write_text('''profile RF2_SYSTEM_A64_V1
fn main(argc,argv)
 let p=buffer("pairs",65536)
 let fd=open(load64(argv+8),0,0)
 let n=read(fd,p,65536)
 do close(fd)
 let out=buffer("results",32768)
 let i=0
 while i<n//16
  do store64(out+i*8,ror32(load64(p+i*16),load64(p+i*16+8)))
  set i=i+1
 end
 do write(1,out,i*8)
 return 0
end
''')
for opt in [[],['--opt']]:
 exe=D/('rotate-opt'if opt else'rotate-plain');subprocess.run([C,source,exe,*opt],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',exe],check=True,capture_output=True);q=subprocess.run([exe,inp],capture_output=True,timeout=5);assert q.returncode==0 and q.stdout==expected,(len(pairs),len(q.stdout),len(expected))
# New primitive does not silently become an untyped record/function name or accept wrong arity.
negatives=['fn ror32(a,b)\n return 0\nend\nfn main(argc,argv)\nreturn 0\nend','record ror32(x:u64)\nfn main(argc,argv)\nreturn 0\nend','fn main(argc,argv)\nreturn ror32(1)\nend','fn main(argc,argv)\nreturn ror32(1,2,3)\nend']
for i,body in enumerate(negatives):
 p=D/f'refuse-{i}.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\n'+body+'\n');out=D/f'refuse-{i}';q=subprocess.run([C,p,out],capture_output=True);assert q.returncode==1 and not out.exists()
sha=(R/'examples/evidence-contract/lib/sha256.rf2').read_text().split('\n',1)[1];p=D/'sha.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\n'+sha+'''fn main(argc,argv)
 let p=buffer("message",65537)
 let fd=open(load64(argv+8),0,0)
 let n=read(fd,p,65537)
 do close(fd)
 if n>65536
  return 1
 end
 do write(1,sha256(p,n),32)
 return 0
end
''');shacases=[]
for opt in [[],['--opt']]:
 exe=D/('sha-opt'if opt else'sha-plain');subprocess.run([C,p,exe,*opt],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',exe],check=True,capture_output=True)
 for n in [0,1,3,31,55,56,63,64,65,127,128,129,255,1024,4096,32768,65536]:
  data=bytes(rng.randrange(256)for _ in range(n));f=D/'message';f.write_bytes(data);q=subprocess.run([exe,f],capture_output=True,timeout=5);assert q.returncode==0 and q.stdout==hashlib.sha256(data).digest(),(n,q.stdout.hex());shacases.append({'bytes':n,'optimized':bool(opt),'expectedSHA256':hashlib.sha256(data).hexdigest()})
report={'passed':True,'rotatePairsPerMode':len(pairs),'compilerModes':2,'negativeCases':len(negatives),'shaCases':shacases,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'shaSourceSHA256':hashlib.sha256((R/'examples/evidence-contract/lib/sha256.rf2').read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'ror32 returns low32input rotated by amountmod32, zero extended. Native32-bit RORV, no floating point or new Core/MCP effect. Finite native/Python differential SHA checks, not wholecrypto/compiler proof.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'report':str(D/'report.json'),'pairsPerMode':len(pairs),'shaCases':len(shacases)}))
