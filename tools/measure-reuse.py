"""0.8 vs frozen 0.7 and JS; full serialized reuse lifecycle counts, no inference billing."""
from pathlib import Path
import sys,os,json,time,statistics,hashlib,platform
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tests/standalone'))
from invoice_verify import Peer,value,expect,NODE
import tiktoken
B=Path(os.environ.get('RF2_TEST_BINARY',str(R/'output/runtime-0.8-ready/rf2')));OLD=Path(os.environ.get('RF2_BASELINE_BINARY',str(R/'output/package/rf2-0.7.0/rf2')));plan=(R/'capabilities/invoice.total.v1/quote.rf2').read_text()
def connect(b):
 p=Peer([b,'mcp']);p.request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'reuse-measurement','version':'1'}});p.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');p.p.stdin.flush();return p
report={'scope':'One-host persistent JSON-lines roundtrip including controller serialization/result checking; startup, discovery and plan preparation excluded from latency. Token experiment includes preparation/release, schemas and exact requests/responses. No inference API invoked.','host':platform.platform(),'runtimeSHA256':hashlib.sha256(B.read_bytes()).hexdigest(),'baseline07SHA256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'raw':[],'summary':[]}
for process_set in range(3):
 p=connect(B);old=connect(OLD);js=Peer([NODE,R/'tests/standalone/invoice_reference.mjs']);handle=value(p.call('invoice_prepare',{'plan':plan}))['plan_id']
 for n in [1,32,1000]:
  lines=[{'quantity':1+i%5,'unit_cents':100+i%97}for i in range(n)];e=expect(plan,lines);jobs=[('native07',old,'invoice_total',{'plan':plan,'lines':lines}),('native08',p,'invoice_total',{'plan':plan,'lines':lines}),('prepared08',p,'invoice_apply',{'plan_id':handle,'lines':lines}),('js',js,'invoice_total_explicit',{'currency':'MYR','tax_bps':600,'lines':lines})]
  for _,peer,name,args in jobs:
   for _ in range(5):assert value(peer.call(name,args))==e
  for t in range(7):
   for label,peer,name,args in jobs[t%4:]+jobs[:t%4]:
    batch=50 if n<1000 else 10;start=time.perf_counter_ns()
    for _ in range(batch):assert value(peer.call(name,args))==e
    report['raw'].append({'processSet':process_set,'trial':t,'lines':n,'variant':label,'batch':batch,'us':(time.perf_counter_ns()-start)/batch/1000})
 assert value(p.call('invoice_release',{'plan_id':handle}))['released'];p.close();old.close();js.close()
for n in [1,32,1000]:
 row={'lines':n}
 for label in ['native07','native08','prepared08','js']:
  v=[x['us']for x in report['raw']if x['lines']==n and x['variant']==label];row[label]={'medianUs':statistics.median(v),'minUs':min(v),'maxUs':max(v)}
 report['summary'].append(row)
fixtures={};counts={};rows=json.loads((R/'capabilities/invoice.total.v1/test-lines.json').read_text())
# Three independent handles record random spelling variability. Clients discard all handles on reconnect.
for n in [1,20,100]:
 for sample in range(3):
  p=connect(B);old=connect(OLD);ns=p.request('tools/list',{})['result']['tools'];oschema=old.request('tools/list',{})['result']['tools'];new=[];previous=[]
  def call(peer,name,args,log):
   response=peer.call(name,args);q={'jsonrpc':'2.0','id':response['id'],'method':'tools/call','params':{'name':name,'arguments':args}};log.extend([q,response]);return value(response)
  prepared=call(p,'invoice_prepare',{'plan':plan},new);h=prepared['plan_id'];assert prepared['taxBps']==600 and prepared['currency']=='MYR'
  for _ in range(n):assert call(p,'invoice_apply',{'plan_id':h,'lines':rows},new)==call(old,'invoice_total',{'plan':plan,'lines':rows},previous)==expect(plan,rows)
  assert call(p,'invoice_release',{'plan_id':h},new)['released'];p.close();old.close()
  serial=lambda x:json.dumps(x,separators=(',',':'),ensure_ascii=False)
  name=f'{n}-calls-sample-{sample}';fixtures[name]={'native08Catalog':serial({'tools':ns}),'native07Catalog':serial({'tools':oschema}),'reuseLifecycle':'\n'.join(map(serial,new)),'unpreparedLifecycle':'\n'.join(map(serial,previous))}
  for encoding in ['o200k_base','cl100k_base']:
   enc=tiktoken.get_encoding(encoding);v={k:len(enc.encode(text))for k,text in fixtures[name].items()};v['reuseTotal']=v['native08Catalog']+v['reuseLifecycle'];v['unpreparedTotal']=v['native07Catalog']+v['unpreparedLifecycle'];counts.setdefault(encoding,{})[name]=v
report['tokenization']={'library':'tiktoken','version':tiktoken.__version__,'scope':'All discovered schemas plus complete prepare/apply/release or unprepared calls, including responses. Shared initialization/framing/caching/model reasoning and actual AI construction/repairs not counted. Exact encoded text, not billed model usage.','counts':counts}
(R/'docs/REUSE-TOKEN-FIXTURES-0.8.json').write_text(json.dumps(fixtures,indent=2)+'\n');report['sourceHashes']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),R/'docs/REUSE-TOKEN-FIXTURES-0.8.json']};(R/'docs/REUSE-MEASUREMENTS-0.8.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'summary':report['summary'],'counts':{e:{k:{'reuse':v['reuseTotal'],'unprepared':v['unpreparedTotal']}for k,v in rows.items()}for e,rows in counts.items()}},indent=2))
