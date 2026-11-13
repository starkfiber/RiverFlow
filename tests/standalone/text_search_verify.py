"""Independent bytes oracle and guarded-page controls for native byte search.

Development controller only; no Python dependency in the RF2 library/application.
"""
from pathlib import Path
import hashlib,json,os,random,shutil,struct,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();D=R/'artifacts/text-search'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
SOURCE=R/'examples/text-search/main.rf2';LIB=R/'examples/text-search/lib/search.rf2';ROWS=[];rng=random.Random(310710)
def run(cmd,data=None,**kw):return subprocess.run(list(map(str,cmd)),input=data,capture_output=True,timeout=15,**kw)
def build(source,name,opt):
 out=D/name;q=run([C,source,out,'--compact',*(['--opt']if opt else[])]);assert q.returncode==0,(q.stderr,source)
 unsigned=hashlib.sha256(out.read_bytes()).hexdigest();q=run(['/usr/bin/codesign','-s','-',out]);assert q.returncode==0,q.stderr
 return out,unsigned
def expected(data,needle,overlap):
 if not needle:return len(data)+1,0
 first=data.find(needle);i=0;count=0
 while True:
  pos=data.find(needle,i)
  if pos<0:return count,first if first>=0 else 2**64-1
  count+=1;i=pos+(1 if overlap else len(needle))
# Native API harness supports binary needles and guard pages at both range ends.
(D/'lib').mkdir();shutil.copy2(LIB,D/'lib/search.rf2')
harness=D/'api.rf2';harness.write_text('''profile RF2_SYSTEM_A64_V1
use "lib/search.rf2"
fn main(argc,argv)
 let input=buffer("probe",1114144)
 let used=0
 let got=1
 while got!=0
  set got=read(0,input+used,1114144-used)
  if got>>63
   return 3
  end
  set used=used+got
  if used==1114144
   return 4
  end
 end
 if used<32
  return 2
 end
 let n=load64(input)
 let m=load64(input+8)
 let overlap=load64(input+16)
 let mode=load64(input+24)
 let data=input+32
 let needle=data
 if (n<=1048576)&(m<=128)
  if used!=32+n+m
   return 2
  end
  set needle=data+n
 end
 let a=0
 let b=0
 if mode
  if (n>16384)|(m>128)
   return 2
  end
  set a=syscall6(197,0,49152,0,4098,18446744073709551615,0)
  set b=syscall6(197,0,49152,0,4098,18446744073709551615,0)
  if (a==18446744073709551615)|(b==18446744073709551615)
   return 6
  end
  if syscall6(74,a+16384,16384,3,0,0,0)|syscall6(74,b+16384,16384,3,0,0,0)
   return 6
  end
  let da=a+32768-n
  let nb=b+32768-m
  if mode==2
   set da=a+16384
   set nb=b+16384
  end
  let i=0
  while i<n
   do store8(da+i,load8(data+i))
   set i=i+1
  end
  set i=0
  while i<m
   do store8(nb+i,load8(needle+i))
   set i=i+1
  end
  set data=da
  set needle=nb
 end
 let out=ByteSearch(0,0,0)
 let prefix=SearchPrefix()
 do byte_search(data,n,needle,m,overlap,prefix,out)
 let answer=buffer("answer",24)
 do store64(answer,out.status)
 do store64(answer+8,out.matches)
 do store64(answer+16,out.first)
 if mode
  if syscall6(73,a,49152,0,0,0,0)|syscall6(73,b,49152,0,0,0,0)
   return 6
  end
 end
 if write(1,answer,24)!=24
  return 5
 end
 return 0
end
''')
api_cases=[(b'',b'',0),(b'',b'x',1),(b'aaaaa',b'aa',0),(b'aaaaa',b'aa',1),(b'abc',b'abc',0),(b'abc',b'abcd',1),(bytes(range(256)),b'\0',0),(b'\xff\0\xff\0',b'\xff\0',1),('தமிழ் தமிழ்'.encode(),'மிழ்'.encode(),0),(b'a'*1048576,b'a'*127+b'b',1),(b'a'*1048576,b'a'*128,1),(b'a'*1048576,b'',0)]
for i in range(180):
 n=rng.randrange(0,900);m=rng.randrange(0,32);alphabet=[0,1,97,98,99,255] if i%2 else list(range(256));data=bytes(rng.choice(alphabet)for _ in range(n));needle=bytes(rng.choice(alphabet)for _ in range(m));api_cases.append((data,needle,i%2))
images=[]
for opt in [False,True]:
 app,appsha=build(SOURCE,'text-search-'+str(opt),opt);api,apisha=build(harness,'api-'+str(opt),opt);images.append(dict(optimized=opt,appBinary=str(app.relative_to(R)),apiBinary=str(api.relative_to(R)),appUnsignedSHA256=appsha,apiUnsignedSHA256=apisha))
 for i,(data,needle,overlap)in enumerate(api_cases):
  q=run([api],struct.pack('<4Q',len(data),len(needle),overlap,0)+data+needle);count,first=expected(data,needle,overlap);assert q.returncode==0 and q.stdout==struct.pack('<3Q',0,count,first),(opt,i,q.returncode,q.stdout,q.stderr)
  ROWS.append(dict(case='binary API oracle',optimized=opt,sample=i,bytes=len(data),needleBytes=len(needle),overlap=overlap))
 for mode in [1,2]:
  for data,needle,overlap in api_cases[:9]+[(b'a'*16384,b'a'*127+b'b',1),(b'x'*128,b'x'*128,1)]:
   q=run([api],struct.pack('<4Q',len(data),len(needle),overlap,mode)+data+needle);count,first=expected(data,needle,overlap);assert q.returncode==0 and q.stdout==struct.pack('<3Q',0,count,first),(opt,mode,q.returncode)
   ROWS.append(dict(case='guarded range',optimized=opt,mode=mode,bytes=len(data),needleBytes=len(needle)))
 for n,m,overlap in [(1048577,0,0),(0,129,0),(0,0,2),(2**64-1,2**64-1,0)]:
  q=run([api],struct.pack('<4Q',n,m,overlap,0));assert q.returncode==0 and q.stdout==struct.pack('<3Q',1,0,2**64-1),(opt,n,m,q.returncode,q.stdout)
  ROWS.append(dict(case='API bounds reject before read',optimized=opt,n=n,m=m,overlap=overlap))
 queries=['','a','aa','ana','தமிழ்','é','\n','--help','--overlap','x'*128]
 for i in range(120):
  query=queries[i%len(queries)];overlap=i%2;data=(b'a'*500 if i%3==0 else b'banana \0\xff Tamil '+ 'தமிழ் é'.encode())*(1+i%7)
  # --help is a conventional standalone command; with --overlap it is literal.
  if query=='--help'and not overlap:continue
  q=run([app,query,*(['--overlap']if overlap else[])],data);count,first=expected(data,query.encode(),overlap)
  answer=dict(bytes=len(data),query_bytes=len(query.encode()),matches=count,first_byte=first if count else None)
  assert q.returncode==0 and not q.stderr and json.loads(q.stdout)==answer,(opt,i,q.returncode,q.stdout,q.stderr,answer)
  ROWS.append(dict(case='CLI JSON oracle',optimized=opt,sample=i))
 for args,data,code in [([],b'',2),(['x','bad'],b'',2),(['x','--overlap','extra'],b'',2),(['x'*129],b'',2),(['x'],b'a'*1048577,4)]:
  q=run([app,*args],data);assert q.returncode==code and q.stdout==b'',(opt,args[:1],q.returncode,q.stdout)
  ROWS.append(dict(case='CLI refusal',optimized=opt,expectedExit=code))
 assert run([app,'x'],preexec_fn=lambda:os.close(0)).returncode==3
 assert run([app,'x'],b'xx',preexec_fn=lambda:os.close(1)).returncode==5
 q=run([app,'--help']);assert q.returncode==0 and b'Usage:'in q.stdout
 ROWS.append(dict(case='CLI descriptors/help',optimized=opt,checks=3))
report=dict(passed=True,schema='rf2.text.search.verification.v1',cases=len(ROWS),rows=ROWS,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [SOURCE,LIB]},images=images,limits='Finite Apple Silicon Mac native execution; independent Python bytes oracle, two optimizer modes, guard pages immediately outside each range, explicit size budgets. Exact byte semantics, not grapheme/locale/normalization. Trusted caller supplies valid nonaliasing readable ranges and writable output. Caller supplies a distinct typed prefix workspace; no thread support or ownership transfer is claimed. No speed, memory-safety, energy or AI token claim.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),passed=True,cases=len(ROWS))))
