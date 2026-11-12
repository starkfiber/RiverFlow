"""Actual standalone executable tests. Python/Node are development oracles only."""
from pathlib import Path
import json, subprocess, random, hashlib, os, time, sys, select, tempfile, atexit
R=Path(__file__).resolve().parents[2];binary=Path(os.environ.get('RF2_TEST_BINARY',str(R/'output/bin/rf2')))
node=os.environ.get('RF2_TEST_NODE','/opt/homebrew/opt/node@22/bin/node')
class Peer:
 def __init__(self,args):self.p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.i=0;atexit.register(lambda: self.p.kill() if self.p.poll() is None else None)
 def send(self,obj,reply=True):
  raw=obj if isinstance(obj,bytes) else json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
  self.p.stdin.write(raw+b'\n');self.p.stdin.flush()
  if not reply:return
  if not select.select([self.p.stdout],[],[],8)[0]:raise AssertionError('Native request timed out')
  line=self.p.stdout.readline()
  if not line:raise AssertionError(f'Native process exited {self.p.poll()}: {self.p.stderr.read(400)}')
  return json.loads(line)
 def rpc(self,method,params=None):
  self.i+=1;obj={'jsonrpc':'2.0','id':self.i,'method':method}
  if params is not None:obj['params']=params
  out=self.send(obj);assert out['id']==self.i;return out
 def run(self,source,data,count=None):
  args={'source':source,'data':data}
  if count is not None:args['count']=count
  return self.rpc('tools/call',{'name':'rf2_run','arguments':args})
 def close(self):
  self.p.stdin.close();self.p.wait(timeout=8);assert self.p.returncode==0;assert self.p.stderr.read()==b''
def expand(op,mode):
 p=subprocess.run([str(binary),'expand',str(R/f'examples/compact/{op}-{mode}.rf2')],capture_output=True,text=True,check=True)
 return p.stdout
report={'schema':'rf2.standalone.verification.v1','target':'macos-arm64','speedClaim':None,'selfHosted':False,'differentialCases':0,'independentCases':0,'negativeCases':0,'parserMutations':0,'maxInputWords':65536,'tests':[]}
peer=Peer([str(binary),'mcp']);oracle=Peer([node,str(R/'tests/standalone/oracle.mjs')])
assert peer.rpc('tools/list')['error']['code']==-32002
assert peer.rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'independent test','version':'1'}})['result']['serverInfo']['version']==os.environ.get('RF2_TEST_VERSION','0.4.0')
peer.send({'jsonrpc':'2.0','method':'notifications/initialized'},False)
assert len(peer.rpc('tools/list')['result']['tools'])==int(os.environ.get('RF2_TEST_TOOLS','3'))
assert peer.rpc('initialize',{'protocolVersion':'2024-11-05'})['error']['code']==-32600
randomizer=random.Random(20261111)
for op in ['sum','squares','bits','nonzero']:
 for mode in ['checked','wrap']:
  source=f'rf2 v1 {mode}\n{op} input\n';path=R/f'examples/compact/{op}-{mode}.rf2';path.write_text(source)
  core=expand(op,mode)
  arrays=[[],[0],[4294967295],[4294967295,1],[65535,65536],[0,1,2,3,4294967295],[1]*65536]
  arrays += [[randomizer.randrange(1<<32) if i%3 else randomizer.randrange(1000) for _ in range(randomizer.randrange(0,101))]for i in range(120)]
  for i,data in enumerate(arrays):
   count=len(data) if i%4 else randomizer.randrange(len(data)+1)
   got=peer.run(source,data,count)
   expected=oracle.send({'source':core,'data':data,'count':count})
   total=0;ok=True
   for x in data[:count]:
    value={'sum':lambda:x,'squares':lambda:x*x,'bits':lambda:bin(x).count('1'),'nonzero':lambda:int(x!=0)}[op]()
    if mode=='checked' and value>0xffffffff:ok=False;break
    value&=0xffffffff;total+=value
    if mode=='checked' and total>0xffffffff:ok=False;break
    total&=0xffffffff
   assert expected['ok']==ok,(op,mode,data,count,expected)
   actualok='result' in got and not got['result'].get('isError',False)
   assert actualok==ok,(op,mode,got,expected)
   if ok:
    value=got['result']['structuredContent'];assert value['value']==total==expected['value'];assert value['steps']==expected['steps']
   else:assert 'overflow' in got['result']['content'][0]['text'].lower()
   report['differentialCases']+=1;report['independentCases']+=1
report['tests'].append('Eight compact operations/modes expand to checked Core; native result, event counts and overflow agree with JS and independent integer arithmetic')
valid='rf2 v1 checked\nsum input'
for data,count in [([1],2),([-1],None),([4294967296],None),([1.5],None),(['1'],None),([None],None),([True],None),([[]],None),([{}],None),([1]*65537,None),([1],-1),([1],1.5)]:
 got=peer.run(valid,data,count);assert 'error' in got or got['result'].get('isError');report['negativeCases']+=1
for src in ['', 'sum input','rf2 v2 checked sum input','rf2 v1 sum input','rf2 v1 checked sum input extra','rf2 v1 checked network input','profile RF2_SYSTEM_A64_V1','rf2 v1 checked sum input\0','a'*32769,(R/'examples/sum.flow').read_text()]:
 if src==(R/'examples/sum.flow').read_text() and os.environ.get('RF2_TEST_VERSION')in ['0.6.0','0.7.0','0.8.0','0.9.0','0.10.0','0.11.0','0.12.0','0.13.0','0.14.0','0.15.0']:
  assert peer.run(src,[1])['result']['structuredContent']['value']==1
 else:
  got=peer.run(src,[1]);assert got['result'].get('isError');report['negativeCases']+=1
# Whitespace is flexible; unsupported words are never silently ignored.
assert peer.run(' \t rf2\r\nv1\tchecked \n sum\tinput \r\n',[1,2])['result']['structuredContent']['value']==3
# Valid alternate JSON number spellings and escaped key names.
special=b'{"jsonrpc":"2.0","id":"Unicode \\u0ba4\\u0bae\\u0bbf\\u0bb4\\u0bcd \\ud83c\\udf0a","method":"tools/call","params":{"name":"rf2_run","arguments":{"sou\\u0072ce":"rf2 v1 checked\\nsum input","data":[1e0,2.00,300e-2,-0,0e99999]}}}'
assert peer.send(special)['result']['structuredContent']['value']==6
for n in ['1e100000','-1e0','0.1','18446744073709551616','1844674407.3709551616e10','4.294967296e9']:
 raw=b'{"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"rf2_run","arguments":{"source":"rf2 v1 checked sum input","data":['+n.encode()+b']}}}'
 assert peer.send(raw)['result'].get('isError');report['negativeCases']+=1
for raw in [b'{',b'[]',b'null',b'{"jsonrpc":"1.0","id":1,"method":"ping"}',b'{"jsonrpc":"2.0","id":1,"method":"ping","method":"tools/list"}',b'{"jsonrpc":"2.0","id":1,"me\\u0074hod":"ping","method":"ping"}',b'{"a":'+b'['*40+b'0'+b']'*40+b'}',b'{"x":"\\ud800"}',b'{"x":"\xff"}',b'{"x":01}',b'{"x":1.}',b'{"x":1e}',b'{"x":[1,]}',b'{"x":trueX}',b'{"x":"bad\\q"}']:
 assert 'error' in peer.send(raw);report['negativeCases']+=1
# Seeded byte mutations, crash/time bound and recovery, not proof of complete parser safety.
base=json.dumps({'jsonrpc':'2.0','id':99,'method':'tools/call','params':{'name':'rf2_run','arguments':{'source':valid,'data':[1,2,3]}}},separators=(',',':')).encode()
for i in range(250):
 arr=bytearray(base);pos=randomizer.randrange(len(arr));arr[pos]=randomizer.choice([0,1,34,44,58,92,123,125,255]);arr=bytes(arr).replace(b'\n',b' ')
 try: decoded=json.loads(arr)
 except (ValueError,UnicodeDecodeError): decoded=None
 if isinstance(decoded,dict) and 'id' not in decoded and decoded.get('jsonrpc')=='2.0' and isinstance(decoded.get('method'),str):
  peer.send(arr,False);assert peer.rpc('ping')['result']=={}
 else:
  got=peer.send(arr);assert isinstance(got,dict);assert got.get('jsonrpc')=='2.0'
 report['parserMutations']+=1
assert peer.send(b' '*1048577)['error']['code']==-32700
assert peer.run(valid,[2,3])['result']['structuredContent']['value']==5
report['tests'].append('Malformed JSON, duplicate/escaped keys, UTF-8, surrogate pairs, size/depth/data bounds, numeric forms, 250 seeded mutations and request recovery exercised')
# No Node, npm, Python, C compiler or C++ runtime is needed in the executable environment.
r=subprocess.run([str(binary),'run',str(R/'examples/compact/sum.rf2'),'[1,2,3]'],env={'PATH':'/nonexistent'},capture_output=True,text=True,check=True);assert json.loads(r.stdout)['value']==6
report['tests'].append('Native CLI runs with PATH=/nonexistent')
for args in [['check',str(R/'examples/compact/sum.rf2')],['status'],['expand',str(R/'examples/compact/sum.rf2')]]:
 assert subprocess.run([str(binary),*args],capture_output=True).returncode==0
assert subprocess.run([str(binary),'run','/nonexistent','[]'],capture_output=True).returncode==1
peer.close();oracle.close()
if os.environ.get('RF2_TEST_VERSION')in ['0.6.0','0.7.0','0.8.0','0.9.0','0.10.0','0.11.0','0.12.0','0.13.0','0.14.0','0.15.0']:
 report.pop('selfHosted',None);report['runtimeVersion']=os.environ.get('RF2_TEST_VERSION');report['systemsCompiler']='Native compiler self-reproduction is qualified in a separate report';report['sourceFiles']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [R/'native/rf2.rf2',R/'native/core.rf2',R/'native/attendance.rf2',R/'native/attendance-kernel.rf2',R/'native/fingerprint.rf2']+([R/'native/invoice.rf2',R/'native/invoice-kernel.rf2']if os.environ.get('RF2_TEST_VERSION')in ['0.7.0','0.8.0','0.9.0','0.10.0','0.11.0','0.12.0','0.13.0','0.14.0','0.15.0']else[])+([R/'native/prepared.rf2',R/'native/workspace.rf2']if os.environ.get('RF2_TEST_VERSION')in ['0.8.0','0.9.0','0.10.0','0.11.0','0.12.0','0.13.0','0.14.0','0.15.0']else[])+([R/'native/editor.rf2']if os.environ.get('RF2_TEST_VERSION')in ['0.9.0','0.10.0','0.11.0','0.12.0','0.13.0','0.14.0','0.15.0']else[])}
report['executableSHA256']=hashlib.sha256(binary.read_bytes()).hexdigest();report['sourceSHA256']=hashlib.sha256((R/'native/rf2.rf2').read_bytes()).hexdigest();report['bootstrapSHA256']=hashlib.sha256((R/'bootstrap/seed.py').read_bytes()).hexdigest();report['passed']=True
Path(os.environ.get('RF2_TEST_REPORT',str(R/'docs/STANDALONE-VERIFICATION.json'))).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
