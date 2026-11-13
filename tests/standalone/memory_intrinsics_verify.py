"""Raw-range functional oracle with full-region canaries and live-register checks."""
from pathlib import Path
import subprocess,struct,random,json,hashlib,time,os
R=Path(__file__).resolve().parents[2];D=R/'artifacts/sha-memory'/('verify-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-memory1-self'));rng=random.Random(251113)
source='''profile RF2_SYSTEM_A64_V1
fn transform(dst,src,n,mode)
 let a=111
 let b=222
 let c=333
 if mode==0
  do fill_zero(dst,n)
 else
  do bswap32_copy(dst,src,n)
 end
 return a+b+c+n+mode
end
fn main(argc,argv)
 let p=buffer("case",16416)
 let fd=open(load64(argv+8),0,0)
 let got=read(fd,p,16416)
 do close(fd)
 if got!=16416
  return 2
 end
 let mode=load64(p)
 let n=load64(p+8)
 let src=load64(p+16)
 let dst=load64(p+24)
 if transform(p+32+dst,p+32+src,n,mode)!=666+n+mode
  return 3
 end
 do write(1,p,16416)
 return 0
end
'''
lengths=list(range(129))+[255,256,257,511,512,513,1023,1024,2047,2048,4096];words=list(range(21))+[31,32,33,63,64,65,127,128,129,256,1024];cases=[(0,n,0,32+off)for n in lengths for off in range(8)];cases +=[(1,n,32+off,8192+((off*7)&15))for n in words for off in range(16)];cases +=[(1,n,32+off,32+off)for n in words for off in range(16)];checks=0
for opt in [False,True]:
 p=D/('driver-opt.rf2'if opt else'driver-plain.rf2');p.write_text(source);exe=p.with_suffix('');subprocess.run([C,p,exe,*(['--opt']if opt else[])],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True)
 for mode,n,src,dst in cases:
  raw=bytearray(rng.randbytes(16384));expect=raw[:]
  if mode==0:expect[dst:dst+n]=bytes(n)
  else:
   original=bytes(raw[src:src+n*4]);expect[dst:dst+n*4]=b''.join(original[i:i+4][::-1]for i in range(0,n*4,4))
  header=struct.pack('<4Q',mode,n,src,dst);f=D/'input';f.write_bytes(header+raw);q=subprocess.run([exe,f],capture_output=True,timeout=3);assert q.returncode==0 and q.stdout==header+expect,(opt,mode,n,src,dst,q.returncode);checks+=1
# Literal-size lowering must preserve exact byte ranges and evaluate complex arguments.
const_cases=[('fill',n)for n in range(258)]+[('swap',n)for n in range(66)]
const_source='profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n let p=buffer("literal",2048)\n let i=0\n'
expected_constant=b''
for kind,n in const_cases:
 const_source+=' set i=0\n while i<2048\n  do store8(p+i,i&255)\n  set i=i+1\n end\n'
 data=bytearray(bytes(range(256))*8)
 if kind=='fill':
  const_source+=f' do fill_zero(p+7,{n})\n';data[7:7+n]=bytes(n)
 else:
  const_source+=f' do bswap32_copy(p+1027,p+3,{n})\n';original=bytes(data[3:3+n*4]);data[1027:1027+n*4]=b''.join(original[j:j+4][::-1]for j in range(0,n*4,4))
 const_source+=' do write(1,p,2048)\n';expected_constant+=bytes(data)
const_source+=' return 0\nend\n'
for opt in [False,True]:
 p=D/('literal-opt.rf2'if opt else'literal-plain.rf2');p.write_text(const_source);out=p.with_suffix('');subprocess.run([C,p,out,*(['--opt']if opt else[])],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);q=subprocess.run([out],check=True,capture_output=True,timeout=10);assert q.stdout==expected_constant
probe=D/'probe.rf2';probe.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\nlet zero=argc-1\nreturn fill_zero(0,zero) | bswap32_copy(0,0,zero)\nend\n');exe=D/'probe';subprocess.run([C,probe,exe,'--opt'],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True);assert subprocess.run([exe],capture_output=True).returncode==0
for name in ['fill_zero','bswap32_copy']:
 obj=D/(name+'.o');subprocess.run(['/usr/bin/clang','-target','arm64-apple-macos11','-c',R/'tests/standalone'/(name+'.s'),'-o',obj],capture_output=True,check=True);raw=obj.read_bytes();off=32;code=None
 for _ in range(struct.unpack_from('<I',raw,16)[0]):
  cmd,size=struct.unpack_from('<II',raw,off)
  if cmd==0x19:
   for j in range(struct.unpack_from('<I',raw,off+64)[0]):
    a=off+72+j*80
    if raw[a:a+16].rstrip(b'\0')==b'__text':
     n=struct.unpack_from('<Q',raw,a+40)[0];start=struct.unpack_from('<I',raw,a+48)[0];code=raw[start:start+n]
  off+=size
 assert code is not None and exe.read_bytes().count(code)==1
negative=[]
for name,args,wrong in [('fill_zero','0,0','0'),('bswap32_copy','0,0,0','0,0')]:
 negative += [f'fn {name}(x)\nreturn x\nend\nfn main(argc,argv)\nreturn 0\nend',f'record {name}(x:u64)\nfn main(argc,argv)\nreturn 0\nend',f'fn main(argc,argv)\nreturn {name}({wrong})\nend',f'fn main(argc,argv)\nreturn {name}({args},0)\nend',f'record Thing(x:u64)\nfn main(argc,argv)\nlet a=Thing(0)\nreturn {name}(a,{args})\nend']
 view=f'array Data(u8,8)\nview Window(Data)\nfn main(argc,argv)\nlet a=Data()\nlet v=Window(a,0,1)\nreturn {name}({args})\nend';negative.append(view)
 # Confirm the live-view control is otherwise valid, preventing a false refusal claim.
 p=D/(name+'-view-control.rf2');p.write_text('profile RF2_SYSTEM_A64_V1\n'+view.replace(f'{name}({args})','0')+'\n');subprocess.run([C,p,p.with_suffix('')],capture_output=True,check=True)
for i,s in enumerate(negative):
 p=D/f'negative-{i}.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\n'+s+'\n');out=p.with_suffix('');q=subprocess.run([C,p,out],capture_output=True);assert q.returncode==1 and not out.exists(),i
report={'passed':True,'casesPerCompilerMode':len(cases),'comparisons':checks,'preservedLiveRegisters':7,'negativeCases':len(negative),'literalSizeComparisons':len(const_cases)*2,'zeroCountNullNoOp':True,'independentAssemblerByteMatch':True,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Valid raw ranges, byte counts0..4096, word counts0..1024, unaligned/disjoint/exact-in-place copy, full region canaries. Partial overlap outside copy contract. No bounds/ownership proof or new Core/MCP effect.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'comparisons':checks,'negativeCases':len(negative),'literalSizeComparisons':len(const_cases)*2,'report':str(D/'report.json')}))
