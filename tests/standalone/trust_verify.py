"""Native0.18 trust, independent semantics, key-policy and MCP failure tests.
Development oracle only; generated random TEST keys never enter public records.
"""
from pathlib import Path
import subprocess,json,hashlib,hmac,struct,random,time,os,select,shutil,sys
R=Path(__file__).resolve().parents[2];D=R/'artifacts/trust-0.18'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
B=Path(os.environ.get('RF2_TRUST_DIR',R/'output/trust-018-optimized')).resolve();issuer=B/'rf2-trust';verifier=B/'rf2-verify';build=json.loads((B/'BUILD.json').read_text());sid=build['sourceIdentity'];rows=[]
def call(args,timeout=10):return subprocess.run(list(map(str,args)),capture_output=True,timeout=timeout)
def check(name,condition):
 assert condition,name
 rows.append({'name':name,'passed':True})
def plan(data,ops,allow=7,budget=None):
 words=['RF2E1','allow',str(allow),'budget',str(2*len(data)*len(ops)if budget is None else budget),'input',str(len(data)),*map(str,data),'steps',str(len(ops))]
 for op,arg in ops:words +=[op]+([]if op=='reverse'else[str(arg)])
 return (' '.join(words)+'\n').encode()
def oracle(data,ops,allow,budget):
 state=list(data);r=[0]*6
 if allow>7:return state,[1,0,0,0,0,0]
 for j,(op,arg)in enumerate(ops):
  code={'add':1,'xor':2,'reverse':4}[op]
  if arg>255:return list(data),[1,j,0,0,arg,0]
  if allow&code!=code:return list(data),[2,j,0,code,allow,0]
 if budget<2*len(data)*len(ops):return list(data),[3,0,0,2*len(data)*len(ops),budget,0]
 work=0
 for j,(op,arg)in enumerate(ops):
  if op=='reverse':state.reverse();work+=len(data)
  else:
   for i,v in enumerate(state):
    work+=1
    if op=='add'and v+arg>255:return list(data),[4,j,i,255,v+arg,work]
    state[i]=v+arg if op=='add'else v^arg
 r[-1]=2*len(data)*len(ops)
 return state,r
def receipt(raw,out,run):return hashlib.sha256(b'RF2-EVIDENCE-CONTRACT-1'+sid.encode()+hashlib.sha256(raw).digest()+hashlib.sha256(bytes(out)).digest()+struct.pack('<6Q',*run)).digest()
def envelope(raw,out,run,key):
 rec=receipt(raw,out,run);kid=hashlib.sha256(b'RF2-KEY-ID-1'+key).digest()[:16];tag=hmac.new(key,b'RF2-AUTH-CAPSULE-1'+sid.encode()+rec+hashlib.sha256(raw).digest()+kid,hashlib.sha256).digest()
 return b'RF2A1 source '+sid.encode()+b' key '+kid.hex().encode()+b' receipt '+rec.hex().encode()+b' tag '+tag.hex().encode()+b' plan '+raw.hex().encode()+b'\n'
class Peer:
 def __init__(self):self.p=subprocess.Popen([issuer,'mcp',keypath],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.i=0
 def raw(self,raw,reply=True):
  self.p.stdin.write(raw+b'\n');self.p.stdin.flush()
  if not reply:return
  assert select.select([self.p.stdout],[],[],5)[0],'MCP timed out'
  return json.loads(self.p.stdout.readline())
 def request(self,m,params={}):
  self.i+=1;return self.raw(json.dumps({'jsonrpc':'2.0','id':self.i,'method':m,'params':params}).encode())
 def tool(self,name,args):return self.request('tools/call',{'name':name,'arguments':args})
 def close(self):
  self.p.stdin.close();self.p.wait(timeout=5);assert self.p.returncode==0;assert not self.p.stderr.read()
peer=None
try:
 keypath=D/'test.key';p=call([issuer,'keygen',keypath]);check('keygen native',p.returncode==0 and json.loads(p.stdout)=={'created':True});key=keypath.read_bytes();check('key length and mode',len(key)==32 and keypath.stat().st_mode&0o777==0o600)
 before=keypath.read_bytes();p=call([issuer,'keygen',keypath]);check('keygen refuses replacement',p.returncode!=0 and keypath.read_bytes()==before)
 other=D/'other.key';check('separate keygen',call([issuer,'keygen',other]).returncode==0 and other.read_bytes()!=key)
 raw=plan([1,2,3],[('add',5),('reverse',0),('xor',2)]);pf=D/'plan';cap=D/'capsule';pf.write_bytes(raw);p=call([issuer,'issue',keypath,pf]);expected=envelope(raw,[10,5,4],[0,0,0,0,0,18],key);check('native envelope equals independent HMAC/receipt',p.returncode==0 and p.stdout==expected);cap.write_bytes(p.stdout)
 check('independent offline verify',call([verifier,keypath,cap]).returncode==0);check('issuer verify route',call([issuer,'verify',keypath,cap]).returncode==0);check('wrong key rejected',call([verifier,other,cap]).returncode!=0)
 for mode in [0o644,0o640,0o400,0o666]:
  keypath.chmod(mode);check(f'insecure/unexpected key mode {oct(mode)}',call([verifier,keypath,cap]).returncode!=0)
 keypath.chmod(0o600)
 sym=D/'key-link';sym.symlink_to(keypath);check('symlink key rejected',call([verifier,sym,cap]).returncode!=0)
 fifo=D/'key-fifo';os.mkfifo(fifo,0o600);check('FIFO key refused without wait',call([verifier,fifo,cap],2).returncode!=0);fifo.unlink()
 for n in [0,31,33,64]:
  bad=D/'bad.key';bad.write_bytes(bytes(n));bad.chmod(0o600);check(f'key size {n} refuses',call([verifier,bad,cap]).returncode!=0)
 # Every tag nibble must fail; source/key/receipt/plan tampering is separately exercised.
 tokens=expected.split()
 for field in [2,4,6,8,10]:
  indexes=range(len(tokens[field]))if field==8 else range(min(12,len(tokens[field])))
  for j in indexes:
   t=tokens.copy();v=bytearray(t[field]);v[j]=ord('0')if v[j]!=ord('0')else ord('1');t[field]=bytes(v);cap.write_bytes(b' '.join(t)+b'\n');check(f'altered field {field} nibble {j}',call([verifier,keypath,cap]).returncode!=0)
 # A KEY HOLDER can authenticate nonsense. The separate semantics must still reject.
 cap.write_bytes(envelope(plan([3],[('xor',1)]),[3],[0,0,0,0,0,2],key));check('valid MAC with wrong output rejects semantics',call([verifier,keypath,cap]).returncode!=0)
 cap.write_bytes(envelope(plan([250],[('add',10)]),[250],[4,0,0,255,259,1],key));check('valid MAC with wrong error witness rejects',call([verifier,keypath,cap]).returncode!=0)
 rng=random.Random(183191)
 for i in range(180):
  n=rng.randrange(129);data=[rng.randrange(256)for _ in range(n)];ops=[(rng.choice(['add','xor','reverse']),0)for _ in range(rng.randrange(33))];ops=[(op,0 if op=='reverse'else rng.randrange(256))for op,_ in ops];allow=rng.choice([7,7,7,1,2,4,0,8]);budget=max(0,2*n*len(ops)-rng.choice([0,0,0,1]));out,run=oracle(data,ops,allow,budget);raw=plan(data,ops,allow,budget);pf.write_bytes(raw);p=call([issuer,'issue',keypath,pf]);check(f'fresh issue matches Python {i}',p.returncode==(0 if run[0]==0 else 1)and p.stdout==envelope(raw,out,run,key));cap.write_bytes(p.stdout);check(f'fresh independent verify {i}',call([verifier,keypath,cap]).returncode==0)
 for i,raw in enumerate([b'',b'RF2E2',plan([],[])+b'junk',b'\x00',plan([1],[('xor',1)]).replace(b'input 1',b'input 01'),b'X'*8193]):
  pf.write_bytes(raw);check(f'malformed plan {i}',call([issuer,'issue',keypath,pf]).returncode!=0 and not call([issuer,'issue',keypath,pf]).stdout.startswith(b'RF2A1'))
 # Stateful MCP: schema refusals must recover without leaking keys or creating files.
 peer=Peer();check('preinitialize refusal','error'in peer.request('tools/list'));check('initialize',peer.request('initialize',{'protocolVersion':'2024-11-05'})['result']['serverInfo']['name']=='rf2-contract-native');peer.raw(b'{"jsonrpc":"2.0","method":"notifications/initialized"}',False)
 check('exact bounded tools',[t['name']for t in peer.request('tools/list')['result']['tools']]==['contract_status','contract_run','contract_verify'])
 raw=plan([1,2,3],[('add',5),('reverse',0),('xor',2)]);r=peer.tool('contract_run',{'plan':raw.decode()});content=r['result']['structuredContent'];check('MCP output and native capsule',content['output']==[10,5,4]and content['capsule'].encode()==envelope(raw,[10,5,4],[0,0,0,0,0,18],key));issued=content['capsule'];check('MCP independent verification',peer.tool('contract_verify',{'capsule':issued})['result']['structuredContent']['verified']is True)
 for i,args in enumerate([{}, {'plan':raw.decode(),'key':key.hex()},{'plan':raw.decode(),'path':'/tmp/forbidden'},{'plan':123},{'plan':None},{'plan':raw.decode(),'allow':7},{'capsule':issued,'keyfile':str(keypath)}]):
  r=peer.tool('contract_run'if'capsule'not in args else'contract_verify',args);check(f'MCP forbidden schema {i}','error'in r or r.get('result',{}).get('isError')is True)
 for i,packet in enumerate([b'notjson',b'{"jsonrpc":"2.0","id":97,"method":"tools/call","params":{"name":"contract_run","arguments":{"plan":"a","plan":"b"}}}',b'{"jsonrpc":"2.0","id":98,"method":"tools/call","params":{"name":"contract_run","arguments":{"pl\\u0061n":"x","plan":"y"}}}',b'X'*65537]):
  check(f'MCP malformed {i}','error'in peer.raw(packet));check(f'MCP recovery {i}','result'in peer.tool('contract_status',{}))
 r=peer.tool('contract_verify',{'capsule':issued.replace('tag ','tag f',1)});check('MCP altered auth refuses',r['result']['isError']is True)
 check('final request recovery','result'in peer.tool('contract_status',{}));peer.close();peer=None
 report={'date':'2026-11-13','passed':True,'checks':len(rows),'sourceIdentity':sid,'build':build,'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'seed':183191,'results':rows,'limits':['Shared-key authentication: key holders can forge; no public signature or nonrepudiation','Independent parser/trajectory algorithm shares compiler/crypto; not toolchain independence','MCP is separate native stdio service;9original tools unchanged','No key bytes in published report; all keys are local test artifacts']};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(rows),'report':str(D/'report.json')},indent=2))
except Exception:
 (D/'partial.json').write_text(json.dumps(rows,indent=2)+'\n')
 if peer is not None:peer.p.kill();peer.p.wait()
 raise
