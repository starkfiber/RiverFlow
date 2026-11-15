"""Native bounded Booking MCP: independent wire/codec tests and official legacy SDK."""
from pathlib import Path
import concurrent.futures,fcntl,hashlib,json,os,random,shutil,struct,subprocess,tempfile
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_STORE_COMPILER']).resolve();D=Path(tempfile.mkdtemp(prefix='booking-agent-',dir=R/'artifacts'));CHECKS=[]
NODE=Path('/Users/ik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,v,detail=None):
 CHECKS.append(dict(name=name,passed=bool(v),detail=detail))
 if not v:(D/'FAILED.json').write_text(json.dumps(CHECKS,indent=2)+'\n');raise AssertionError((name,detail))
def build(name,opt,entry='agent.flow',changes=()):
 root=D/name;(root/'lib').mkdir(parents=True)
 for p in(R/'experiments/typed-booking/lib').iterdir():shutil.copy2(p,root/'lib'/p.name)
 for p in('io.flow','storage.flow','text.flow','datetime.flow'):shutil.copy2(R/'examples/documents/lib'/p,root/'lib'/p)
 shutil.copy2(R/'examples/evidence-contract/lib/sha256.rf2',root/'lib/sha256.rf2');shutil.copy2(R/'examples/collection-tools/lib/output.rf2',root/'lib/output.rf2');shutil.copy2(R/'experiments/typed-booking'/entry,root/entry)
 for relative,old,new in changes:
  p=root/relative;text=p.read_text();assert text.count(old)==1;p.write_text(text.replace(old,new,1))
 exe=root/'program';q=subprocess.run([str(C),str(root/entry),str(exe),*(['--opt']if opt else[])],capture_output=True,timeout=30);check('build '+name,q.returncode==0,(q.stdout+q.stderr).decode(errors='replace')[:400]);subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],capture_output=True,check=True);return exe
META={'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{}}
def request(method='tools/call',params=None,id=1,modern=True):
 p=dict(params or{})
 if modern:p['_meta']=META.copy()
 return dict(jsonrpc='2.0',id=id,method=method,params=p)
def call(name='booking_list',args=None,id=1,modern=True):return request(params=dict(name=name,arguments=args or{}),id=id,modern=modern)
def wire(exe,db,messages,write=False):
 raw=b''.join((m if isinstance(m,bytes)else json.dumps(m,ensure_ascii=True,separators=(',',':')).encode()+b'\n')for m in messages)
 q=subprocess.run([str(exe),str(db),*(['--write']if write else[])],input=raw,capture_output=True,timeout=15,env={'PATH':'/nonexistent'});check('native wire exit and clean stderr',q.returncode==0 and not q.stderr,dict(exit=q.returncode,stderr=q.stderr.decode(errors='replace')[:200]));return[json.loads(s)for s in q.stdout.splitlines()]
def init(cli,p):
 q=subprocess.run([str(cli),str(p),'init'],capture_output=True,timeout=10);check('create selected journal',q.returncode==0,q.stderr.decode())
def error(exe,db,message,code=32602,write=True):
 before=db.read_bytes();rs=wire(exe,db,[message,call(id='next')],write);check('bounded protocol refusal',len(rs)==2 and rs[0].get('error',{}).get('code')==-code,rs[:1]);check('parser recovers next valid request',rs[-1].get('result',{}).get('structuredContent',{}).get('outcome')=='read');check('refusal preserves exact file',db.read_bytes()==before)
def receipt(r,db,rows=None,outcome='read'):
 s=r['result']['structuredContent'];raw=db.read_bytes();check('source snapshot digest matches actual bytes',s['snapshot_sha256']==raw[-40:-8].hex() and hashlib.sha256(raw[(-120-len(s['bookings'])*40): -40]).digest()==raw[-40:-8]);check('typed response outcome',s['outcome']==outcome and not r['result']['isError']);
 if rows is not None:check('typed response exact bookings',s['bookings']==rows)

for opt in(False,True):
 exe=build('agent-'+str(opt),opt);cli=build('cli-'+str(opt),opt,'main.flow');db=D/f'workspace-{opt}.db';init(cli,db)
 rs=wire(exe,db,[request('server/discover'),request('tools/list',id=2),call(id=3)]);check('modern stateless complete result',all(r['result']['resultType']=='complete' for r in rs));check('discovery current support','2026-07-28'in rs[0]['result']['supportedVersions']);check('read-only process advertises read only',[t['name']for t in rs[1]['result']['tools']]==['booking_list']);receipt(rs[2],db,[])
 before=db.read_bytes();error(exe,db,call('booking_reserve',dict(expected_revision=1,id='1',room=1,day=739938,start=540,finish=600)),write=False)
 rs=wire(exe,db,[request('tools/list')],True);tools=rs[0]['result']['tools'];check('exact fixed write tools',[t['name']for t in tools]==['booking_list','booking_reserve','booking_cancel']);check('schemas carry no path/source/network authority',all(t['inputSchema']['additionalProperties']is False and not any(k in t['inputSchema'].get('properties',{})for k in('path','source','url'))for t in tools));check('advertised schemas match reviewed manifest',tools==json.loads((R/'experiments/typed-booking/tools.json').read_text())['writeEnabled']);check('read/write flags explicit',tools[0]['annotations']['readOnlyHint']and not tools[1]['annotations']['readOnlyHint']and tools[2]['annotations']['destructiveHint'])
 a=dict(expected_revision=1,id='18446744073709551615',room=1,day=739938,start=540,finish=600);r=wire(exe,db,[call('booking_reserve',a)],True)[0];row=dict(id=a['id'],room=1,day=739938,start=540,finish=600);receipt(r,db,[row],'confirmed')
 before=db.read_bytes();r=wire(exe,db,[call('booking_reserve',a)],True)[0];check('stale write produces tool error without mutation',r['result']['isError']and r['result']['structuredContent']==dict(outcome='failed',errorCode=409)and db.read_bytes()==before)
 # Distinct rooms accept simultaneous intervals; same room conflict refuses.
 a.update(expected_revision=2,id='2');r=wire(exe,db,[call('booking_reserve',a)],True)[0];check('overlap refused by shared rules',r['result']['structuredContent'].get('errorCode')==409 and db.read_bytes()==before)
 a['room']=2;r=wire(exe,db,[call('booking_reserve',a)],True)[0];receipt(r,db,[row,dict(id='2',room=2,day=739938,start=540,finish=600)],'confirmed')
 # Invalid structural/semantic values must not alter a selected journal.
 for k,v in [('expected_revision',0),('expected_revision',2**32),('id','0'),('id','01'),('id',2),('id','18446744073709551616'),('id','-1'),('room',0),('room',17),('day',0),('day',3652060),('start',1440),('finish',0),('finish',1441),('room',1.5),('room',True),('room',None)]:
  bad={**a,k:v};error(exe,db,call('booking_reserve',bad))
 for bad in ({**a,'path':'/tmp/escape.db'}, {k:v for k,v in a.items()if k!='room'},[],None):
  m=call('booking_reserve');m['params']['arguments']=bad;error(exe,db,m)
 for name in ['execute','booking_recover','booking_migrate','booking_init','rf2_run','../booking_list','booking_list\0x','x'*4096]:error(exe,db,call(name))
 for m in [request('tools/list',dict(cursor='next')),request('tools/call',dict(name='booking_list',arguments={},path='/tmp/x')),call(args={'x'*4096:1}),request('tools/list',modern=False),request('server/discover',modern=False)]:error(exe,db,m)
 for meta in ({},{'io.modelcontextprotocol/protocolVersion':'2026-07-28'},{**META,'io.modelcontextprotocol/clientCapabilities':[]},{**META,'io.modelcontextprotocol/clientInfo':{}},{**META,'io.modelcontextprotocol/protocolVersion':'x'*65}):
  m=request('server/discover');m['params']['_meta']=meta;error(exe,db,m)
 m=request('server/discover');m['params']['_meta']={**META,'io.modelcontextprotocol/protocolVersion':'2030-01-01'};error(exe,db,m,32022)
 # No inherited modern metadata, even immediately after successful discovery.
 rs=wire(exe,db,[request('server/discover'),call(modern=False)],True);check('no metadata inheritance',rs[1]['error']['code']==-32602)
 notification=call('booking_cancel',dict(expected_revision=3,id='2'));del notification['id'];before=db.read_bytes();rs=wire(exe,db,[notification,call(id='after')],True);check('tool notification has no response or side effect',len(rs)==1 and rs[0]['id']=='after'and db.read_bytes()==before)
 # Exact request IDs include escaped strings/control characters and integer precision.
 for id in [0,-9223372036854775808,18446744073709551615,'quote" slash\\ new\n tab\t null\0','தமிழ்', 'x'*256]:
  r=wire(exe,db,[call(id=id)])[0];check('exact JSON RPC id roundtrip',r['id']==id);receipt(r,db)
 for id in [None,False,1.5,[],{},'x'*257,10**22]:error(exe,db,call(id=id),32600)
 malformed=[b'{bad}\n',b'[]\n',b'{"jsonrpc":"2.0","id":1,"method":"tools/list","method":"ping"}\n',b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{"a":1,"\\u0061":2}}\n',b'{"a":"\xff"}\n',b'{"a":"\\ud800"}\n',b'{"a":"\0"}\n',b'{"a":'+b'['*40+b'0'+b']'*40+b'}\n',b'X'*65537+b'\n']
 for m in malformed:
  code=32600 if m==b'[]\n'else 32700;error(exe,db,m,code)
 # Unterminated valid-looking write is framing failure, never a committed mutation.
 before=db.read_bytes();q=subprocess.run([str(exe),str(db),'--write'],input=json.dumps(call('booking_cancel',dict(expected_revision=3,id='2'))).encode(),capture_output=True,timeout=10);check('unterminated request not executed',q.returncode==0 and json.loads(q.stdout)['error']['code']==-32700 and db.read_bytes()==before)
 with db.open('rb')as held:
  fcntl.flock(held.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);r=wire(exe,db,[call()])[0];check('busy file is explicit tool failure',r['result']['isError']and r['result']['structuredContent']['errorCode']==35)
 # Actual separate native processes race same revision: exactly one confirmed write.
 a=dict(expected_revision=3,id='3',room=3,day=739938,start=540,finish=600)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:rs=list(pool.map(lambda _:wire(exe,db,[call('booking_reserve',a)],True)[0],range(8)))
 check('concurrent MCP commit exactly once',sum(r['result']['structuredContent']['outcome']=='confirmed'for r in rs)==1)
 r=wire(exe,db,[call()])[0];receipt(r,db);check('committed revision is four',r['result']['structuredContent']['revision']==4)
 # Controlled failure hooks prove failed/uncertain tool distinctions, not actual power loss.
 partial=('lib/io.flow','fn io_write_all(fd,p,n):IO\n','fn io_write_all(fd,p,n):IO\n let injected_write=write(fd,p,17)\n if injected_write>>63\n  return err(0-injected_write)\n end\n return err(5)\n')
 truncate=('lib/storage.flow','fn storage_truncate(fd,size)\n','fn storage_truncate(fd,size)\n return -5\n')
 close_hook=('lib/store.flow',' let closed=close(fd)\n if closed>>63\n  if (request.action!=0)|(state.committed!=0)',' let actually_closed=close(fd)\n let closed=-5\n if closed>>63\n  if (request.action!=0)|(state.committed!=0)')
 for name,changes,outcome,code in [('rolled-back',[partial],'failed',5),('rollback-uncertain',[partial,truncate],'uncertain',9002),('postcommit-uncertain',[close_hook],'uncertain',9002)]:
  fault=build('fault-'+name+'-'+str(opt),opt,changes=changes);p=D/f'fault-{name}-{opt}.db';init(cli,p);before=p.read_bytes();args=dict(expected_revision=1,id='1',room=1,day=739938,start=540,finish=600);r=wire(fault,p,[call('booking_reserve',args)],True)[0];check('controlled '+name+' exact tool outcome',r['result']['isError']and r['result']['structuredContent']==dict(outcome=outcome,errorCode=code))
  if name=='rolled-back':check('confirmed rollback exact bytes',p.read_bytes()==before)
  elif name=='postcommit-uncertain':
   follow=wire(exe,p,[call()])[0];receipt(follow,p,[dict(id='1',room=1,day=739938,start=540,finish=600)]);check('fresh read resolves postcommit uncertainty',follow['result']['structuredContent']['revision']==2)
  else:
   follow=wire(exe,p,[call()])[0];check('partial uncertain file cannot be silently read as complete',follow['result']['isError']and follow['result']['structuredContent']['errorCode']==9003)
 # Bounded random syntax probes; each process must recover to a clean independent read.
 rng=random.Random(4500+opt)
 for n in range(36):
  raw=bytes(rng.choice(b'{}[]:,"xyz012\\')for _ in range(rng.randrange(1,400)))+b'\n';before=db.read_bytes();rs=wire(exe,db,[raw,call(id='sentinel')]);check('fresh malformed input recovers without mutation',rs[-1].get('id')=='sentinel'and rs[-1].get('result',{}).get('structuredContent',{}).get('outcome')=='read'and db.read_bytes()==before)
 # Independent SDK legacy initialization, schema validation and tool error behavior.
 if NODE.is_file():
  for write in('no','yes'):
   p=D/f'sdk-{opt}-{write}.db';init(cli,p);q=subprocess.run([str(NODE),str(R/'tests/standalone/booking_sdk.mjs'),str(exe),str(p),write],capture_output=True,timeout=20);check('official SDK interoperability '+write,q.returncode==0,dict(stdout=q.stdout.decode(errors='replace'),stderr=q.stderr.decode(errors='replace')[:1200]));data=json.loads(q.stdout);check('SDK actually performed assertions',data['checks']>4)
 else:raise RuntimeError('Independent SDK runtime not present; do not skip qualification')
 print('Booking agent mode',opt,'passed',flush=True)
(D/'report.json').write_text(json.dumps(dict(checks=len(CHECKS),compilerSHA256=sha(C),results=CHECKS),indent=2)+'\n');print(json.dumps(dict(checks=len(CHECKS),report=str(D/'report.json'))))
