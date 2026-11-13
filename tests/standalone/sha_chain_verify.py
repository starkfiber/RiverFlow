"""Independent split-span SHA state comparison, including empty/disjoint spans and canaries."""
from pathlib import Path
from sha_reference import compress
import subprocess,struct,random,json,time,hashlib,os
R=Path(__file__).resolve().parents[2];D=R/'artifacts/sha-memory'/('chain-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-memory-final-self'));rng=random.Random(251113)
s='''profile RF2_SYSTEM_A64_V1
fn main(argc,argv)
 let p=buffer("chain",8192)
 let fd=open(load64(argv+8),0,0)
 let n=read(fd,p,8192)
 do close(fd)
 let off=load64(p)
 let split=load64(p+8)
 let blocks=load64(p+16)
 let state=p+24+off
 let data=state+288
 do sha256_chain_armv8(state,data,split,data+split*64+16,blocks-split,state+32)
 do write(1,p,n)
 return 0
end
''';cases=0
for opt in [False,True]:
 p=D/('driver-opt.rf2'if opt else'driver-plain.rf2');p.write_text(s);exe=p.with_suffix('');subprocess.run([C,p,exe,*(['--opt']if opt else[])],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True)
 for off in range(16):
  for blocks in range(6):
   for split in range(blocks+1):
    state=[rng.getrandbits(32)for _ in range(8)];k=[rng.getrandbits(32)for _ in range(64)];data=rng.randbytes(blocks*64);prefix=struct.pack('<3Q',off,split,blocks)+b'P'*off;remaining=struct.pack('<64I',*k)+data[:split*64]+b'G'*16+data[split*64:]+b'T'*16;raw=prefix+struct.pack('<8I',*state)+remaining;expected=prefix+struct.pack('<8I',*compress(state,data,k))+remaining;f=D/'input';f.write_bytes(raw);q=subprocess.run([exe,f],capture_output=True,timeout=3);assert q.returncode==0 and q.stdout==expected,(off,blocks,split,opt);cases+=1
probe=D/'zero.rf2';probe.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\nreturn sha256_chain_armv8(0,0,0,0,0,0)\nend\n');exe=probe.with_suffix('');subprocess.run([C,probe,exe,'--opt'],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True);assert subprocess.run([exe],capture_output=True).returncode==0
# Check the independently assembled complete two-span instruction sequence.
obj=D/'oracle.o';subprocess.run(['/usr/bin/clang','-target','arm64-apple-macos11','-march=armv8-a+crypto','-c',R/'tests/standalone/sha256_chain_armv8.s','-o',obj],capture_output=True,check=True);b=obj.read_bytes();off=32;code=None
for _ in range(struct.unpack_from('<I',b,16)[0]):
 cmd,size=struct.unpack_from('<II',b,off)
 if cmd==0x19:
  for j in range(struct.unpack_from('<I',b,off+64)[0]):
   a=off+72+j*80
   if b[a:a+16].rstrip(b'\0')==b'__text':
    n=struct.unpack_from('<Q',b,a+40)[0];start=struct.unpack_from('<I',b,a+48)[0];code=b[start:start+n]
 off+=size
assert code is not None and exe.read_bytes().count(code)==1
negative=['fn sha256_chain_armv8(x)\nreturn x\nend\nfn main(argc,argv)\nreturn 0\nend','record sha256_chain_armv8(x:u64)\nfn main(argc,argv)\nreturn 0\nend','fn main(argc,argv)\nreturn sha256_chain_armv8(0,0,0,0,0)\nend','fn main(argc,argv)\nreturn sha256_chain_armv8(0,0,0,0,0,0,0)\nend','array Data(u8,8)\nview Window(Data)\nfn main(argc,argv)\nlet a=Data()\nlet v=Window(a,0,1)\nreturn sha256_chain_armv8(0,0,0,0,0,0)\nend']
for i,s in enumerate(negative):
 p=D/f'negative-{i}.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\n'+s+'\n');out=p.with_suffix('');q=subprocess.run([C,p,out],capture_output=True);assert q.returncode==1 and not out.exists()
report={'passed':True,'comparisons':cases,'negativeCases':len(negative),'independentAssemblerByteMatch':True,'zeroSpanNullNoOp':True,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'scope':'Finite arbitrary initial states/constants, every split for0..5blocks, offsets0..15, disjoint spans and canaries in both compiler modes. Valid nonoverlapping raw ranges required; no general memory or crypto proof.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'comparisons':cases,'report':str(D/'report.json')}))
