"""Two real native apps importing one canonical shared search library.

Independent Python byte oracles, exact line semantics and process-level failures.
No Python runtime is needed by either RF2 application.
"""
from pathlib import Path
import hashlib,json,os,random,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();D=R/'artifacts/shared-search'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
LIB=R/'examples/text-search/lib/search.rf2';SOURCES={'text-search':R/'examples/text-search/main.rf2','log-scan':R/'examples/text-search/log-scan.rf2'};ROWS=[];IMAGES=[];LIMIT=4096
source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [LIB,*SOURCES.values()]}
def run(args,data=b'',**kw):return subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=20,env={'PATH':'/nonexistent'},**kw)
def occurrences(data,q,overlap=False):
 if not q:return len(data)+1,0
 count=0;i=0;first=None
 while True:
  at=data.find(q,i)
  if at<0:return count,first
  if first is None:first=at
  count+=1;i=at+(1 if overlap else len(q))
def text_expected(data,q,overlap=False):
 count,first=occurrences(data,q,overlap)
 return dict(bytes=len(data),query_bytes=len(q),matches=count,first_byte=first)
def log_expected(data,q):
 lines=[]if not data else data.split(b'\n')
 if data.endswith(b'\n'):lines.pop()
 counts=[occurrences(line,q)[0]for line in lines]
 matching=sum(bool(n)for n in counts);first=next((i+1 for i,n in enumerate(counts)if n),None)
 return dict(bytes=len(data),query_bytes=len(q),lines=len(lines),matching_lines=matching,matches=sum(counts),first_line=first)
rng=random.Random(320422)
samples=[b'',b'\n',b'\n\n',b'one',b'one\n',b'one\ntwo',b'\r\n',b'ERROR one\r\nOK\nERROR ERROR\n',b'\0\xff\n\0\n', 'தமிழ்\nதமிழ் தமிழ்\r\n'.encode(),b'a'*1048576,b'\n'*1048576]
queries=['','one','ERROR','ana','\n','\r','தமிழ்','é','a'*128,'a'*512]
for i in range(80):
 alphabet=[0,10,13,65,66,97,98,255];samples.append(bytes(rng.choice(alphabet)for _ in range(rng.randrange(0,2048))))
for opt in [False,True]:
 apps={}
 for name,source in SOURCES.items():
  image=D/(name+'-'+str(opt));q=run([C,source,image,'--compact',*(['--opt']if opt else[])]);assert q.returncode==0,(name,q.stderr)
  raw=hashlib.sha256(image.read_bytes()).hexdigest();q=run(['/usr/bin/codesign','-s','-',image]);assert q.returncode==0,q.stderr;apps[name]=image
  IMAGES.append(dict(app=name,optimized=opt,binary=str(image.relative_to(R)),unsignedSHA256=raw,signedSHA256=hashlib.sha256(image.read_bytes()).hexdigest(),sharedLibrarySHA256=source_hashes[str(LIB.relative_to(R))]))
 for i,data in enumerate(samples):
  query=queries[i%len(queries)];needle=query.encode()
  for name,image in apps.items():
   args=[image,query];overlap=i%2==1
   if name=='text-search'and overlap:args+=['--overlap']
   q=run(args,data);expected=text_expected(data,needle,overlap)if name=='text-search'else log_expected(data,needle)
   assert q.returncode==0 and not q.stderr and json.loads(q.stdout)==expected,(name,opt,i,q.returncode,q.stdout,q.stderr,expected)
   ROWS.append(dict(case='independent application byte oracle',app=name,optimized=opt,sample=i,bytes=len(data),queryBytes=len(needle)))
 for query,data in [('a'*4096,b'a'*8192+b'\n'+b'a'*4096),('a'*4095+'b',b'a'*16384),('a'*511+'b',(b'a'*511+b'b')*2+b'\n')]:
  for name,image in apps.items():
   q=run([image,query],data);expected=text_expected(data,query.encode())if name=='text-search'else log_expected(data,query.encode())
   assert q.returncode==0 and json.loads(q.stdout)==expected,(name,opt,q.returncode,q.stdout,expected)
   ROWS.append(dict(case='extended query application oracle',app=name,optimized=opt,queryBytes=len(query),bytes=len(data)))
 for name,image in apps.items():
  # Split input into deliberately small writes, preserving the identical oracle.
  data=b'ERROR split\r\nOK\nERROR tail';query='ERROR';p=subprocess.Popen([str(image),query],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/nonexistent'})
  for i in range(0,len(data),3):p.stdin.write(data[i:i+3]);p.stdin.flush()
  p.stdin.close();raw=p.stdout.read();err=p.stderr.read();assert p.wait(timeout=10)==0 and not err
  expected=text_expected(data,b'ERROR')if name=='text-search'else log_expected(data,b'ERROR');assert json.loads(raw)==expected
  ROWS.append(dict(case='chunked stdin writes preserve result',app=name,optimized=opt))
  for args,data,code in [([],b'',2),(['x','unexpected'],b'',2),(['x'*(LIMIT+1)],b'',2),(['x'],b'a'*1048577,4)]:
   q=run([image,*args],data);assert q.returncode==code and not q.stdout,(name,opt,code,q.returncode,q.stdout,q.stderr)
   ROWS.append(dict(case='application refusal',app=name,optimized=opt,exit=code))
  assert run([image,'x'],preexec_fn=lambda:os.close(0)).returncode==3
  assert run([image,'x'],b'x',preexec_fn=lambda:os.close(1)).returncode==5
  assert run([image,'--help']).returncode==0
  ROWS.append(dict(case='borrowed descriptor failures and help',app=name,optimized=opt,checks=3))
# Prove source-module dependency wiring, rather than only matching import spelling.
# The altered library is confined to one disposable project; canonical sources stay frozen.
project=D/'module-dependency';(project/'lib').mkdir(parents=True)
mutated=LIB.read_text().replace('set out.matches=n+1','set out.matches=n+2',1)
assert mutated!=LIB.read_text();(project/'lib/search.rf2').write_text(mutated)
for name,source in SOURCES.items():
 staged=project/(name+'.rf2');staged.write_bytes(source.read_bytes());image=project/(name+'-mutant')
 q=run([C,staged,image,'--compact','--opt']);assert q.returncode==0,q.stderr
 assert run(['/usr/bin/codesign','-s','-',image]).returncode==0
 data=b'a\nb';q=run([image,''],data);assert q.returncode==0
 expected=text_expected(data,b'')if name=='text-search'else log_expected(data,b'')
 expected['matches']+=1 if name=='text-search'else expected['lines']
 assert json.loads(q.stdout)==expected,(name,q.stdout,expected)
 ROWS.append(dict(case='one isolated shared-module mutation affects both applications',app=name,librarySHA256=hashlib.sha256(mutated.encode()).hexdigest()))

for p in [LIB,*SOURCES.values()]:assert hashlib.sha256(p.read_bytes()).hexdigest()==source_hashes[str(p.relative_to(R))],('source changed during campaign',p)
for source in SOURCES.values():assert 'use "lib/search.rf2"'in source.read_text()
report=dict(passed=True,schema='rf2.shared.search.apps.verification.v1',cases=len(ROWS),rows=ROWS,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources=source_hashes,images=IMAGES,oneCanonicalLibrary=True,queryLimit=LIMIT,prefixPayloadBytes=LIMIT*8,limits='Two actual native CLIs on one Apple Silicon Mac; exact byte oracles, LF-only line delimiter (CR retained), empty-input/query contracts, split writes, descriptor and budget failures. These are bounded local application tests, not evidence of live production log incidents, Unicode normalization, general security, concurrency, PDF extraction or speed superiority.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),passed=True,cases=len(ROWS))))
