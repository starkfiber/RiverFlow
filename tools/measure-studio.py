"""0.9 vs frozen 0.8, GUI protocol and exact encoded MCP interface counts."""
from pathlib import Path
import sys,os,json,time,statistics,hashlib,platform,subprocess,re,select,http.client,urllib.parse
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tests/standalone'));from invoice_verify import Peer,value,expect
import tiktoken
B=R/'output/native-0.9/rf2';OLD=R/'output/package/rf2-0.8.0/rf2';plan=(R/'capabilities/invoice.total.v1/quote.rf2').read_text()
def connect(binary):
 p=Peer([binary,'mcp']);p.request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'studio-measurement','version':'1'}});p.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');p.p.stdin.flush();return p
class Editor:
 def __init__(self):
  self.p=subprocess.Popen([B,'editor'],stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert select.select([self.p.stdout],[],[],15)[0];self.url=re.search(r'http://127\.0\.0\.1:\d+',self.p.stdout.readline().decode()).group(0);self.port=int(self.url.rsplit(':',1)[1]);self.page=self.request('GET','/')[1].decode()
 def request(self,method,path,body=None):
  c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=10);h={'Origin':self.url,'Content-Type':'application/x-www-form-urlencoded'}if body is not None else{};c.request(method,path,body=body,headers=h);r=c.getresponse();data=r.read();code=r.status;c.close();return code,data
 def fields(self):return {k:re.search('name='+k+' value="([^"]+)"',self.page).group(1)for k in ['token','rev']}
 def apply(self,lines,e):
  f=self.fields();f.update(currency='MYR',tax=600,rows=len(lines),action='apply')
  for i,x in enumerate(lines):f['q'+str(i)]=x['quantity'];f['p'+str(i)]=str(x['unit_cents']//100)+'.'+str(x['unit_cents']%100).zfill(2)
  assert self.request('POST','/edit',urllib.parse.urlencode(f))[0]==303;code,body=self.request('GET','/');assert code==200;self.page=body.decode();amount=str(e['totalCents']//100)+'.'+str(e['totalCents']%100).zfill(2);assert 'Total</span>'+amount+'<'in self.page
  return len(body)
 def close(self):assert self.request('POST','/quit',urllib.parse.urlencode(self.fields()))[0]==200;self.p.wait(timeout=5);assert self.p.returncode==0 and not self.p.stderr.read()
report={'schema':'rf2.studio.measurement.v1','runtimeSHA256':hashlib.sha256(B.read_bytes()).hexdigest(),'baseline08SHA256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'host':platform.platform(),'scope':'One-host persistent MCP roundtrips vs frozen 0.8. Separate GUI timing includes form encoding, POST, redirect GET, HTML generation and controller result check, not browser DOM/layout. Different work; no GUI-vs-MCP speedup claim. Startup/discovery/preparation excluded.','freshProcessSets':3,'trialsPerSet':7,'raw':[],'summary':[]}
for group in range(3):
 new=connect(B);old=connect(OLD);handle=value(new.call('invoice_prepare',{'plan':plan}))['plan_id'];ui=Editor()
 for size in [1,32,1000]:
  lines=[{'quantity':1+i%5,'unit_cents':100+i%97}for i in range(size)];e=expect(plan,lines);args={'plan':plan,'lines':lines};jobs=[('mcp08',old,'invoice_total',args),('mcp09',new,'invoice_total',args),('prepared09',new,'invoice_apply',{'plan_id':handle,'lines':lines})]
  for _,p,name,a in jobs:
   for _ in range(5):assert value(p.call(name,a))==e
  ui.apply(lines,e)
  for t in range(7):
   for label,p,name,a in jobs[t%3:]+jobs[:t%3]:
    batch=50 if size<1000 else 10;start=time.perf_counter_ns()
    for _ in range(batch):assert value(p.call(name,a))==e
    report['raw'].append({'set':group,'trial':t,'lines':size,'variant':label,'batch':batch,'us':(time.perf_counter_ns()-start)/batch/1000})
   start=time.perf_counter_ns();html=ui.apply(lines,e);report['raw'].append({'set':group,'trial':t,'lines':size,'variant':'gui_http09','batch':1,'us':(time.perf_counter_ns()-start)/1000,'htmlBytes':html})
 assert value(new.call('invoice_release',{'plan_id':handle}))['released'];new.close();old.close();ui.close()
for size in [1,32,1000]:
 row={'lines':size}
 for label in ['mcp08','mcp09','prepared09','gui_http09']:
  xs=[x['us']for x in report['raw']if x['lines']==size and x['variant']==label];row[label]={'medianUs':statistics.median(xs),'minUs':min(xs),'maxUs':max(xs)}
 report['summary'].append(row)
fixtures={};counts={};schema_hashes=[]
for n in [20,100]:
 for sample in range(3):
  peers=[connect(OLD),connect(B)];texts=[]
  for peer in peers:
   tools=peer.request('tools/list',{})['result']['tools'];catalog=json.dumps({'tools':tools},separators=(',',':'));schema_hashes.append(hashlib.sha256(catalog.encode()).hexdigest());events=[]
   def call(name,args):
    a=peer.call(name,args);events.extend([{'jsonrpc':'2.0','id':a['id'],'method':'tools/call','params':{'name':name,'arguments':args}},a]);return value(a)
   h=call('invoice_prepare',{'plan':plan})['plan_id'];lines=[{'quantity':2,'unit_cents':1250},{'quantity':1,'unit_cents':399}]
   for _ in range(n):assert call('invoice_apply',{'plan_id':h,'lines':lines})==expect(plan,lines)
   assert call('invoice_release',{'plan_id':h})['released'];peer.close();texts.append({'catalog':catalog,'lifecycle':'\n'.join(json.dumps(x,separators=(',',':'))for x in events)})
  key=f'{n}-calls-sample-{sample}';fixtures[key]={'old08':texts[0],'new09':texts[1]}
  for encoding in ['o200k_base','cl100k_base']:
   enc=tiktoken.get_encoding(encoding);counts.setdefault(encoding,{})[key]={label:len(enc.encode(x['catalog']))+len(enc.encode(x['lifecycle']))for label,x in fixtures[key].items()}
assert len(set(schema_hashes))==1
report['tokens']={'library':'tiktoken','version':tiktoken.__version__,'catalogSHA256':schema_hashes[0],'catalogByteIdentical08And09':True,'counts':counts,'scope':'All nine actual discovered schemas plus complete prepare/apply/release requests and responses. Random handle spelling varies. Exact encoded text, not billed model usage or complete AI-task savings. No model API called; no provider usage receipts. Browser UI has no inference client.'}
(R/'docs/STUDIO-TOKEN-FIXTURES-0.9.json').write_text(json.dumps(fixtures,indent=2)+'\n');report['sourceHashes']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),R/'docs/STUDIO-TOKEN-FIXTURES-0.9.json']};(R/'docs/STUDIO-MEASUREMENTS-0.9.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'summary':report['summary'],'tokens':report['tokens']},indent=2))
