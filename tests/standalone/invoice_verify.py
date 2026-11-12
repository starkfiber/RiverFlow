"""Native application conformance; Node/Python are development oracles only."""
from pathlib import Path
import subprocess,json,os,random,select,atexit,hashlib,tempfile
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_TEST_BINARY',str(R/'output/runtime-0.7-r2/rf2')));OLD=Path(os.environ.get('RF2_BASELINE_BINARY',str(R/'output/package/rf2-0.6.0/rf2')));NODE='/opt/homebrew/opt/node@22/bin/node'
class Peer:
 def __init__(self,cmd):
  self.p=subprocess.Popen([str(x)for x in cmd],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/nonexistent'});self.i=0;atexit.register(self.close)
 def request(self,method,params):
  self.i+=1;q={'jsonrpc':'2.0','id':self.i,'method':method,'params':params};self.p.stdin.write(json.dumps(q,separators=(',',':')).encode()+b'\n');self.p.stdin.flush();assert select.select([self.p.stdout],[],[],10)[0],'response timeout';a=json.loads(self.p.stdout.readline());assert a['id']==self.i;return a
 def call(self,name,args):return self.request('tools/call',{'name':name,'arguments':args})
 def close(self):
  if self.p.poll()is None:self.p.stdin.close();self.p.wait(timeout=5)
def value(a):return a.get('result',{}).get('structuredContent')if not a.get('result',{}).get('isError')else None
def expect(plan,lines):
 if not isinstance(lines,list)or len(lines)>1000:raise ValueError()
 w=plan.split();rate=int(w[8]);sub=0
 for x in lines:
  if type(x)is not dict or set(x)!={'quantity','unit_cents'}or type(x['quantity'])is not int or type(x['unit_cents'])is not int or not 1<=x['quantity']<=4294967295 or not 0<=x['unit_cents']<=4294967295:raise ValueError()
  amount=x['quantity']*x['unit_cents'];sub+=amount
  if amount>4294967295 or sub>4294967295:raise ValueError()
 tax=(sub*rate+5000)//10000
 if sub+tax>4294967295:raise ValueError()
 return dict(capability='invoice.total@1',currency=w[6],lineCount=len(lines),subtotalCents=sub,taxBps=rate,taxCents=tax,totalCents=sub+tax)
def main():
 native=Peer([B,'mcp']);old=Peer([OLD,'mcp']);js=Peer([NODE,R/'tests/standalone/invoice_reference.mjs']);plan=(R/'capabilities/invoice.total.v1/quote.rf2').read_text();core=(R/'capabilities/invoice.total.v1/total.flow').read_text();rng=random.Random(2026111207)
 report={'schema':'rf2.invoice.verification.v1','passed':False,'validComparisons':0,'oldCoreComparisons':0,'refusals':0,'planMutations':0,'cliCases':0,'scope':'Programming fixtures, not customer transactions or tax compliance evidence'}
 for peer in [native,old]:
  peer.request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'invoice-check','version':'1'}})
  peer.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');peer.p.stdin.flush()
 tools=native.request('tools/list',{})['result']['tools'];assert len(tools)==int(os.environ.get('RF2_TEST_TOOLS','6')) and tools[5]['name']=='invoice_total'
 cases=[[],[{'quantity':2,'unit_cents':1250},{'quantity':1,'unit_cents':399}],[{'quantity':1,'unit_cents':4294967295}]]
 for n in [1,2,17,256,1000]:cases.append([{'quantity':rng.randrange(1,20),'unit_cents':rng.randrange(0,10000)}for _ in range(n)])
 for _ in range(100):cases.append([{'quantity':rng.randrange(1,100),'unit_cents':rng.randrange(0,100000)}for _ in range(rng.randrange(0,20))])
 for lines in cases:
  for rate in [0,1,500,600,10000]:
   text=plan.replace('600',str(rate));args={'plan':text,'lines':lines}
   try:e=expect(text,lines)
   except ValueError:e=None
   a=value(native.call('invoice_total',args));b=value(js.call('invoice_total',args));assert a==b==e,(args,a,b,e)
   if e is not None:report['validComparisons']+=1
   else:report['refusals']+=1
  flat=[v for x in lines for v in [x['quantity'],x['unit_cents']]]
  a=value(old.call('rf2_run',{'source':core,'data':flat,'count':len(lines)}));b=value(native.call('rf2_run',{'source':core,'data':flat,'count':len(lines)}));assert a==b,(a,b)
  assert a['value']==sum(x['quantity']*x['unit_cents']for x in lines);report['oldCoreComparisons']+=1
 # Exhaust rounding boundaries, including ties; tax applies once at invoice level.
 for cents in [0,1,49,50,51,99,100,101,4999,5000,5001,10000,2147483647]:
  for rate in [0,1,50,100,600,5000,10000]:
   text=plan.replace('600',str(rate));lines=[{'quantity':1,'unit_cents':cents}];e=expect(text,lines);assert value(native.call('invoice_total',{'plan':text,'lines':lines}))==value(js.call('invoice_total',{'plan':text,'lines':lines}))==e;report['validComparisons']+=1
 badlines=[None,{},[None],[{}],[{'quantity':True,'unit_cents':1}],[{'quantity':0,'unit_cents':1}],[{'quantity':-1,'unit_cents':1}],[{'quantity':1.5,'unit_cents':1}],[{'quantity':1,'unit_cents':-1}],[{'quantity':1,'unit_cents':'1'}],[{'quantity':1,'unit_cents':1,'discount':1}],[{'quantity':4294967296,'unit_cents':0}],[{'quantity':2,'unit_cents':4294967295}],[{'quantity':1,'unit_cents':4294967295},{'quantity':1,'unit_cents':1}],[{'quantity':1,'unit_cents':0}]*1001]
 for lines in badlines:
  args={'plan':plan,'lines':lines};assert value(native.call('invoice_total',args))is None and value(js.call('invoice_total',args))is None;report['refusals']+=1
 badplans=['',plan+'allow network',plan.replace('MYR','myr'),plan.replace('v1','v2'),plan.replace('invoice','attendance'),plan.replace('600','0600'),plan.replace('600','-1'),plan.replace('600','1.5'),plan.replace('600','10001'),plan.replace('600','1e2'),plan.replace('bps','percent'),plan.replace('\n','\u00a0'),plan+' '*257,plan.replace('MYR','USD;'),plan.replace('tax','TAX')]
 for text in badplans:
  args={'plan':text,'lines':[]};assert value(native.call('invoice_total',args))is None and value(js.call('invoice_total',args))is None,(repr(text),native.call('invoice_total',args));report['refusals']+=1
 for text in [' \t'+plan+'\r\n',plan.replace('\n','\r\n'),plan.replace('MYR','USD')]:assert value(native.call('invoice_total',{'plan':text,'lines':[]}))==expect(text,[]);report['validComparisons']+=1
 for _ in range(200):
  text=list(plan);at=rng.randrange(len(text));text[at]=chr(rng.randrange(32,127));text=''.join(text)
  a=value(native.call('invoice_total',{'plan':text,'lines':[]}));b=value(js.call('invoice_total',{'plan':text,'lines':[]}));assert a==b,(repr(text),a,b);report['planMutations']+=1
 for args in [{'plan':plan,'lines':[],'path':'/tmp/nope'},{'plan':plan},{'plan':None,'lines':[]},{'plan':plan,'lines':[],'allow_write':True}]:assert value(native.call('invoice_total',args))is None;report['refusals']+=1
 # Actual strict JSON transport refuses duplicate keys and recovers.
 native.p.stdin.write(b'{"jsonrpc":"2.0","id":999999,"method":"tools/call","params":{"name":"invoice_total","arguments":{"plan":"x","plan":"y","lines":[]}}}\n');native.p.stdin.flush();assert json.loads(native.p.stdout.readline()).get('error');report['refusals']+=1
 assert value(native.call('invoice_total',{'plan':plan,'lines':[]}))==expect(plan,[])
 assert value(native.call('attendance_export',{'records':[]}))['records']==0
 with tempfile.TemporaryDirectory(prefix='rf2-invoice-')as d:
  root=Path(d);p=root/'plan.rf2';f=root/'lines.json';p.write_text(plan);lines=[{'quantity':2,'unit_cents':1250}];f.write_text(json.dumps(lines));r=subprocess.run([B,'app',p,f],capture_output=True,env={'PATH':'/nonexistent'});assert r.returncode==0 and json.loads(r.stdout)==expect(plan,lines);assert sorted(x.name for x in root.iterdir())==['lines.json','plan.rf2'];report['cliCases']+=1
  for payload in [b'[{"quantity":1,"unit_cents":1,"unit_cents":2}]',b'null',b'['+b' '*1048576+b']']:
   f.write_bytes(payload);r=subprocess.run([B,'app',p,f],capture_output=True);assert r.returncode==1;report['cliCases']+=1
  f.write_text('[]');p.write_bytes(plan.encode()+b'\xff');assert subprocess.run([B,'app',p,f],capture_output=True).returncode==1;report['cliCases']+=1
 for p in [native,old,js]:p.close();assert p.p.returncode==0 and not p.p.stderr.read()
 generated=subprocess.check_output([OLD,'lower',R/'capabilities/invoice.total.v1/total.flow']).decode().replace('cgn_','ivg_').replace('c_f','iv_f').replace('"generated_','"invoice_generated_');assert generated==(R/'native/invoice-kernel.rf2').read_text()
 report.update(passed=True,runtimeSHA256=hashlib.sha256(B.read_bytes()).hexdigest(),baseline06SHA256=hashlib.sha256(OLD.read_bytes()).hexdigest(),kernelReproduction=True,sourceSHA256=hashlib.sha256(core.encode()).hexdigest(),kernelSHA256=hashlib.sha256(generated.encode()).hexdigest());Path(os.environ.get('RF2_TEST_REPORT',str(R/'docs/INVOICE-VERIFICATION.json'))).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
