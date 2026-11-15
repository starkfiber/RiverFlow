"""Real configured journal capacity/reopen and HTTP request lifetime policies."""
from pathlib import Path
import hashlib,http.client,json,os,subprocess,sys,tempfile,urllib.parse
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TRY_COMPILER']).resolve();D=Path(tempfile.mkdtemp(prefix='app-policy-',dir=R/'artifacts'));sys.path.insert(0,str(R/'experiments/app-effort'));from stage import stage
stage(D/'lib');checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:(D/'FAILED.json').write_text(json.dumps(checks,indent=2));raise AssertionError((name,detail))
def build(name,source,opt):
 p=D/(name+str(opt)+'.flow');p.write_text(source);exe=p.with_suffix('');q=subprocess.run([str(C),str(p),str(exe),'--compact',*(['--opt']if opt else[])],capture_output=True,timeout=30);check(name+' compile',q.returncode==0,(q.stdout+q.stderr).decode());subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],check=True,capture_output=True);return exe
source='''profile RF2_SYSTEM_A64_V1
use "lib/store.flow"
fn work(path,creating):IO
 do try store_configure(4194304)
 let request=StoreRequest(1,0,0,1,1,0,1)
 let out=Writer(buffer("test_output",65536),65536,0,0)
 if creating
  do try store_operation(path,request,out)
  let i=1
  while i<=256
   set request.action=2
   set request.expected=i
   set request.id=i
   set request.start=i*3
   set request.finish=i*3+1
   do try store_operation(path,request,out)
   set i=i+1
  end
  set request.expected=257
  set request.id=257
  set request.start=1000
  set request.finish=1001
  handle store_operation(path,request,out)
  ok overflowed
   return err(71)
  err capacity
   if capacity!=27
    return err(72)
   end
  end
 end
 set request.action=0
 do try store_operation(path,request,out)
 do try io_write_all(1,out.data,out.used)
 return ok(0)
end
fn main(argc,argv)
 handle work(load64(argv+8),argc>2)
 ok complete
  return 0
 err cause
  return cause
 end
 return 201
end
'''
HTTP_SOURCE='''profile RF2_SYSTEM_A64_V1
use "lib/app-server.flow"
use "lib/ui.flow"
fn app_dispatch(fd):IO
 let out=Writer(buffer("policy_html",64),64,0,0)
 do writer_text(out,"<p>ready</p>")
 return ok(ui_response(fd,out,"200 OK"))
end
fn main(argc,argv)
 handle form_session()
 ok ready
 err entropy_error
  return 2
 end
 handle app_request_budget(argc-1)
 ok configured
 err policy_error
  return 3
 end
 handle app_serve()
 ok complete
  return 0
 err failure
  return 4
 end
 return 5
end
'''
for opt in(False,True):
 exe=build('capacity',source,opt);db=D/('capacity-'+str(opt)+'.db');q=subprocess.run([str(exe),str(db),'create'],capture_output=True,timeout=120);check('256 full journal operations '+str(opt),q.returncode==0,[q.returncode,q.stderr.decode()]);state=json.loads(q.stdout);check('full current state',state['revision']==257 and len(state['bookings'])==256);check('actually exceeds old cap',1048576<db.stat().st_size<4194304,db.stat().st_size);before=hashlib.sha256(db.read_bytes()).hexdigest();q=subprocess.run([str(exe),str(db)],capture_output=True,timeout=15);check('fresh process reopen',q.returncode==0 and json.loads(q.stdout)==state);check('read leaves original bytes',before==hashlib.sha256(db.read_bytes()).hexdigest())
 # Independent frame-length/hash-chain decoder; no RF2 parser used.
 data=db.read_bytes();at=0;previous=bytes(32);frames=0
 while at<len(data):
  import struct
  version,schema,revision,count,size=struct.unpack_from('<5Q',data,at+8);frame=data[at:at+120+size]
  check('independent frame '+str(opt)+' '+str(revision),frame[:8]==b'RF2BK02\n'and version==2 and len(frame)==120+size and count<=256 and size==count*40 and schema.to_bytes(8,'little')==b'BKG00002' and revision==frames+1 and count==frames and frame[48:80]==previous and frame[-8:]==b'BKCOMMIT' and hashlib.sha256(frame[:-40]).digest()==frame[-40:-8])
  actual=[struct.unpack_from('<5Q',frame,80+i*40)for i in range(count)]
  check('independent rows '+str(opt)+' '+str(revision),actual==[(i,1,1,i*3,i*3+1)for i in range(1,count+1)])
  previous=frame[-40:-8];at+=len(frame);frames+=1
 check('257 committed frames',frames==257 and at==len(data))
 web=build('http',HTTP_SOURCE,opt)
 for args,count,should_stop in [(['x']*3,3,True),([],4100,False)]:
  p=subprocess.Popen([str(web),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   url=p.stdout.readline().strip();port=urllib.parse.urlparse(url).port;check('loopback URL',url.startswith('http://127.0.0.1:')and bool(port),url)
   for i in range(count):
    c=http.client.HTTPConnection('127.0.0.1',port,timeout=3);c.request('GET','/');r=c.getresponse();body=r.read();c.close();check('HTTP '+str(opt)+' '+str(should_stop)+' '+str(i),r.status==200 and b'ready'in body,dict(status=r.status,body=body[:160].decode(errors='replace')))
   if should_stop:check('exact finite policy exits',p.wait(timeout=5)==0)
   else:check('unlimited survives4096',p.poll()is None)
  finally:
   if p.poll()is None:p.terminate()
   p.wait(timeout=5)
receipt=dict(checks=len(checks),passed=sum(x['passed']for x in checks),results=checks,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),scope='Native configured fixtures,4100 private-loopback requests per mode; no public-server/load or real-customer claim.')
(D/'RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(D),checks=len(checks),passed=receipt['passed'])))
