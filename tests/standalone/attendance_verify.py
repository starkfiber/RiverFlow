from pathlib import Path
import subprocess,json,os,random,csv,io,hashlib,tempfile,select,atexit,datetime,stat
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_TEST_BINARY',str(R/'output/core-0.6-r6/rf2')));root=R/'output/attendance-0.6';root.mkdir(exist_ok=True);work=Path(tempfile.mkdtemp(prefix='run-',dir=root));p=subprocess.Popen([str(B),'mcp'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);atexit.register(lambda:p.kill()if p.poll()is None else None)
i=0
report={'schema':'rf2.attendance.verification.v1','successfulExports':0,'recordsChecked':0,'refusals':0,'fileProtectionCases':0,'passed':False,'dataScope':'Explicit fictional TEST identifiers used only as test inputs; no student or workplace study','speedClaim':None,'tokenClaim':None}
def rpc(method,params=None):
 global i;i+=1;v={'jsonrpc':'2.0','id':i,'method':method}
 if params is not None:v['params']=params
 p.stdin.write(json.dumps(v,separators=(',',':')).encode()+b'\n');p.stdin.flush();assert select.select([p.stdout],[],[],10)[0];ans=json.loads(p.stdout.readline());assert ans['id']==i;return ans
rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'attendance-test','version':'1'}});p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');p.stdin.flush()
def export(rows):return rpc('tools/call',{'name':'attendance_export','arguments':{'records':rows}})
def valid(rows):
 ans=export(rows);assert 'result'in ans and not ans['result'].get('isError'),ans;v=ans['result']['structuredContent'];assert v['records']==len(rows)
 for status in ['present','absent','late']:assert v[status]==sum(x['status']==status for x in rows)
 data=v['csv'].encode();assert len(data)==v['csvBytes'];assert hashlib.sha256(data).hexdigest()==v['csvSHA256'];assert list(csv.DictReader(io.StringIO(v['csv'])))==rows
 report['successfulExports']+=1;report['recordsChecked']+=len(rows);return v
rng=random.Random(20261112)
valid([])
for n in [1,3,39,1000]:
 rows=[{'student_id':f'TEST{x:04d}','date':(datetime.date(2024,2,1)+datetime.timedelta(days=x%30)).isoformat(),'status':rng.choice(['present','absent','late'])}for x in range(n)];valid(rows)
rows=[{'student_id':'TEST001','date':'2024-02-29','status':'present'},{'student_id':'TEST001','date':'2024-03-01','status':'late'}];valid(rows)
base={'student_id':'TEST001','date':'2026-11-12','status':'present'}
bad=[None,{},[None],[{}],[dict(base,extra=1)],[dict(base,student_id='=SUM(1)')],[dict(base,student_id='@BAD')],[dict(base,student_id='-BAD')],[dict(base,student_id='TEST,1')],[dict(base,student_id='TEST\n1')],[dict(base,student_id='தமிழ்')],[dict(base,student_id='x'*65)],[dict(base,status='Present')],[dict(base,date='2026-02-29')],[dict(base,date='1900-02-29')],[dict(base,date='2026-04-31')],[dict(base,date='2026-13-01')],[dict(base,date='0000-01-01')],[dict(base,date='2026-1-01')],[dict(base,date='2026-01-01,')],[base,base],[base]*1001]
for rows in bad:
 ans=export(rows);assert 'error'in ans or ans['result'].get('isError'),ans;report['refusals']+=1
for args in [{'records':[],'path':'/tmp/should-not-exist'},{'records':[],'allow_file_write':True}]:assert 'error'in rpc('tools/call',{'name':'attendance_export','arguments':args});report['refusals']+=1
# Calendar classification compared with Python's independent Gregorian implementation.
for year in [1,1900,2000,2024,2026,2100,2400,9999]:
 for month,day in [(2,28),(2,29),(2,30),(4,30),(4,31),(12,31)]:
  row=dict(base,date=f'{year:04d}-{month:02d}-{day:02d}')
  try:datetime.date(year,month,day);ok=True
  except ValueError:ok=False
  ans=export([row]);actual='result'in ans and not ans['result'].get('isError');assert actual==ok,(row,ans)
  if ok:report['successfulExports']+=1;report['recordsChecked']+=1
  else:report['refusals']+=1
v=valid([base]);src=work/'records.json';src.write_text(json.dumps([base]));out=work/'attendance.csv';r=subprocess.run([str(B),'attendance',str(src),str(out)],capture_output=True,text=True,env={'PATH':'/nonexistent'},check=True);assert out.read_bytes()==v['csv'].encode();receipt=json.loads(r.stdout);assert receipt['csvSHA256']==hashlib.sha256(out.read_bytes()).hexdigest();assert stat.S_IMODE(out.stat().st_mode)==0o600
before=out.read_bytes();r=subprocess.run([str(B),'attendance',str(src),str(out)],capture_output=True);assert r.returncode==1 and out.read_bytes()==before;report['fileProtectionCases']+=1
link=work/'link.csv';link.symlink_to(out);r=subprocess.run([str(B),'attendance',str(src),str(link)],capture_output=True);assert r.returncode==1 and out.read_bytes()==before;report['fileProtectionCases']+=1
src.write_text(json.dumps([base,base]));target=work/'invalid.csv';r=subprocess.run([str(B),'attendance',str(src),str(target)],capture_output=True);assert r.returncode==1 and not target.exists();report['fileProtectionCases']+=1
# Core execution and lower-source requests still work after an application refusal.
ans=rpc('tools/call',{'name':'rf2_run','arguments':{'source':(R/'examples/sum.flow').read_text(),'data':[1,2,3]}});assert ans['result']['structuredContent']['value']==6
ans=rpc('tools/call',{'name':'rf2_lower','arguments':{'source':(R/'examples/sum.flow').read_text()}});assert 'fn cgn_entry'in ans['result']['content'][0]['text']
p.stdin.close();p.wait(timeout=5);assert p.returncode==0;assert not p.stderr.read();report.update(passed=True,runtimeSHA256=hashlib.sha256(B.read_bytes()).hexdigest(),tallySourceSHA256=hashlib.sha256((R/'capabilities/attendance.local.v1/tally.flow').read_bytes()).hexdigest(),compiledKernelSourceSHA256=hashlib.sha256((R/'native/attendance-kernel.rf2').read_bytes()).hexdigest());Path(os.environ.get('RF2_TEST_REPORT',str(R/'docs/ATTENDANCE-VERIFICATION.json'))).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
