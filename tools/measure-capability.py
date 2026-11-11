"""Reproducible local latency and encoded-interface experiment, not AI inference billing."""
from pathlib import Path
import sys,os,json,hashlib,time,statistics,platform,subprocess,datetime
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tests/standalone'))
from invoice_verify import Peer,value,expect,B,OLD,NODE
import tiktoken
report={'schema':'rf2.capability.measurement.v1','runtimeSHA256':hashlib.sha256(B.read_bytes()).hexdigest(),'baseline06SHA256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'nodeVersion':subprocess.check_output([NODE,'--version']).decode().strip(),'host':{'os':platform.platform(),'machine':platform.machine(),'model':subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model']).decode().strip()},'measuredUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'clock':'time.perf_counter_ns','scope':'Persistent JSON-lines request roundtrip, includes controller JSON encoding/decoding, IPC, validation, calculation and response. Process launch, schema discovery and compilation excluded. One host, not CPU-kernel or energy measurements.','freshPairs':3,'trialsPerPair':7,'warmups':5,'raw':[],'summary':[]}
plan=(R/'capabilities/invoice.total.v1/quote.rf2').read_text();core=(R/'capabilities/invoice.total.v1/total.flow').read_text()
def initialize(p):
 p.request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'measurement','version':'1'}});p.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');p.p.stdin.flush()
def trial(p,name,args,expected,n):
 start=time.perf_counter_ns()
 for _ in range(n):assert value(p.call(name,args))==expected
 return (time.perf_counter_ns()-start)/n/1000
for pair in range(3):
 native=Peer([B,'mcp']);old=Peer([OLD,'mcp']);js=Peer([NODE,R/'tests/standalone/invoice_reference.mjs']);initialize(native);initialize(old)
 for size in [1,32,1000]:
  lines=[{'quantity':1+(i%5),'unit_cents':100+(i%97)}for i in range(size)];expected=expect(plan,lines);args={'plan':plan,'lines':lines};other={'currency':'MYR','tax_bps':600,'lines':lines};flat=[v for x in lines for v in [x['quantity'],x['unit_cents']]];cargs={'source':core,'data':flat,'count':size}
  oldv=value(old.call('rf2_run',cargs));assert oldv['value']==expected['subtotalCents'] and value(native.call('rf2_run',cargs))==oldv
  jobs=[('invoice_native',native,'invoice_total',args,expected),('invoice_js_explicit',js,'invoice_total_explicit',other,expected),('core_06',old,'rf2_run',cargs,oldv),('core_07',native,'rf2_run',cargs,oldv)]
  for _,p,name,a,e in jobs:
   for _ in range(5):assert value(p.call(name,a))==e
  for t in range(7):
   order=jobs[t%4:]+jobs[:t%4];batches=50 if size<1000 else 10
   for label,p,name,a,e in order:report['raw'].append({'pair':pair,'trial':t,'lines':size,'variant':label,'batch':batches,'microsecondsPerRequest':trial(p,name,a,e,batches)})
 for p in [native,old,js]:p.close();assert p.p.returncode==0 and not p.p.stderr.read()
for size in [1,32,1000]:
 row={'lines':size}
 for label in ['invoice_native','invoice_js_explicit','core_06','core_07']:
  v=[x['microsecondsPerRequest']for x in report['raw']if x['lines']==size and x['variant']==label];row[label]={'medianUs':statistics.median(v),'minUs':min(v),'maxUs':max(v),'trials':len(v)}
 row['invoiceRoundtripRatioJsOverNative']=row['invoice_js_explicit']['medianUs']/row['invoice_native']['medianUs'];row['coreRoundtripRatio06Over07']=row['core_06']['medianUs']/row['core_07']['medianUs'];report['summary'].append(row)
# Count exact serialized interface text using public tokenizers; no model call takes place.
peer=Peer([B,'mcp']);initialize(peer);tools=peer.request('tools/list',{})['result']['tools'];native_schema=tools[-1]
lines=json.loads((R/'capabilities/invoice.total.v1/test-lines.json').read_text());e=expect(plan,lines)
def compact(v):return json.dumps(v,separators=(',',':'),ensure_ascii=False)
def req(i,name,args):return {'jsonrpc':'2.0','id':i,'method':'tools/call','params':{'name':name,'arguments':args}}
nreq=[req(i,'invoice_total',{'plan':plan,'lines':lines})for i in range(1,21)];jreq=[req(i,'invoice_total_explicit',{'currency':'MYR','tax_bps':600,'lines':lines})for i in range(1,21)]
nresponses=[peer.request(q['method'],q['params'])for q in nreq];ref=Peer([NODE,R/'tests/standalone/invoice_reference.mjs']);explicit_schema=ref.request('tools/list',{})['result']['tools'][0];jresponses=[ref.request(q['method'],q['params'])for q in jreq];
for q,a in zip(nreq,nresponses):q['id']=a['id']
for q,a in zip(jreq,jresponses):q['id']=a['id']
assert all(value(x)==e for x in nresponses+jresponses)
texts={'compactPlan':plan,'nativeToolSchema':compact(native_schema),'explicitReferenceToolSchema':compact(explicit_schema),'allSixNativeToolSchemas':compact({'tools':tools}),'native20Requests': '\n'.join(map(compact,nreq)),'explicit20Requests':'\n'.join(map(compact,jreq)),'native20Responses':'\n'.join(map(compact,nresponses)),'explicit20Responses':'\n'.join(map(compact,jresponses))}
(R/'docs/INTERFACE-TOKEN-FIXTURES.json').write_text(json.dumps(texts,indent=2)+'\n')
report['tokenization']={'library':'tiktoken','version':tiktoken.__version__,'encodings':{},'scope':'Exact fixture text counts, not billed model usage, reasoning tokens or full task savings. No inference API invoked. Same input data and result, alternative plan vs explicit-config interfaces. Cached prompts, framing, tool selection, construction and repairs not measured.'}
for encoding in ['o200k_base','cl100k_base']:
 enc=tiktoken.get_encoding(encoding);counts={k:len(enc.encode(v))for k,v in texts.items()};counts['nativeSchemaPlus20Roundtrips']=counts['nativeToolSchema']+counts['native20Requests']+counts['native20Responses'];counts['explicitSchemaPlus20Roundtrips']=counts['explicitReferenceToolSchema']+counts['explicit20Requests']+counts['explicit20Responses'];report['tokenization']['encodings'][encoding]=counts
for p in [peer,ref]:p.close()
report['sourceHashes']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),R/'tests/standalone/invoice_reference.mjs',R/'docs/INTERFACE-TOKEN-FIXTURES.json']}
(R/'docs/CAPABILITY-MEASUREMENTS-0.7.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['summary','tokenization']},indent=2))
