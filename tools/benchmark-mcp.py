"""Native bounded MCP tools, not model generation or billed token usage."""
from pathlib import Path
import os,subprocess,json,time,select,statistics,tempfile,random,hashlib
R=Path(__file__).resolve().parents[1];D=R/'artifacts/mappings-0.21'/('mcp-'+str(time.time_ns()));D.mkdir(parents=True);versions={'RF2 0.20':R/'output/trust-0.20','RF2 0.21':Path(os.environ.get('RF2_TRUST_DIR',R/'output/trust-0.21-qualified'))};sessions={};report={'passed':False,'scope':'Local persistent native stdio services; includes native execution/HMAC, pipes and Python host JSON. Nine rotated trials,20calls per trial after3warmups. No network, provider inference, AI generation, billed tokens or language-equivalence claim.','raw':[],'summary':[]}
class Session:
 def __init__(self,path,key):
  self.p=subprocess.Popen([path/'rf2-trust','mcp',key],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/nonexistent'});self.i=0;self.request('initialize',{'protocolVersion':'2025-06-18'});self.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');self.p.stdin.flush()
 def request(self,method,args):
  self.i+=1;raw=json.dumps({'jsonrpc':'2.0','id':self.i,'method':method,'params':args},separators=(',',':')).encode();self.p.stdin.write(raw+b'\n');self.p.stdin.flush();assert select.select([self.p.stdout],[],[],5)[0];reply=self.p.stdout.readline();v=json.loads(reply);assert 'error'not in v,v;return v,len(raw)+1,len(reply)
 def tool(self,name,args):
  v,sent,got=self.request('tools/call',{'name':name,'arguments':args});assert not v['result'].get('isError'),v;return v['result']['structuredContent'],sent,got
 def close(self):self.p.stdin.close();self.p.wait(timeout=5);assert self.p.returncode==0 and not self.p.stderr.read()
with tempfile.TemporaryDirectory(prefix='rf2-bench-keys-')as td:
 key=Path(td)/'key';key.write_bytes(os.urandom(32));key.chmod(0o600)
 try:
  for name,path in versions.items():sessions[name]=Session(path,key)
  for n,steps in [(8,1),(128,8),(128,32)]:
   words=['RF2E1','allow','7','budget',str(2*n*steps),'input',str(n),*map(str,range(n)),'steps',str(steps)]
   for j in range(steps):words+=['xor',str(j&255)]if j%2==0 else['reverse']
   plan=' '.join(words)+'\n';args={};times={}
   for version,s in sessions.items():
    cap=s.tool('contract_run',{'plan':plan})[0]['capsule']
    for tool,a in [('contract_run',{'plan':plan}),('contract_verify',{'capsule':cap})]:
     ident=version+' '+tool;args[ident]=(s,tool,a);times[ident]=[]
     for _ in range(3):s.tool(tool,a)
   for trial in range(9):
    order=list(args);random.Random(2100+trial).shuffle(order)
    for ident in order:
     s,tool,a=args[ident];start=time.perf_counter_ns();sizes=[]
     for _ in range(20):
      result,sent,received=s.tool(tool,a);assert result.get('code')==0; sizes.append([sent,received])
     ms=(time.perf_counter_ns()-start)/1e6/20;times[ident].append(ms);report['raw'].append({'bytes':n,'steps':steps,'trial':trial,'variant':ident,'msPerCall':ms,'requestResponseBytes':sizes})
   report['summary'].append({'bytes':n,'steps':steps,'medianMsPerCall':{k:statistics.median(v)for k,v in times.items()}})
 finally:
  for s in sessions.values():s.close()
report['passed']=True;report['binarySHA256']={k:hashlib.sha256((v/'rf2-trust').read_bytes()).hexdigest()for k,v in versions.items()};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'summary':report['summary']},indent=2))
