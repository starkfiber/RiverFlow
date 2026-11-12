"""Observed native stdio round trips including Python host transport/JSON cost."""
from pathlib import Path
import subprocess,time,json,select,statistics,hashlib,os
R=Path(__file__).resolve().parents[2];B=R/'output/trust-0.18';D=R/'artifacts/trust-0.18'/('mcp-measure-'+str(time.time_ns()));D.mkdir(parents=True);key=D/'public-test.key';key.write_bytes(bytes(range(32)));key.chmod(0o600)
p=subprocess.Popen([B/'rf2-trust','mcp',key],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);counter=0

def req(method,params={}):
 global counter
 counter+=1;raw=json.dumps({'jsonrpc':'2.0','id':counter,'method':method,'params':params},separators=(',',':')).encode();p.stdin.write(raw+b'\n');p.stdin.flush();assert select.select([p.stdout],[],[],10)[0];reply=p.stdout.readline();r=json.loads(reply);assert 'error'not in r,r
 return r,len(raw)+1,len(reply)
def tool(name,args):return req('tools/call',{'name':name,'arguments':args})
req('initialize',{'protocolVersion':'2024-11-05'});p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');p.stdin.flush();rows=[]
try:
 for n,steps in [(8,1),(128,8),(128,32)]:
  data=list(range(n));ops=[('xor',j&255)if j%2==0 else('reverse',0)for j in range(steps)];words=['RF2E1','allow','7','budget',str(2*n*steps),'input',str(n),*map(str,data),'steps',str(steps)]
  for op,arg in ops:words +=[op]+([]if op=='reverse'else[str(arg)])
  plan=' '.join(words)+'\n';r,_,_=tool('contract_run',{'plan':plan});cap=r['result']['structuredContent']['capsule'];trials={}
  for name,args in [('contract_run',{'plan':plan}),('contract_verify',{'capsule':cap})]:
   for _ in range(3):tool(name,args)
   samples=[];sizes=[]
   for trial in range(11):
    start=time.perf_counter_ns()
    for _ in range(20):
     out,sent,received=tool(name,args);assert out['result']['structuredContent'].get('code')==0;sizes.append((sent,received))
    samples.append((time.perf_counter_ns()-start)/1e6/20)
   trials[name]={'perCallMs':samples,'medianPerCallMs':statistics.median(samples),'requestByteRange':[min(x[0]for x in sizes),max(x[0]for x in sizes)],'responseByteRange':[min(x[1]for x in sizes),max(x[1]for x in sizes)]}
  rows.append({'bytes':n,'steps':steps,'trials':trials})
finally:p.stdin.close();p.wait(timeout=5);assert p.returncode==0 and not p.stderr.read()
report={'date':'2026-11-13','rows':rows,'trials':11,'callsPerTrial':20,'warmups':3,'build':json.loads((B/'BUILD.json').read_text()),'scope':'One local stdio process. Includes native parsing, execution or verification, authentication, pipes and Python host JSON serialization/deserialization. Not a network, GPU, pure engine, AI bill/token or crosslanguage result. No previous authenticated MCP baseline existed.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'medians':[{ 'bytes':x['bytes'],'steps':x['steps'],**{k:v['medianPerCallMs']for k,v in x['trials'].items()}}for x in rows]},indent=2))
