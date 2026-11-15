"""Native SDK protocol and explicit policy qualification; bounded local fixtures."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TRY_COMPILER']).resolve();D=Path(tempfile.mkdtemp(prefix='app-effort-check-',dir=R/'artifacts'));checks=[]
sys.path.insert(0,str(R/'experiments/app-effort'));from stage import stage
stage(D/'lib')
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:(D/'FAILED.json').write_text(json.dumps(checks,indent=2));raise AssertionError((name,detail))
def build(name,source,opt):
 p=D/(name+str(opt)+'.flow');p.write_text(source);exe=p.with_suffix('');q=subprocess.run([str(C),str(p),str(exe),'--compact',*(['--opt']if opt else[])],capture_output=True,timeout=30);check(name+' compile '+str(opt),q.returncode==0,(q.stdout+q.stderr).decode());subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],check=True,capture_output=True);return exe
def request(method,id=2,params=None):
 d=dict(jsonrpc='2.0',id=id,method=method)
 if params is not None:d['params']=params
 return d
init=request('initialize',1,dict(protocolVersion='2025-11-25',capabilities={},clientInfo=dict(name='independent',version='1')))
notice=dict(jsonrpc='2.0',method='notifications/initialized')
call=request('tools/call',2,dict(name='status_read',arguments={}))
header='profile RF2_SYSTEM_A64_V1\nuse "lib/mcp.flow"\n'
callback='''fn mcp_execute(out:Writer):IO
 let count=buffer("callback_counter",8)
 do store64(count,load64(count)+1)
 do writer_text(out,"{\\"calls\\":")
 do writer_number(out,load64(count))
 do writer_text(out,"}")
 return ok(out.used)
end
'''
entry='''fn main(argc,argv)
 handle mcp_serve("native-status","0.47-candidate","status_read","Read one local status object")
 ok complete
  return 0
 err failure
  return 2
 end
 return 3
end
'''
def wire(exe,items):
 data=b''.join((json.dumps(x).encode()if not isinstance(x,bytes)else x)+b'\n'for x in items)
 q=subprocess.run([str(exe)],input=data,capture_output=True,timeout=10);check('wire clean exit',q.returncode==0,[q.returncode,q.stderr.decode(errors='replace')]);return[json.loads(x)for x in q.stdout.splitlines()]
for opt in(False,True):
 exe=build('status',header+callback+entry,opt)
 rows=wire(exe,[init,notice,request('tools/list'),call]);check('one tool',len(rows[1]['result']['tools'])==1 and rows[1]['result']['tools'][0]['name']=='status_read');check('callback',rows[2]['result']['structuredContent']==dict(calls=1))
 invalids=[(b'{',32700),(b'{"jsonrpc":"2.0","id":4,"method":"ping","\\u006dethod":"ping"}',32700),(request('tools/call',2,dict(name='nope',arguments={})),32602),(request('tools/call',2,dict(name='status_read',arguments=dict(path='/tmp/forbidden'))),32602),(request('tools/call',2,dict(name='status_read')),32602),(request('tools/call',2,dict(name='status_read',arguments={},extra=1)),32602),(request('missing'),32601),(request('tools/list',2,dict(cursor='bad')),32602),(b' '*65537,32700),(b'"\xff"',32700),(request('ping',None),32600),(request('ping',[]),32600),(request('ping',1.5),32600),(request('ping','x'*257),32600)]
 for item,code in invalids:
  rows=wire(exe,[init,notice,item,dict(jsonrpc='2.0',method='tools/call',params=dict(name='status_read',arguments={})),call]);check('reject '+str(code)+' '+str(opt),rows[-2]['error']['code']==-code,rows);check('recovery and notification denied',rows[-1]['result']['structuredContent']==dict(calls=1),rows)
 for id in ['x"\\தமிழ்',-123,18446744073709551615]+[chr(i)for i in range(32)]:
  rows=wire(exe,[init,notice,request('tools/call',id,dict(name='status_read',arguments={}))]);check('stable id after callback parse',rows[-1]['id']==id,rows[-1])
 rows=wire(exe,[call,init,notice,call]);check('handshake refused then recovers','error'in rows[0]and rows[-1]['result']['structuredContent']==dict(calls=1))
 payload=json.dumps(json.dumps(dict(text='spaces and \"quotes\" stay',nested=[1,2]),indent=2)+'\n')
 pretty=build('pretty-output',header+'fn mcp_execute(out:Writer):IO\n do writer_text(out,'+payload+')\n return ok(out.used)\nend\n'+entry,opt)
 rows=wire(pretty,[init,notice,call]);check('compact pretty callback to one line',rows[-1]['result']['structuredContent']==dict(text='spaces and "quotes" stay',nested=[1,2]),rows)
 rows=wire(exe,[init,dict(jsonrpc='2.0',method='notifications/initialized',params=[]),call,notice,call]);check('invalid readiness does not authorize callback','error'in rows[-2]and rows[-1]['result']['structuredContent']==dict(calls=1),rows)
 for name,body in [('callback-error','return err(73)'),('invalid-output','do writer_text(out,"[]")\n return ok(0)'),('overflow','set out.error=28\n return ok(0)'),('invalid-used','set out.used=65537\n return ok(0)')]:
  other=build(name,header+'fn mcp_execute(out:Writer):IO\n '+body+'\nend\n'+entry,opt);rows=wire(other,[init,notice,call,request('ping',3)]);check(name+' tool failure',rows[-2]['result']['isError']is True and rows[-1]['result']=={},rows)
 # Policy changes are explicit, bounded and immutable after attempted use.
 source='''profile RF2_SYSTEM_A64_V1
use "lib/store.flow"
use "lib/app-server.flow"
use "lib/ui.flow"
fn app_dispatch(fd):IO
 return ok(app_bad(fd,"400 Bad Request"))
end
fn work():IO
 if store_limit()!=1048576
  return err(80)
 end
 do try store_configure(4194304)
 if store_limit()!=4194304
  return err(81)
 end
 handle store_configure(16777217)
 ok bad
  return err(82)
 err invalid
  if invalid!=22
   return err(83)
  end
 end
 let state=StoreState(0,0,0,0,0,0,0)
 handle store_view("/no-such-rf2-test-file",state)
 ok own rows:Bookings
  return err(84)
 err absent
 end
 handle store_configure(1048576)
 ok changed
  return err(85)
 err frozen
  if frozen!=16
   return err(86)
  end
 end
 if app_more(4095)==0
  return err(87)
 end
 if app_more(4096)
  return err(88)
 end
 do try app_request_budget(0)
 if app_more(1000000000)==0
  return err(89)
 end
 do try app_request_budget(3)
 if (app_more(2)==0)|app_more(3)
  return err(90)
 end
 return ok(0)
end
fn main(argc,argv)
 handle work()
 ok passed
  return 0
 err failure
  return failure
 end
 return 201
end
'''
 exe=build('policies',source,opt);q=subprocess.run([str(exe)],capture_output=True);check('policy execution '+str(opt),q.returncode==0,[q.returncode,q.stderr.decode()])
receipt=dict(schema='rf2.app-effort-sdk-checks.v1',compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),checks=len(checks),passed=sum(x['passed']for x in checks),results=checks,scope='Native Mac ARM64; strict legacy single-tool subset; local controlled fixtures, no workplace/user trial.')
(D/'RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(D),checks=receipt['checks'],passed=receipt['passed'])))
