from pathlib import Path
import sys,os,json,hashlib
sys.path.insert(0,str(Path(__file__).parent))
from invoice_verify import Peer,value,expect
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_TEST_BINARY',str(R/'output/runtime-0.8-r1/rf2')))
def connect():
 p=Peer([B,'mcp']);p.request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'reuse-check','version':'1'}});p.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');p.p.stdin.flush();return p
p=connect();plan=(R/'capabilities/invoice.total.v1/quote.rf2').read_text();rows=[{'quantity':2,'unit_cents':1250}];report={'passed':False,'prepared':0,'applied':0,'refusals':0,'released':0}
assert len(p.request('tools/list',{})['result']['tools'])==9
ids=[]
for i in range(32):
 text=plan.replace('600',str(i)).replace('MYR','USD'if i%2 else'MYR');v=value(p.call('invoice_prepare',{'plan':text}));assert v['taxBps']==i;assert v['currency']==('USD'if i%2 else'MYR');assert v['plan_id']not in ids;ids.append(v['plan_id']);report['prepared']+=1
for i,handle in enumerate(ids):
 text=plan.replace('600',str(i)).replace('MYR','USD'if i%2 else'MYR');v=value(p.call('invoice_apply',{'plan_id':handle,'lines':rows}));assert v==expect(text,rows);report['applied']+=1
bad=[('invoice_prepare',{'plan':plan}),('invoice_prepare',{'plan':plan+' network'}),('invoice_apply',{'plan_id':0,'lines':rows}),('invoice_apply',{'plan_id':ids[0],'lines':rows,'tax_bps':0}),('invoice_apply',{'plan_id':ids[0],'lines':rows,'path':'/tmp/no'}),('invoice_apply',{'plan_id':ids[0]}),('invoice_release',{'plan_id':ids[0],'lines':[]}),('invoice_release',{}),('invoice_apply',{'plan_id':True,'lines':[]}),('invoice_prepare',{'plan':plan,'path':'x'})]
for name,args in bad:assert value(p.call(name,args))is None,(name,args);report['refusals']+=1
# Errors and unprepared calls must not change checked plans.
for i,h in enumerate(ids):assert value(p.call('invoice_apply',{'plan_id':h,'lines':rows}))['taxBps']==i;report['applied']+=1
for h in ids:
 assert value(p.call('invoice_release',{'plan_id':h}))=={'released':True};report['released']+=1
 assert value(p.call('invoice_apply',{'plan_id':h,'lines':rows}))is None;report['refusals']+=1
 assert value(p.call('invoice_release',{'plan_id':h}))is None;report['refusals']+=1
new=value(p.call('invoice_prepare',{'plan':plan}))['plan_id'];assert value(p.call('invoice_apply',{'plan_id':new,'lines':rows}))==expect(plan,rows);report['prepared']+=1;report['applied']+=1
# New process has no retained plan. A random handle is a locator, not access authentication.
q=connect();assert value(q.call('invoice_apply',{'plan_id':new,'lines':rows}))is None;report['refusals']+=1
q.close();p.close();report.update(passed=True,runtimeSHA256=hashlib.sha256(B.read_bytes()).hexdigest());(R/'docs/PREPARED-0.8-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
