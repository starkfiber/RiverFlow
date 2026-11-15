"""Native HTTP application checks, including refused requests and IDE parity."""
from pathlib import Path
import http.client,json,os,re,select,subprocess,tempfile,urllib.parse
ROOT=Path(__file__).resolve().parents[2]; HOME=Path(os.environ['RF2_TEST_HOME']).resolve()
OUT=Path(tempfile.mkdtemp(prefix='workbench-http-',dir=ROOT/'artifacts'));rows=[]
def check(name,ok):
 rows.append(dict(name=name,passed=bool(ok)));(OUT/'results.json').write_text(json.dumps(rows,indent=2));assert ok,name
procs=[]
def build(entry):
 dest=OUT/entry
 p=subprocess.run(['sh',str(ROOT/'tools/build-program.sh'),str(HOME/'rf2c'),str(ROOT/'examples/documents'/f'{entry}.flow'),str(dest),'--opt'],capture_output=True)
 check('build '+entry,p.returncode==0);return dest/'program'
def start(exe,*args):
 p=subprocess.Popen(list(map(str,[exe,*args])),stdout=subprocess.PIPE,stderr=subprocess.PIPE);procs.append(p)
 assert select.select([p.stdout],[],[],5)[0]
 url=p.stdout.readline().decode().strip();check('loopback URL',url.startswith('http://127.0.0.1:'))
 return urllib.parse.urlsplit(url)
def req(url,method='GET',body=None,headers=None):
 c=http.client.HTTPConnection(url.hostname,url.port,timeout=15)
 h={'Host':url.netloc}
 if method=='POST':h.update({'Origin':'http://'+url.netloc,'Content-Type':'application/x-www-form-urlencoded'})
 if headers:h.update(headers)
 c.request(method,'/action' if method=='POST' else '/',body,h)
 try:
  r=c.getresponse();data=r.read().decode();return r.status,data
 except (ConnectionResetError,http.client.IncompleteRead,http.client.RemoteDisconnected):
  return 599,'Transport refused or closed before complete response'
 finally:c.close()
def form(page,**fields):
 pairs=dict(re.findall(r'name=(token|rev) value="?([^" >]+)',page));assert len(pairs)==2,page[:1000]
 pairs.update(fields);return urllib.parse.urlencode(pairs)
try:
 cli=build('booking');db=OUT/'test.db';subprocess.run([cli,'init',db],check=True,capture_output=True)
 url=start(build('booking-web'),db);status,page=req(url);check('booking GET',status==200)
 data=form(page,action='reserve',date='2027-01-01',start='09:00',end='10:00',name='Test Student')
 before=db.read_bytes()
 for name,body,headers in [('origin',data,{'Origin':'http://evil.invalid'}),('token',data.replace('token=','token=bad'),{}),('duplicate',data+'&name=Other',{}),('unknown',data+'&extra=x',{})]:
  status,_=req(url,'POST',body,headers);check('reject '+name,status>=400 and before==db.read_bytes())
 status,page=req(url,'POST',data);check('save GUI',status==200 and 'Last action saved' in page)
 before=db.read_bytes();status,_=req(url,'POST',data);check('stale form',before==db.read_bytes())
 status,page=req(url);status,page=req(url,'POST',form(page,action='cancel',id='1'));check('cancel GUI',status==200 and '0 active' in page)
 project=OUT/'Learning Project';project.mkdir(mode=0o700)
 url=start(build('studio'),project,HOME,ROOT);status,page=req(url);check('studio GET',status==200)
 data=form(page,action='run',source='rf2 v1 checked\nsquares input\n',data='[1,2,3]')
 status,page=req(url,'POST',data);check('checked result',status==200 and '&quot;value&quot;:14' in page)
 n=len(list(project.iterdir()));status,_=req(url,'POST',data);check('IDE stale no files',len(list(project.iterdir()))==n)
 status,page=req(url);status,page=req(url,'POST',form(page,action='native',source='rf2 v1 checked\nsquares input\n',data='[1,2,3]'))
 check('native parity',status==200 and '&quot;value&quot;:14' in page and 'Step completed' in page)
 native_before=set(project.glob('*-build'))
 status,page=req(url);status,page=req(url,'POST',form(page,action='native',source='profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return 0\nend\n',data='[]'))
 check('systems rejected',status==200 and 'tool refused' in page)
 check('systems not built',set(project.glob('*-build'))==native_before)
finally:
 for p in procs:
  if p.poll() is None:p.terminate()
  p.communicate(timeout=5)
(OUT/'report.json').write_text(json.dumps({'checks':rows,'scope':'HTTP controller and separate native application processes; no browser automation, network service qualification or OS sandbox claim'},indent=2))
print(json.dumps({'passed':len(rows),'report':str(OUT/'report.json')}))
