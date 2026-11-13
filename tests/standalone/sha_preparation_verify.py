"""Primitive, reused-state and actual CLI acceptance checks. Independent development oracle."""
from pathlib import Path
import subprocess,struct,random,hashlib,json,time,os,tempfile
R=Path(__file__).resolve().parents[2];D=R/'artifacts/sha-stream'/('verify-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-sha-prep3-self'));rng=random.Random(241113)
def build(name,text,opt):
 p=D/(name+'.rf2');p.write_text('profile RF2_SYSTEM_A64_V1\n'+text);out=D/name;subprocess.run([C,p,out,*(['--opt']if opt else[])],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);return out
values=[0,1,0xffffffff,0x12345678,0x100000000,0xffffffffffffffff]+[1<<i for i in range(64)]+[rng.getrandbits(64)for _ in range(2000)];fixture=D/'words';fixture.write_bytes(b''.join(struct.pack('<Q',v)for v in values));expected=b''.join(struct.pack('<2Q',int.from_bytes((v&0xffffffff).to_bytes(4,'little'),'big'),int.from_bytes(v.to_bytes(8,'little'),'big'))for v in values)
primitive='''fn main(argc,argv)
let p=buffer("p",32768)
let fd=open(load64(argv+8),0,0)
let n=read(fd,p,32768)
do close(fd)
let i=0
let out=buffer("swapped",65536)
while i<n
 do store64(out+i*2,bswap32(load64(p+i)))
 do store64(out+i*2+8,bswap64(load64(p+i)))
 set i=i+8
end
do write(1,out,n*2)
return 0
end
'''
sha=(R/'examples/evidence-contract/lib/sha256.rf2').read_text().split('\n',1)[1]
lengths=[0,63,64,55,56,65,127,128,129,1,4096,32768]*6
# One process sees changing lengths and padding, rather than restarting scratch state per digest.
seq='''fn main(argc,argv)
 let data=buffer("reuse",32768)
 let i=0
 while i<32768
  do store8(data+i,i&255)
  set i=i+1
 end
'''
for j,n in enumerate(lengths):seq+=f' do store8(data,{j}&255)\n do write(1,sha256(data,{n}),32)\n'
seq+=' return 0\nend\n';data=bytearray(bytes(range(256))*128);expected_seq=b''
for j,n in enumerate(lengths):data[0]=j&255;expected_seq+=hashlib.sha256(data[:n]).digest()
app_checks=[]
for opt in [False,True]:
 exe=build('swap'+('-opt'if opt else'-plain'),primitive,opt);q=subprocess.run([exe,fixture],capture_output=True,check=True);assert q.stdout==expected
 exe=build('reuse'+('-opt'if opt else'-plain'),sha+seq,opt);q=subprocess.run([exe],capture_output=True,check=True);assert q.stdout==expected_seq
 app=D/('file-checksum-opt'if opt else'file-checksum-plain');subprocess.run([C,R/'examples/file-checksum.rf2',app,*(['--opt']if opt else[])],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',app],check=True,capture_output=True)
 with tempfile.TemporaryDirectory(prefix='rf2-checksum-')as td:
  t=Path(td);f=t/'file';link=t/'link';link.symlink_to(f);fifo=t/'fifo';os.mkfifo(fifo)
  for n in [0,1,55,56,63,64,65,127,128,129,4096,32768,1048576]:
   raw=rng.randbytes(n);f.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest();stdout=(digest+'\n').encode()
   for arg,rc in [(None,0),(digest,0),(digest.upper(),0),('0'*64,1)]:
    q=subprocess.run([app,f,*([]if arg is None else[arg])],capture_output=True,timeout=10);assert q.returncode==rc and q.stdout==stdout,(n,arg,q.returncode,q.stdout);app_checks.append({'opt':opt,'bytes':n,'mode':'produce'if arg is None else'verify','exit':rc})
  for args in [[],[f,'x'],[f,'f'*63],[f,'f'*65],[f,'g'*64],[f,'0'*64,'extra'],[t/'absent'],[link],[fifo],[t]]:
   q=subprocess.run([app,*map(str,args)],capture_output=True,timeout=2);assert q.returncode==2 and q.stdout==b'',(args,q.returncode,q.stdout);app_checks.append({'opt':opt,'rejected':True})
  f.write_bytes(b'x'*1048577);q=subprocess.run([app,f],capture_output=True,timeout=2);assert q.returncode==2 and q.stdout==b'';assert f.stat().st_size==1048577;app_checks.append({'opt':opt,'oversizeRefused':True})
# Independently qualify the stronger direct C comparator's full digests.
cp=D/'direct-check.c';cp.write_text((R/'tests/fixtures/sha256_direct_armv8.c').read_text()+'\n#include <stdio.h>\nint main(int argc,char**argv){unsigned char d[1048577];FILE*f=fopen(argv[1],"rb");if(!f)return 2;size_t n=fread(d,1,sizeof(d),f);fclose(f);if(n>1048576)return 2;fwrite(direct_call(d,n),1,32,stdout);return 0;}\n');ce=D/'direct-check';subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',cp,'-o',ce],capture_output=True,check=True)
for n in list(range(140))+[255,256,511,512,513,1024,4096,32768,65536,1048576]:
 data=rng.randbytes(n);(D/'direct-message').write_bytes(data);q=subprocess.run([ce,D/'direct-message'],capture_output=True,check=True);assert q.stdout==hashlib.sha256(data).digest()
neg=['fn bswap32(x)\nreturn x\nend\nfn main(argc,argv)\nreturn 0\nend','record bswap32(x:u64)\nfn main(argc,argv)\nreturn 0\nend','fn main(argc,argv)\nreturn bswap32()\nend','fn main(argc,argv)\nreturn bswap32(1,2)\nend']
neg+= [s.replace('bswap32','bswap64') for s in neg]
for i,s in enumerate(neg):
 p=D/f'negative-{i}.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\n'+s+'\n');out=D/f'negative-{i}';q=subprocess.run([C,p,out],capture_output=True);assert q.returncode==1 and not out.exists()
report={'passed':True,'directCFullDigestCases':150,'primitiveCasesPerMode':len(values),'primitiveComparisons':len(values)*4,'reusedStateDigests':len(lengths)*2,'negativeCases':len(neg),'appChecks':len(app_checks),'appCases':app_checks,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'shaSourceSHA256':hashlib.sha256((R/'examples/evidence-contract/lib/sha256.rf2').read_bytes()).hexdigest(),'appSourceSHA256':hashlib.sha256((R/'examples/file-checksum.rf2').read_bytes()).hexdigest(),'scope':'Finite local default/optimized byte-swap, changing-message reuse and file-integrity CLI checks. No thread-safety, authenticated origin or general memory safety.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','primitiveComparisons','reusedStateDigests','negativeCases','appChecks']}|{'report':str(D/'report.json')}))
