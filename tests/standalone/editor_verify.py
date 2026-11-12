"""Actual loopback editor tests. No real customer data; no browser substitute claim."""
from pathlib import Path
from decimal import Decimal
import subprocess,os,json,re,select,urllib.parse,http.client,socket,time,atexit,tempfile,hashlib
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_TEST_BINARY',str(R/'output/native-0.9/rf2')));OLD=R/'output/package/rf2-0.8.0/rf2'
p=subprocess.Popen([str(B),'editor'],stdout=subprocess.PIPE,stderr=subprocess.PIPE);atexit.register(lambda:p.kill()if p.poll()is None else None);assert select.select([p.stdout],[],[],15)[0];start=p.stdout.readline().decode();url=re.search(r'http://127\.0\.0\.1:(\d+)',start).group(0);port=int(url.rsplit(':',1)[1]);report={'passed':False,'successfulEdits':0,'refusals':0,'documentRoundtrips':0,'pdf08ByteComparisons':0,'uploadCases':0,'idleConcurrencyCases':0,'scope':'Private single-draft loopback GUI protocol; programming fixtures only'}
def request(method,path,body=None,headers=None):
 c=http.client.HTTPConnection('127.0.0.1',port,timeout=10);h=headers or {};c.request(method,path,body=body,headers=h);r=c.getresponse();data=r.read();answer=(r.status,dict((k.lower(),v)for k,v in r.getheaders()),data);c.close();return answer
def page():
 code,headers,data=request('GET','/');assert code==200;return data.decode()
def fields(text):return {k:re.search('name='+k+' value="([^"]+)"',text).group(1)for k in ['token','rev']}
def download(kind,text=None):
 v=fields(text or page());return request('POST','/'+kind,urllib.parse.urlencode(v),{'Origin':url,'Content-Type':'application/x-www-form-urlencoded'})
def doc():
 code,_,body=download('document');assert code==200;return json.loads(body)
def edit(rows,action='apply',currency='MYR',tax='600',extra=None,text=None):
 f=fields(text or page());f.update(rows=str(len(rows)),currency=currency,tax=str(tax),action=action)
 for i,(q,price)in enumerate(rows):f['q'+str(i)]=str(q);f['p'+str(i)]=str(price)
 if extra:f.update(extra)
 return request('POST','/edit',urllib.parse.urlencode(f),{'Origin':url,'Content-Type':'application/x-www-form-urlencoded'})
s=page();assert '<script'not in s and 'http'not in re.sub('http-equiv','',s);assert 'Quantity' in s
code,h,_=request('GET','/');assert "default-src 'none'"in h['content-security-policy']and h['cache-control']=='no-store'
for rows in [[],[(2,'12.50'),(1,'3.99')],[(1,'0')],[(1,'0.01')],[(1,'42949672.95')]]:
 code,_,_=edit(rows,tax=0 if rows==[(1,'42949672.95')]else 600);assert code==303,(rows,code);report['successfulEdits']+=1
 expected=[{'quantity':q,'unit_cents':int(Decimal(price)*100)}for q,price in rows];d=doc();assert d['lines']==expected;report['documentRoundtrips']+=1
edit([(2,'12.50'),(1,'3.99')]);saved=doc();before=page();v=fields(before)
# Compare exported bytes to frozen 0.8 CLI, not merely text that looks plausible.
code,_,pdf=download('pdf',before);assert code==200 and pdf.startswith(b'%PDF-1.4')
with tempfile.TemporaryDirectory(prefix='rf2-editor-')as tmp:
 source=Path(tmp)/'doc.json';out=Path(tmp)/'old.pdf';source.write_text(json.dumps(saved));subprocess.run([str(OLD),'invoice','pdf',str(source),str(out)],check=True,capture_output=True);assert out.read_bytes()==pdf;report['pdf08ByteComparisons']+=1
# Rejected changes must leave both persisted draft and rendered values unchanged.
for rows,kwargs in [([(0,'1')],{}),([(1,'-1')],{}),([(1,'1.001')],{}),([(1,'1e2')],{}),([(1,'42949672.96')],{}),([(2,'42949672.95')],{}),([(1,'1')],{'currency':'<x>'}),([(1,'1')],{'tax':10001}),([(1,'1')],{'extra':{'path':'/tmp/nope'}}),([(1,'1')],{'extra':{'pBAD':'1'}}),([(1,'1')],{'extra':{'q00':'1'}})]:
 code,_,_=edit(rows,**kwargs);assert code==409;assert doc()==saved;assert '30.73'in page();report['refusals']+=1
# Stale form and download selectors cannot silently read or overwrite a newer draft.
edit([(1,'1.00')]);new=doc();assert edit([(9,'9')],text=before)[0]==409 and doc()==new;report['refusals']+=1;assert download('pdf',before)[0]==403;report['refusals']+=1
# Idle preconnect sockets must not block an actual request or receive a spurious error.
idle=[socket.create_connection(('127.0.0.1',port))for _ in range(8)];t=time.perf_counter();assert request('GET','/')[0]==200;assert time.perf_counter()-t<2;report['idleConcurrencyCases']+=1
for s in idle:s.close()
def raw(payload):
 s=socket.create_connection(('127.0.0.1',port));s.settimeout(10);s.sendall(payload);out=b''
 try:
  while True:
   b=s.recv(65536)
   if not b:break
   out+=b
 except ConnectionResetError:pass
 s.close();return int(out.split(b' ',2)[1])if out else 0
base=f'POST /edit HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nOrigin: {url}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 0\r\n'
for text in [base.replace('Host:','Host: evil.invalid\r\nOther:'),base.replace(url,'http://evil.invalid'),base.replace('Origin: '+url+'\r\n',''),base+'Content-Length: 0\r\n',base+'Host: 127.0.0.1:'+str(port)+'\r\n',base+'Transfer-Encoding: chunked\r\n',base+'Expect: 100-continue\r\n',base.replace('Content-Length: 0','Content-Length: 524289'),base.replace('HTTP/1.1','HTTP/1.0')]:assert raw((text+'\r\n').encode())==400;report['refusals']+=1
assert request('GET','/unknown')[0]==404;report['refusals']+=1
f=fields(page());f.update(rows=1,currency='MYR',tax=600,q0=1,p0='1.00',action='apply');body=urllib.parse.urlencode(f)+'&%74oken='+f['token'];assert request('POST','/edit',body,{'Origin':url,'Content-Type':'application/x-www-form-urlencoded'})[0]==409;report['refusals']+=1
f=fields(page());f['token']='0'*32;assert request('POST','/quit',urllib.parse.urlencode(f),{'Origin':url,'Content-Type':'application/x-www-form-urlencoded'})[0]==403;report['refusals']+=1
# Escaped-key and nonce mutations must never acquire document authority.
import random
rng=random.Random(2026111209)
for _ in range(100):
 f=fields(page());at=rng.randrange(32);nonce=list(f['token']);nonce[at]=next(c for c in '0123456789abcdef'if c!=nonce[at]);f.update(token=''.join(nonce),rows=0,currency='MYR',tax=0,action='apply');snapshot=doc();assert request('POST','/edit',urllib.parse.urlencode(f),{'Origin':url,'Content-Type':'application/x-www-form-urlencoded'})[0]==409 and doc()==snapshot;report['refusals']+=1
# Real multipart upload, bounded validation and canonical re-save.
def upload(document,duplicate=False):
 f=fields(page());boundary='RF2TestBoundary2026';parts=[]
 for key,val in [*f.items(),('document',document)]+([('document',document)]if duplicate else[]):parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{val}\r\n')
 payload=(''.join(parts)+f'--{boundary}--\r\n').encode();return request('POST','/open',payload,{'Origin':url,'Content-Type':'multipart/form-data; boundary='+boundary})
for cut in range(3,23):
 f=fields(page());boundary='RF2TruncationBoundary';parts=[]
 for key,val in [*f.items(),('document',json.dumps(saved))]:parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{val}\r\n')
 payload=(''.join(parts)+f'--{boundary}--\r\n').encode()[:-cut];snapshot=doc();assert request('POST','/open',payload,{'Origin':url,'Content-Type':'multipart/form-data; boundary='+boundary})[0]==409 and doc()==snapshot;report['refusals']+=1
assert upload(json.dumps(saved))[0]==303 and doc()==saved;report['uploadCases']+=1
for payload in ['null','{"format":"wrong"}',json.dumps(dict(saved,totalCents=1))]:assert upload(payload)[0]==409 and doc()==saved;report['refusals']+=1
assert upload(json.dumps(saved),True)[0]==409 and doc()==saved;report['refusals']+=1
large=dict(saved,lines=[{'quantity':1,'unit_cents':100}for _ in range(1000)]);assert upload(json.dumps(large))[0]==303 and doc()==large;report['uploadCases']+=1
assert edit([(1,'1')]*1000,action='add')[0]==409 and doc()==large;report['refusals']+=1
assert edit([(1,'1')]*1000,action='remove:999')[0]==303 and len(doc()['lines'])==999;report['successfulEdits']+=1
old=doc();assert edit([(1,'1')]*999,action='new')[0]==303 and doc()==old;assert edit([(1,'1')]*999,action='reset')[0]==303 and doc()['lines']==[];report['successfulEdits']+=1
f=fields(page());assert request('POST','/quit',urllib.parse.urlencode(f),{'Origin':url,'Content-Type':'application/x-www-form-urlencoded'})[0]==200;p.wait(timeout=5);assert p.returncode==0 and not p.stderr.read();report.update(passed=True,cleanupVerified=True,runtimeSHA256=hashlib.sha256(B.read_bytes()).hexdigest(),baseline08SHA256=hashlib.sha256(OLD.read_bytes()).hexdigest());(R/'docs/EDITOR-0.9-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
