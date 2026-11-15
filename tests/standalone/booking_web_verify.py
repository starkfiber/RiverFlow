"""Native Booking HTTP/UI behavior against real shared storage; browser checks are separate."""
from pathlib import Path
import datetime,hashlib,html.parser,http.client,json,os,shutil,struct,subprocess,tempfile,urllib.parse
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_STORE_COMPILER']).resolve();D=Path(tempfile.mkdtemp(prefix='booking-web-',dir=R/'artifacts'));CHECKS=[]
def check(name,passed,detail=None):
 CHECKS.append(dict(name=name,passed=bool(passed),detail=detail))
 if not passed:(D/'FAILED.json').write_text(json.dumps(CHECKS,indent=2)+'\n');raise AssertionError((name,detail))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(name,opt,entry):
 root=D/name;(root/'lib').mkdir(parents=True)
 for p in(R/'experiments/typed-booking/lib').iterdir():shutil.copy2(p,root/'lib'/p.name)
 for p in('io.flow','storage.flow','text.flow','datetime.flow'):shutil.copy2(R/'examples/documents/lib'/p,root/'lib'/p)
 shutil.copy2(R/'examples/evidence-contract/lib/sha256.rf2',root/'lib/sha256.rf2');shutil.copy2(R/'examples/collection-tools/lib/output.rf2',root/'lib/output.rf2');shutil.copy2(R/'experiments/typed-booking'/entry,root/entry)
 exe=root/'program';q=subprocess.run(list(map(str,[C,root/entry,exe,*(['--opt']if opt else[])])),capture_output=True,timeout=20);check('build '+name,q.returncode==0,(q.stdout+q.stderr).decode(errors='replace')[:600]);subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],capture_output=True,check=True);return exe
class Page(html.parser.HTMLParser):
 def __init__(self,s):
  super().__init__();self.forms=[];self.current=None;self.images=0;self.controls=[];self.feed(s)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='form':self.current={};self.forms.append(self.current)
  if tag=='input'and self.current is not None and'name'in a:self.current[a['name']]=a.get('value','')
  if tag=='img':self.images+=1
  if tag in('input','select','button'):self.controls.append(a)
 def handle_endtag(self,tag):
  if tag=='form':self.current=None
 def form(self,action,id=None):
  return next(f.copy()for f in self.forms if f.get('action')==action and(id is None or f.get('id')==str(id)))
class Server:
 def __init__(self,exe,db):
  self.p=subprocess.Popen([str(exe),str(db)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/nonexistent'});self.url=self.p.stdout.readline().decode().strip();check('server loopback URL',self.url.startswith('http://127.0.0.1:'),self.url);self.port=urllib.parse.urlsplit(self.url).port
 def request(self,method='GET',path='/',form=None,headers=None,body=None):
  if form is not None:body=urllib.parse.urlencode(form)
  h={'Host':f'127.0.0.1:{self.port}'}
  if method=='POST':h.update({'Origin':self.url.rstrip('/'),'Content-Type':'application/x-www-form-urlencoded'})
  h.update(headers or{});c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5);c.request(method,path,body=body,headers=h);r=c.getresponse();result=(r.status,dict(r.getheaders()),r.read().decode());c.close();return result
 def close(self):
  self.p.terminate();self.p.communicate(timeout=5)
def cli(exe,db,*args):
 q=subprocess.run(list(map(str,[exe,db,*args])),capture_output=True,timeout=10);check('CLI shared state operation',q.returncode==0,q.stderr.decode());return json.loads(q.stdout)

for opt in(False,True):
 exe=build('web-'+str(opt),opt,'web.flow');command=build('cli-'+str(opt),opt,'main.flow');db=D/f'workspace-{opt}.db';s=Server(exe,db)
 try:
  code,headers,page=s.request();check('first-run create action',code==200 and'Create booking workspace'in page and not db.exists());init=Page(page).form('initialize')
  check('no external scripts',not any(v in page for v in('<script','https://fonts','cdn.')))
  check('CSP and response protection',"default-src 'none'"in headers['Content-Security-Policy']and"frame-ancestors 'none'"in headers['Content-Security-Policy']and headers['X-Content-Type-Options']=='nosniff'and headers['Cache-Control']=='no-store')
  for h in({'Host':'evil.example'},{'Origin':'https://evil.example'}):
   code,_,_=s.request('POST','/action',init,headers=h);check('foreign host/origin rejected',code==400 and not db.exists())
  # More than the initial header read leaves unread body bytes on rejection.
  # The complete error response must survive closing, and the next request works.
  for attempt in range(40):
   code,_,body=s.request('POST','/action',body='x'*32768,headers={'Host':'evil.example'});check('rejected large body complete response '+str(attempt),code==400 and bool(body)and not db.exists())
  code,_,page=s.request();check('server recovers after unread-body refusals',code==200 and'Create booking workspace'in page and not db.exists())
  wrong=init.copy();wrong['token']='0'*32;code,_,_=s.request('POST','/action',wrong);check('wrong token refused',code==403 and not db.exists())
  code,_,page=s.request('POST','/action',init);check('native GUI creates workspace',code==200 and db.is_file()and'Saved to your workspace'in page)
  check('bookings navigation selected','href=/ aria-current=page'in page);parsed=Page(page);theme=parsed.form('appearance');theme['appearance']='light';before=digest(db);code,h,page=s.request('POST','/action',theme);cookie=h.get('Set-Cookie','');check('appearance only sets bounded preference',code==200 and'class="light"'in page and'rf2_booking_theme=light;'in cookie and'HttpOnly'in cookie and'SameSite=Strict'in cookie and digest(db)==before)
  code,_,page=s.request(headers={'Cookie':'rf2_booking_theme=light'});check('light preference survives next request','class="light"'in page and'value="light" selected'in page)
  reserve=Page(page).form('reserve');reserve.update(room=1,date='2028-02-29',start='00:00',end='24:00');code,_,page=s.request('POST','/action',reserve);check('GUI date/time stores full-day leap-date booking',code==200 and'2028-02-29'in page and'00:00'in page and'24:00'in page);state=cli(command,db,'list');check('same typed CLI state',state['bookings']==[dict(id='1',room=1,day=datetime.date(2028,2,29).toordinal(),start=0,finish=1440)])
  before=digest(db);stale=reserve.copy();stale['id']='2';code,_,page=s.request('POST','/action',stale);check('stale browser form no duplicate',code==200 and'This booking could not be saved'in page and digest(db)==before)
  reserve=Page(page).form('reserve');reserve.update(room=1,date='2028-02-29',start='12:00',end='13:00');before=digest(db);code,_,page=s.request('POST','/action',reserve);check('overlap warning and exact preserved input',code==200 and'This booking could not be saved'in page and'value="2028-02-29"'in page and'value="12:00"'in page and'value="13:00"'in page and digest(db)==before)
  reserve=Page(page).form('reserve');reserve.update(room=2,date='2028-02-29',start='12:00',end='13:00');code,_,page=s.request('POST','/action',reserve);check('separate room accepted',code==200 and'2 saved'in page and'Room 2'in page)
  reserve=Page(page).form('reserve');reserve.update(room=2,date='2028-02-28',start='12:00',end='13:00');code,_,page=s.request('POST','/action',reserve);check('rows ordered by actual date',page.index('2028-02-28')<page.index('2028-02-29'))
  # Unknown fields, malformed escapes and repeated fields never reach storage.
  reserve=Page(page).form('reserve');reserve.update(room=3,date='2028-02-29',start='12:00',end='13:00');body=urllib.parse.urlencode(reserve);before=digest(db)
  for suffix in('&path=/tmp/other.db','&token=duplicate','&unknown=x','&room=4'):
   code,_,_=s.request('POST','/action',body=body+suffix);check('strict field admission',code==400 and digest(db)==before)
  for bad in('token=%','token=%00','token=%zz'):
   code,_,_=s.request('POST','/action',body=bad);check('malformed encoded form refused',code in(400,403)and digest(db)==before)
  code,_,_=s.request(path='/../other');check('unrecognized route refused',code==404)
  code,_,page=s.request(path='/storage');check('storage view has real verified revision','Storage format'in page and'Verified file bytes'in page and'Saved revision'in page)
  check('storage navigation and page title correct','<title>Storage | RF2 Booking</title>'in page and'href=/storage aria-current=page'in page and'id=booking-form'not in page)
  # U64 identifiers cross CLI/browser unchanged, without a JavaScript number conversion.
  state=cli(command,db,'list');cli(command,db,'add',state['revision'],2**64-1,3,datetime.date(2028,3,1).toordinal(),0,1);code,_,page=s.request();cancel=Page(page).form('cancel',2**64-1);check('full u64 ID rendered intact',cancel['id']==str(2**64-1));code,_,page=s.request('POST','/action',cancel);check('browser cancels exact u64 ID',code==200 and str(2**64-1)not in page)
  # Duplicate transport metadata refuses before action execution.
  before=digest(db);c=http.client.HTTPConnection('127.0.0.1',s.port,timeout=5);c.putrequest('GET','/',skip_host=True);c.putheader('Host',f'127.0.0.1:{s.port}');c.putheader('Cookie','rf2_booking_theme=light');c.putheader('Cookie','rf2_booking_theme=dark');c.endheaders();r=c.getresponse();r.read();check('duplicate appearance cookie rejected',r.status==400 and digest(db)==before);c.close()
 finally:s.close()
 # Upgrade compatibility data through the same real GUI and persistence functions.
 db=D/f'upgrade-{opt}.db';cli(command,db,'init-v1');cli(command,db,'add',1,7,1,datetime.date(2026,11,18).toordinal(),540,600);s=Server(exe,db)
 try:
  _,_,page=s.request(path='/storage');check('GUI explains compatibility upgrade','Enable multiple rooms'in page);form=Page(page).form('migrate');code,_,page=s.request('POST','/action',form);state=cli(command,db,'list');check('GUI migration preserves booking',code==200 and state['version']==2 and state['bookings']==[dict(id='7',room=1,day=datetime.date(2026,11,18).toordinal(),start=540,finish=600)])
 finally:s.close()
 # Deliberately incomplete bytes are a test fixture, never labelled a power-loss trial.
 db=D/f'recover-{opt}.db';cli(command,db,'init');before=db.read_bytes();db.write_bytes(before+b'RF2BK02\\n'[:7]);s=Server(exe,db)
 try:
  _,_,page=s.request();check('interrupted save has explicit recovery action','An interrupted save needs attention'in page);form=Page(page).form('recover');code,_,page=s.request('POST','/action',form);check('GUI recovery preserves verified prefix',code==200 and db.read_bytes()==before and'Saved to your workspace'in page)
 finally:s.close()
 # User-selected file names are text, not markup.
 db=D/f'escaped-<img src=x onerror=bad>-{opt}.db';cli(command,db,'init');s=Server(exe,db)
 try:
  _,_,page=s.request(path='/storage');check('workspace path is HTML escaped','&lt;img'in page and Page(page).images==0)
 finally:s.close()
 print('Booking GUI protocol mode',opt,'passed',flush=True)

(D/'report.json').write_text(json.dumps(dict(checks=len(CHECKS),compilerSHA256=digest(C),results=CHECKS),indent=2)+'\n');print(json.dumps(dict(checks=len(CHECKS),report=str(D/'report.json'))))
