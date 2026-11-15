"""Frozen black-box acceptance grader; never edits an attempt's implementation."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,html.parser,http.client,json,os,re,select,subprocess,sys,tempfile,urllib.parse
W=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve();results=[]
def check(name,ok,detail=None):results.append(dict(name=name,passed=bool(ok),detail=detail))
def finish():
 OUT.write_text(json.dumps(dict(checks=len(results),passed=sum(r['passed']for r in results),allPassed=bool(results)and all(r['passed']for r in results),results=results),indent=2)+'\n');print(json.dumps(dict(report=str(OUT),passed=sum(r['passed']for r in results),checks=len(results))))
try:
 launch=json.loads((W/'launch.json').read_text());assert isinstance(launch,list)and all(isinstance(s,str)for s in launch)
 assert launch==['./app']or launch==['python3','app.py'];check('valid self-contained launch contract',True)
except Exception as e:check('valid self-contained launch contract',False,str(e));finish();raise SystemExit(0)
def cli(*a):
 try:
  p=subprocess.run([*launch,*map(str,a)],cwd=W,capture_output=True,timeout=8);return p.returncode,json.loads(p.stdout),p.stderr.decode(errors='replace')[:150]
 except Exception as e:return -1,{},str(e)
def good(name,*a):
 code,result,err=cli(*a);check(name,code==0 and isinstance(result,dict)and'revision'in result and'bookings'in result,(code,result,err));return result
class Page(html.parser.HTMLParser):
 def __init__(self,raw):super().__init__();self.forms=[];self.current=None;self.labels=[];self.feed(raw)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='form':self.current=dict(action=a.get('action'),fields={});self.forms.append(self.current)
  if self.current is not None and tag=='input'and a.get('name'):self.current['fields'][a['name']]=a.get('value','')
  if tag=='label':self.labels.append(a.get('for'))
 def handle_endtag(self,tag):
  if tag=='form':self.current=None
 def form(self,kind):return next(f for f in self.forms if f['fields'].get('action')==kind)
try:
 with tempfile.TemporaryDirectory(prefix='study-rooms-grade-')as tmp:
  db=Path(tmp)/'workspace.db';state=good('exclusive new workspace','init',db);check('initial state',state.get('revision')==1 and state.get('bookings')==[])
  code,result,_=cli('init',db);check('existing path refused',code==2 and result==dict(error=17))
  state=good('first reservation','reserve',db,1,'18446744073709551615',1,'2028-02-29','09:00','10:00');row=dict(id='18446744073709551615',room=1,day=datetime.date(2028,2,29).toordinal(),start=540,finish=600);check('canonical date and exact u64 row',state.get('revision')==2 and state.get('bookings')==[row]);before=db.read_bytes()
  for name,revision,id,room,date,start,end,error in [
   ('overlap',2,'2',1,'2028-02-29','09:59','10:01',409),('stale',1,'2',2,'2028-02-29','09:00','10:00',409),('bad leap',2,'2',1,'2027-02-29','09:00','10:00',22),('noncanonical date',2,'2',1,'2028-2-29','09:00','10:00',22),('noncanonical id',2,'01',2,'2028-02-29','09:00','10:00',22),('overflow id',2,str(2**64),2,'2028-02-29','09:00','10:00',22),('invalid room',2,'2',17,'2028-02-29','09:00','10:00',22),('bad start',2,'2',2,'2028-02-29','24:00','24:00',22),('equal time',2,'2',2,'2028-02-29','10:00','10:00',22),('backwards',2,'2',2,'2028-02-29','10:00','09:00',22)]:
   code,r,_=cli('reserve',db,revision,id,room,date,start,end);check(name+' refusal',code==2 and r==dict(error=error));check(name+' preserves data',db.read_bytes()==before)
  state=good('adjacent allowed','reserve',db,2,'2',1,'2028-02-29','10:00','11:00');state=good('other room allowed','reserve',db,3,'3',2,'2028-02-29','09:00','10:00');state=good('other day and midnight allowed','reserve',db,4,'4',1,'2028-03-01','23:00','24:00');check('four real reopened reservations',len(state.get('bookings',[]))==4 and state.get('revision')==5)
  state=good('reopen in fresh process','list',db);check('first u64 remains exact',(state.get('bookings')or[{}])[0].get('id')=='18446744073709551615')
  before=db.read_bytes();code,r,_=cli('cancel',db,4,'2');check('stale cancellation refuses',code==2 and r==dict(error=409)and db.read_bytes()==before)
  state=good('exact cancellation','cancel',db,5,'2');check('cancel preserves other rows',state.get('revision')==6 and [r['id']for r in state.get('bookings',[])]==[row['id'],'3','4'])
  def contender(i):return cli('reserve',db,6,str(i+10),3,'2028-03-02','09:00','10:00')
  with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:replies=list(pool.map(contender,range(8)))
  check('simultaneous native processes have one confirmed winner',sum(code==0 for code,_,_ in replies)==1 and all(code==0 or(code==2 and r.get('error')in(35,409))for code,r,_ in replies),[(c,r.get('error'))for c,r,_ in replies]);state=good('race reopen','list',db);check('race persisted one revision',state.get('revision')==7 and len(state.get('bookings',[]))==4)
  # GUI is graded through real HTTP requests, independently from generated self-tests.
  server=None
  try:
   server=subprocess.Popen([*launch,'serve',str(db)],cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   assert select.select([server.stdout],[],[],5)[0],'No loopback URL';url=server.stdout.readline().decode().strip();u=urllib.parse.urlsplit(url);assert u.scheme=='http'and u.hostname=='127.0.0.1'and u.port
   def request_http(method='GET',form=None,headers=None,body=None):
    h={'Host':f'127.0.0.1:{u.port}'}
    if method=='POST':h.update({'Origin':url.rstrip('/'),'Content-Type':'application/x-www-form-urlencoded'})
    h.update(headers or{});c=http.client.HTTPConnection(u.hostname,u.port,timeout=5);c.request(method,'/'if method=='GET'else'/action',body=urllib.parse.urlencode(form)if form is not None else body,headers=h);r=c.getresponse();answer=(r.status,r.read().decode());c.close();return answer
   status,body=request_http();page=Page(body);form=page.form('reserve')['fields'];check('GUI actual data and semantic form',status==200 and '2028-02-29'in body and row['id']in body and len(page.labels)>=4 and len(form.get('token',''))>=32 and '<script'not in body)
   request={**form,'id':'99','room':'4','date':'2029-04-12','start':'09:00','end':'10:00'};before=db.read_bytes()
   bad=request.copy();bad['token']='0'*32;code,_=request_http('POST',bad);check('GUI wrong CSRF no effect',code in(400,403)and db.read_bytes()==before)
   code,_=request_http('POST',request,headers={'Origin':'https://evil.invalid'});check('GUI foreign origin no effect',code in(400,403)and db.read_bytes()==before)
   code,_=request_http('POST',body=urllib.parse.urlencode(request)+'&room=5');check('GUI duplicate field no effect',code in(400,403)and db.read_bytes()==before)
   code,_=request_http('POST',{**request,'path':'/tmp/not-permitted'});check('GUI unknown field no effect',code in(400,403)and db.read_bytes()==before)
   code,body=request_http('POST',request);state=good('CLI sees actual GUI commit','list',db);check('GUI uses shared transaction rules',code==200 and state.get('revision')==8 and any(r['id']=='99'and r['room']==4 for r in state.get('bookings',[])))
   before=db.read_bytes();code,body=request_http('POST',request);check('stale browser form cannot duplicate',db.read_bytes()==before and ('could not'in body.lower()or'stale'in body.lower()or'conflict'in body.lower()or'already'in body.lower()))
   reserve=Page(body).form('reserve')['fields'];bad={**reserve,'id':'100','room':'4','date':'2029-04-12','start':'09:30','end':'10:30'};code,body=request_http('POST',bad);check('failed GUI retains user input',db.read_bytes()==before and'value="2029-04-12"'in body and'value="09:30"'in body and'value="10:30"'in body)
   cancel=Page(body).form('cancel')['fields'];cancel_id=cancel['id'];code,body=request_http('POST',cancel);state=good('CLI sees GUI cancellation','list',db);check('GUI cancels only selected ID',code==200 and state.get('revision')==9 and all(r['id']!=cancel_id for r in state.get('bookings',[])))
  except Exception as e:check('GUI complete acceptance sequence',False,str(e))
  finally:
   if server is not None:
    server.terminate()
    try:server.communicate(timeout=3)
    except subprocess.TimeoutExpired:server.kill();server.communicate()
  # Legacy read-only tool discovery, denial, refusal recovery and real saved state.
  try:
   messages=[dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2025-11-25',capabilities={},clientInfo=dict(name='frozen-independent-grade',version='1'))),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list',params={}),dict(jsonrpc='2.0',id=3,method='tools/call',params=dict(name='booking_list',arguments={})),dict(jsonrpc='2.0',id=4,method='tools/call',params=dict(name='booking_list',arguments={'path':'/tmp/elsewhere'})),dict(jsonrpc='2.0',id=5,method='tools/call',params=dict(name='booking_reserve',arguments={})),dict(jsonrpc='2.0',id=6,method='ping',params={})]
   before=db.read_bytes();raw=b''.join(json.dumps(m).encode()+b'\n'for m in messages);q=subprocess.run([*launch,'mcp',str(db)],cwd=W,input=raw,capture_output=True,timeout=8);rs={r['id']:r for r in map(json.loads,q.stdout.splitlines())};check('MCP legacy actual connection',q.returncode==0 and rs[1]['result']['protocolVersion']=='2025-11-25');tools=rs[2]['result']['tools'];check('MCP exact read-only tool schema',[t['name']for t in tools]==['booking_list']and tools[0]['inputSchema'].get('additionalProperties')is False)
   check('MCP returns actual saved state',rs[3]['result']['structuredContent'].get('revision')==state.get('revision')and rs[3]['result']['structuredContent'].get('bookings')==state.get('bookings'))
   check('MCP path/write denial and recovery','error'in rs[4]and'error'in rs[5]and'result'in rs[6]and db.read_bytes()==before)
   # Duplicate keys and malformed data cannot be ignored as a different successful request.
   raw=b'{bad}\n'+b'{"jsonrpc":"2.0","id":7,"method":"ping","method":"tools/list"}\n'+b''.join(json.dumps(m).encode()+b'\n'for m in messages)
   q=subprocess.run([*launch,'mcp',str(db)],cwd=W,input=raw,capture_output=True,timeout=8);rs=list(map(json.loads,q.stdout.splitlines()));check('MCP malformed/duplicate refusal then valid recovery',q.returncode==0 and'error'in rs[0]and'error'in rs[1]and any(r.get('id')==6 and'result'in r for r in rs)and db.read_bytes()==before)
  except Exception as e:check('MCP complete acceptance sequence',False,str(e))
  check('delivery instructions present',(W/'README.md').is_file()and len((W/'README.md').read_text())>100)
except Exception as e:check('application acceptance could not continue',False,type(e).__name__+': '+str(e))
finish()
