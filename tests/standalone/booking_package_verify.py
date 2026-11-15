"""Fresh extraction, manifest verification and native source rebuild of the exact Booking archive."""
from pathlib import Path,PurePosixPath
import hashlib,http.client,json,os,shutil,subprocess,sys,tarfile,tempfile,urllib.parse
R=Path(__file__).resolve().parents[2];archive=Path(sys.argv[1]).resolve();D=Path(tempfile.mkdtemp(prefix='booking-package-',dir=R/'artifacts'));checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,v,detail=None):
 checks.append(dict(name=name,passed=bool(v),detail=detail))
 if not v:(D/'FAILED.json').write_text(json.dumps(checks,indent=2)+'\n');raise AssertionError((name,detail))
def run(args,data=None):return subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=30,env={'PATH':'/nonexistent'})
with tarfile.open(archive)as f:
 members=f.getmembers();check('bounded archive size',sum(x.size for x in members)<64000000)
 for x in members:
  name=PurePosixPath(x.name);check('safe regular archive entry',not name.is_absolute()and'..'not in name.parts and(x.isfile()or x.isdir()))
  p=D/x.name
  if x.isdir():p.mkdir(parents=True,exist_ok=True)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(f.extractfile(x).read());p.chmod(x.mode&0o777)
P=D/archive.name.removesuffix('.tar.gz');manifest=json.loads((P/'MANIFEST.json').read_text());check('manifest has exact file set',{str(p.relative_to(P))for p in P.rglob('*')if p.is_file()}==set(manifest['files'])|{'MANIFEST.json'})
for path,info in manifest['files'].items():check('manifest identity '+path,sha(P/path)==info['sha256']and(P/path).stat().st_size==info['bytes'])
for name in('rf2','rf2c','booking','booking-web','booking-agent'):
 q=subprocess.run(['/usr/bin/codesign','--verify',str(P/name)],capture_output=True);check('extracted signature '+name,q.returncode==0)
q=run([P/'rf2','status']);check('unchanged runtime executes without search path',q.returncode==0 and json.loads(q.stdout)['version']=='0.17.0')
(D/'compiler-rebuild').mkdir();rebuilt_compiler=D/'compiler-rebuild/program'
q=run([P/'rf2c',P/'source/compiler.flow',rebuilt_compiler,'--opt']);check('native compiler rebuild',q.returncode==0,q.stderr.decode());subprocess.run(['/usr/bin/codesign','-s','-',str(rebuilt_compiler)],check=True,capture_output=True);check('native compiler source self-reproduces exact signed image',sha(rebuilt_compiler)==sha(P/'rf2c'))
for entry,name in [('main','booking'),('web','booking-web'),('agent','booking-agent')]:
 q=run([rebuilt_compiler,P/f'source/booking/{entry}.flow',D/name,'--opt']);check('native app rebuild '+name,q.returncode==0,q.stderr.decode());subprocess.run(['/usr/bin/codesign','-s','-',str(D/name)],check=True,capture_output=True);check('application exact signed image '+name,sha(D/name)==sha(P/name))
db=D/'new.db';q=run([P/'booking',db,'init']);check('extracted CLI creates actual file',q.returncode==0 and json.loads(q.stdout)==dict(revision=1,version=2,bookings=[]))
q=run([P/'booking',db,'add',1,1,1,739938,540,600]);check('extracted app persists typed row',q.returncode==0 and json.loads(q.stdout)['revision']==2)
q=run([D/'booking',db,'list']);check('rebuilt app reads same durable data',q.returncode==0 and json.loads(q.stdout)['bookings']==[dict(id='1',room=1,day=739938,start=540,finish=600)])
server=subprocess.Popen([str(P/'booking-web'),str(db)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/nonexistent'})
try:
 url=server.stdout.readline().decode().strip();host=urllib.parse.urlsplit(url);c=http.client.HTTPConnection(host.hostname,host.port,timeout=5);c.request('GET','/');r=c.getresponse();body=r.read();check('extracted native GUI serves actual saved data',r.status==200 and b'2026-11-18'in body and b'Reservation #1'in body and b'aria-current=page'in body);c.close()
finally:server.terminate();server.communicate(timeout=5)
meta={'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{}};request=dict(jsonrpc='2.0',id=1,method='tools/call',params=dict(_meta=meta,name='booking_list',arguments={}));q=run([P/'booking-agent',db],json.dumps(request).encode()+b'\n');result=json.loads(q.stdout)['result']['structuredContent'];check('extracted agent shares actual snapshot',q.returncode==0 and result['revision']==2 and result['snapshot_sha256']==db.read_bytes()[-40:-8].hex())
(D/'report.json').write_text(json.dumps(dict(checks=len(checks),archiveSHA256=sha(archive),files=manifest['files'],results=checks),indent=2)+'\n');print(json.dumps(dict(checks=len(checks),report=str(D/'report.json'))))
