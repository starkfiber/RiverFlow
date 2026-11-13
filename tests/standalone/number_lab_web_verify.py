"""Actual native private-loopback Number Lab acceptance and failure controls."""
from pathlib import Path
import atexit,hashlib,http.client,json,os,re,select,socket,subprocess,time,urllib.parse,random
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();SOURCE=R/'examples/number-lab-web/main.rf2';D=R/'artifacts/number-lab-web'/('verify-'+str(time.time_ns()));D.mkdir(parents=True);CONTROLLER_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();ROWS=[]
B=D/'number-lab-web';q=subprocess.run([str(C),str(SOURCE),str(B),'--opt','--compact'],capture_output=True,timeout=30);assert q.returncode==0,q.stderr;subprocess.run(['/usr/bin/codesign','-s','-',B],capture_output=True,check=True)
# Exercise a retained function pack before running the complete HTTP campaign.
if os.environ.get('RF2_WEB_PACK_TEST') == '1':
 cache=D/'packed-units';cache.mkdir(mode=0o700)
 for stage in ['cold','warm']:
  out=D/('packed-'+stage)
  q=subprocess.run([str(C),str(SOURCE),str(out),'--opt','--compact','--reuse-pack',str(cache)],capture_output=True,timeout=30)
  assert q.returncode==0,q.stderr
  # Both images use different signing identifiers; compare unsigned image bytes.
  clean=D/('oracle-'+stage)
  q=subprocess.run([str(C),str(SOURCE),str(clean),'--opt','--compact'],capture_output=True,timeout=30)
  assert q.returncode==0 and out.read_bytes()==clean.read_bytes(),q.stderr
  receipt=json.loads(Path(str(out)+'.reuse.json').read_text())
  if stage=='warm':assert receipt['reused']>0 and receipt['unitContainerReads']==1
 B=out;subprocess.run(['/usr/bin/codesign','-s','-',B],capture_output=True,check=True)
p=subprocess.Popen([str(B)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/nonexistent'});atexit.register(lambda:p.kill()if p.poll()is None else None);assert select.select([p.stdout],[],[],10)[0];URL=p.stdout.readline().decode().strip().rstrip('/');assert re.fullmatch(r'http://127\.0\.0\.1:[0-9]+',URL);PORT=int(URL.rsplit(':',1)[1]);HOST='127.0.0.1:'+str(PORT)
def req(method,path,body=None,headers=None):
 c=http.client.HTTPConnection('127.0.0.1',PORT,timeout=6);c.request(method,path,body=body,headers=headers or {});r=c.getresponse();raw=r.read();result=r.status,dict((k.lower(),v)for k,v in r.getheaders()),raw;c.close();return result
def page():
 status,headers,raw=req('GET','/');assert status==200 and len(raw)<32768
 return headers,raw

def fields(raw):return {k:re.search(('name='+k+' value="([^"]+)"').encode(),raw).group(1).decode()for k in ['token','rev']}
def state(raw):return tuple(re.search(pattern,raw).group(1)for pattern in [b'id=decimal>([0-9]+)',b'id=hex>([^<]+)',b'id=ascii>([^<]+)',b'id=gate-result>([0-9]+)',b'id=score>([0-9]+)'])+(fields(raw)['rev'].encode(),)
def post(action,more=None,raw=None,path='/play',extra=None):
 f=fields(raw or page()[1]);f.update(action=action)
 if more:f.update(more)
 body=urllib.parse.urlencode(f);headers={'Origin':URL,'Content-Type':'application/x-www-form-urlencoded'}
 if extra:headers.update(extra)
 return req('POST',path,body,headers)
def record(name,**kw):ROWS.append(dict(case=name,**kw))
headers,raw=page();initial=state(raw);assert initial[:3]==(b'65',b'41',b'A');assert '<script'not in raw.decode().lower();assert b'http:'not in raw and b'https:'not in raw;assert b'grid-template-columns:repeat(4' in raw;assert b'focus-visible'in raw;assert headers['cache-control']=='no-store' and headers['x-content-type-options']=='nosniff';assert headers['referrer-policy']=='same-origin';assert "default-src 'none'"in headers['content-security-policy'] and "frame-ancestors 'none'"in headers['content-security-policy'];record('self-contained initial page and defensive headers')
# GET is a read-only operation, preserving revision and state across refresh.
assert fields(page()[1])==fields(raw) and state(page()[1])==initial;record('GET refresh is read-only')
assert req('GET','/',headers={'Origin':URL})[0]==200;record('same-origin GET remains read-only')
for n in [0,1,31,32,34,38,39,60,62,65,127,128,255]:
 status,h,_=post('show',{'value':n});assert status==303 and h['location']=='/';raw=page()[1];s=state(raw);expected={32:b'space',34:b'&quot;',38:b'&amp;',39:b'&#39;',60:b'&lt;',62:b'&gt;'}.get(n,chr(n).encode()if 32<=n<=126 else b'control'if n<128 else b'not ASCII');assert s[0]==str(n).encode() and s[1]==f'{n:02X}'.encode() and s[2]==expected
 for weight in [128,64,32,16,8,4,2,1]:
  marker=f'aria-label="Toggle bit {weight}" aria-pressed="'.encode();bit=re.search(re.escape(marker)+b'(true|false)',raw).group(1);assert bit==(b'true'if n&weight else b'false')
 record('computed byte and safe HTML character',value=n)
# Real form toggles: 65 XOR128 becomes193, then the same bit toggles back.
post('show',{'value':65});raw=page()[1];target=int(re.search(b'name=value value="([0-9]+)"',raw).group(1));assert target==193;assert post('show',{'value':target})[0]==303 and state(page()[1])[0]==b'193';assert post('show',{'value':65})[0]==303;record('rendered bit toggle posts computed value')
rng=random.Random(29014)
for op in ['and','or','xor','not']:
 for _ in range(12):
  a=rng.randrange(256);b=rng.randrange(256);expected={'and':lambda:a&b,'or':lambda:a|b,'xor':lambda:a^b,'not':lambda:a^255}[op]();assert post('gate',{'a':a,'b':b,'op':op})[0]==303;s=state(page()[1]);assert int(s[0])==expected and int(s[3])==expected;record('independent gate calculation',operation=op,a=a,b=b,result=expected)
score=0
for a,b in [(0,0),(0,1),(1,0),(1,1)]:
 assert post('quiz',{'a':a,'b':b})[0]==303;raw=page()[1];assert f'{a} AND {b} = ?'.encode()in raw;assert post('answer',{'value':(a&b)^1})[0]==303;raw=page()[1];assert b'Not quite.'in raw and f'{a} AND {b} = ?'.encode()in raw and int(state(raw)[4])==score
 assert post('answer',{'value':a&b})[0]==303;raw=page()[1];score+=1;assert b'You got it!'in raw and int(state(raw)[4])==score;record('quiz wrong-answer recovery and correct score',a=a,b=b)
# Duplicate/unknown/encoded/truncated fields and invalid values must not change state.
invalid=[{'action':'show','value':'256'},{'action':'show','value':'-1'},{'action':'show','value':'1.0'},{'action':'show','value':'1e2'},{'action':'show','value':'<script>'},{'action':'gate','a':'1','b':'2','op':'wat'},{'action':'quiz','a':'2','b':'0'},{'action':'answer','value':'2'},{'action':'answer','value':'0'},{'action':'show','value':'65','extra':'1'},{'action':'show'}, {'action':'wat','value':'0'}]
for more in invalid:
 raw=page()[1];before=state(raw);f=fields(raw);f.update(more);status,_,_=req('POST','/play',urllib.parse.urlencode(f),{'Origin':URL,'Content-Type':'application/x-www-form-urlencoded'});assert status==400,(more,status);assert state(page()[1])==before;record('invalid form preserves state',form=more)
raw=page()[1];before=state(raw);f=fields(raw)
for suffix in ['&value=2','&%76alue=2','&token='+f['token'],'&bogus=0','&','&x=%00']:
 body=urllib.parse.urlencode(dict(f,action='show',value=1))+suffix;assert req('POST','/play',body,{'Origin':URL,'Content-Type':'application/x-www-form-urlencoded'})[0]==400;assert state(page()[1])==before;record('duplicate or malformed fields preserve state',suffix=suffix.split('=')[0])
for token in ['', '0'*32, 'x'*32]:
 f=fields(page()[1]);f.update(action='show',value=1,token=token);assert req('POST','/play',urllib.parse.urlencode(f),{'Origin':URL,'Content-Type':'application/x-www-form-urlencoded'})[0]==403;assert state(page()[1])==before;record('incorrect capability token refuses')
# A null Origin stays denied; legitimate native forms retain their real Origin via same-origin referrer policy.
f=fields(page()[1]);f.update(action='show',value=1);before=state(page()[1]);assert req('POST','/play',urllib.parse.urlencode(f),{'Origin':'null','Content-Type':'application/x-www-form-urlencoded'})[0]==400;assert state(page()[1])==before;record('null Origin remains denied after browser-policy correction')
stale=page()[1];assert post('show',{'value':77},stale)[0]==303;after=state(page()[1]);assert post('show',{'value':88},stale)[0]==409;assert state(page()[1])==after;record('stale revision refuses')
# Raw HTTP probes retain duplicate headers and binary request-line cases.
def wire(data,timeout=6):
 with socket.create_connection(('127.0.0.1',PORT),timeout=timeout)as s:
  s.settimeout(timeout);s.sendall(data);result=b''
  while True:
   try:x=s.recv(65536)
   except ConnectionResetError:break
   if not x:break
   result+=x
 return result
base=b'GET / HTTP/1.1\r\nHost: '+HOST.encode()+b'\r\n'
probes=[('wrong Host',b'GET / HTTP/1.1\r\nHost: attacker.example\r\n\r\n'),('missing Host',b'GET / HTTP/1.1\r\n\r\n'),('duplicate Host',base+b'Host: '+HOST.encode()+b'\r\n\r\n'),('method refusal',b'DELETE / HTTP/1.1\r\nHost: '+HOST.encode()+b'\r\n\r\n'),('HTTP version refusal',b'GET / HTTP/1.0\r\nHost: '+HOST.encode()+b'\r\n\r\n'),('binary path refusal',b'GET /\x00x HTTP/1.1\r\nHost: '+HOST.encode()+b'\r\n\r\n'),('transfer encoding refusal',base+b'Transfer-Encoding: chunked\r\n\r\n'),('expect refusal',base+b'Expect: 100-continue\r\n\r\n'),('GET body refusal',base+b'Content-Length: 1\r\n\r\nx'),('pipeline refusal',base+b'\r\n'+base+b'\r\n'),('oversized headers',base+b'X-Long: '+b'x'*4100+b'\r\n\r\n')]
for name,request in probes:
 before=state(page()[1]);reply=wire(request);assert reply.startswith(b'HTTP/1.1 400'),(name,reply[:80]);assert state(page()[1])==before;record(name)
f=fields(page()[1]);body=urllib.parse.urlencode(dict(f,action='show',value=1)).encode();posthead=b'POST /play HTTP/1.1\r\nHost: '+HOST.encode()+b'\r\nOrigin: '+URL.encode()+b'\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: '+str(len(body)).encode()+b'\r\n'
for name,request in [('duplicate length',posthead+b'Content-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body),('duplicate origin',posthead+b'Origin: '+URL.encode()+b'\r\n\r\n'+body),('wrong origin',posthead.replace(URL.encode(),b'http://attacker.example')+b'\r\n'+body),('missing origin',posthead.replace(b'Origin: '+URL.encode()+b'\r\n',b'')+b'\r\n'+body),('oversized body',posthead.replace(b'Content-Length: '+str(len(body)).encode()+b'\r\n',b'Content-Length: 257\r\n')+b'\r\n'+b'x'*257)]:
 before=state(page()[1]);reply=wire(request);assert reply.startswith(b'HTTP/1.1 400'),(name,reply[:80]);assert state(page()[1])==before;record(name)
assert req('GET','/missing')[0]==404;assert req('GET','/?value=1')[0]==404;record('unknown and query routes refuse')
# Idle preconnections do not block an ordinary request. Close all test sockets.
idle=[socket.create_connection(('127.0.0.1',PORT),timeout=3)for _ in range(3)]
try:assert page()[0]['cache-control']=='no-store';record('idle preconnections permit active GET')
finally:
 for s in idle:s.close()
# A ready partial request gets a monotonic absolute deadline; the server recovers.
start=time.monotonic();reply=wire(base+b'X-Partial: unfinished',timeout=5);duration=time.monotonic()-start;assert duration<4.5 and reply.startswith(b'HTTP/1.1 400');assert page()[0]['cache-control']=='no-store';record('partial header deadline and recovery',observedSeconds=duration)
start=time.monotonic();reply=wire(posthead+b'\r\n'+body[:-3],timeout=5);duration=time.monotonic()-start;assert duration<4.5 and reply.startswith(b'HTTP/1.1 400');assert page()[0]['cache-control']=='no-store';record('partial body deadline and recovery',observedSeconds=duration)
# A drip-fed request cannot restart the absolute ready-request deadline.
before=state(page()[1]);start=time.monotonic()
with socket.create_connection(('127.0.0.1',PORT),timeout=5)as drip:
 drip.settimeout(5);drip.sendall(base+b'X-Drip: ')
 for _ in range(6):
  time.sleep(.25)
  try:drip.sendall(b'x')
  except BrokenPipeError:break
 reply=b''
 while True:
  try:part=drip.recv(65536)
  except ConnectionResetError:break
  if not part:break
  reply+=part
duration=time.monotonic()-start;assert reply.startswith(b'HTTP/1.1 400') and duration<3.4,(duration,reply[:80]);assert state(page()[1])==before;record('drip header cannot extend absolute deadline',observedSeconds=duration)
# Rejected quit cannot stop the listener; accepted quit closes all descriptors.
raw=page()[1];f=fields(raw);f['token']='bad';assert req('POST','/quit',urllib.parse.urlencode(f),{'Origin':URL,'Content-Type':'application/x-www-form-urlencoded'})[0]==403;assert page()[0]['cache-control']=='no-store';record('invalid quit token preserves service')
f=fields(page()[1]);status,_,raw=req('POST','/quit',urllib.parse.urlencode(f),{'Origin':URL,'Content-Type':'application/x-www-form-urlencoded'});assert status==200 and b'See you next time!'in raw;p.wait(timeout=5);assert p.returncode==0 and p.stderr.read()==b''
try:s=socket.create_connection(('127.0.0.1',PORT),timeout=1)
except OSError:pass
else:s.close();raise AssertionError('listener remained open after quit')
record('accepted quit closes listener and cleanly exits')
# Real application source remains byte-identical under opt-in function reuse.
cache=D/'units';cache.mkdir(mode=0o700)
for label in ['first','warm']:
 image=D/('reuse-'+label);oracle=D/('clean-'+label);flags=['--opt','--compact']
 q=subprocess.run([str(C),str(SOURCE),str(image),*flags,'--reuse-cache',str(cache)],capture_output=True,timeout=30);assert q.returncode==0,q.stderr
 q=subprocess.run([str(C),str(SOURCE),str(oracle),*flags],capture_output=True,timeout=30);assert q.returncode==0,q.stderr;assert image.read_bytes()==oracle.read_bytes()
 reuse=json.loads(Path(str(image)+'.reuse.json').read_text());assert reuse['reused']==0 if label=='first'else reuse['reused']>0;record('native graphical app '+label+' function-reuse clean bytes',reuse=reuse)
report={'passed':True,'schema':'rf2.number.lab.web.verification.v1','cases':len(ROWS),'rows':ROWS,'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'controllerSHA256':CONTROLLER_SHA,'executableSHA256':hashlib.sha256(B.read_bytes()).hexdigest(),'cleanupVerified':True,'executedRetainedPackImage':os.environ.get('RF2_WEB_PACK_TEST')=='1','target':'macos-arm64','scope':'Actual RF2 native private loopback HTTP and computed learning-game state. Browser rendering is not validated by this HTTP controller. No public hosting, external educational, platform, hardware, energy or token result.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'passed':True,'cases':len(ROWS)}))
