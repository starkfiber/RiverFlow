"""Independent request oracle, unchanged-output failures and moved-target refusals."""
from pathlib import Path
import datetime,hashlib,itertools,json,os,random,subprocess,tempfile
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_REQUEST_COMPILER']).resolve();B=Path(os.environ['RF2_REQUEST_BASELINE']).resolve()
D=Path(tempfile.mkdtemp(prefix='typed-requests-',dir=R/'artifacts'));checks=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:(D/'FAILED.json').write_text(json.dumps(checks,indent=2)+'\n');raise AssertionError((name,detail,D))
def build(name,source,opt,compiler=C,refuse=None,place=None):
 root=place or D;path=root/(name+'.flow');path.write_text(source);exe=root/name
 q=subprocess.run([str(compiler),str(path),str(exe),'--compact',*(['--opt']if opt else[])],capture_output=True,timeout=30)
 text=(q.stdout+q.stderr).decode(errors='replace')
 if refuse:
  check(name+' refusal',q.returncode!=0 and refuse in text,text);check(name+' no image',not exe.exists());return
 check(name+' compile',q.returncode==0,text);subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],check=True,capture_output=True);return exe
HEADER='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext Name(IO,32)\nrecord Row(label:own Name,id:u64)\nrecord Outer(row:own Row,total:u64)\n'
for opt in(False,True):
 for nested,consume_parent,error in itertools.product((False,True),(False,True),(False,True)):
  if not nested and consume_parent:continue
  typ='Outer'if consume_parent else'Row';rhs='parent'if consume_parent else('parent.row'if nested else'row');target='parent.row.id'if nested else'row.id'
  own=' own parent=Outer(Row(Name(),7),11)'if nested else' own row=Row(Name(),7)'
  s=HEADER+'fn consume(own value:'+typ+'):IO\n return '+('err(73)'if error else'ok(9)')+'\nend\nfn work():IO\n'+own+'\n set '+target+'=try consume(move('+rhs+'))\n return ok(0)\nend\nfn main(argc,argv)\n handle work()\n ok done\n  return 0\n err cause\n  return cause\n end\n return 201\nend\n'
  name='ownership-'+str((opt,nested,consume_parent,error)).replace(' ','')
  baseline=build(name+'-old',s,opt,B)
  q=subprocess.run([str(baseline)],capture_output=True);check(name+' baseline admitted',q.returncode==(73 if error else 0),q.returncode)
  build(name+'-fixed',s,opt,refuse='assignment destination was consumed')

import sys
sys.path.insert(0,str(R/'experiments/typed-requests'))
from stage import stage
HARNESS='''profile RF2_SYSTEM_A64_V1
use "lib/booking-request.flow"
fn field(values:FormValues,key,p)
 set values[key*2]=p
 set values[key*2+1]=io_size(p)
 return 0
end
fn main(argc,argv)
 let values=FormValues()
 let request=StoreRequest(71,72,73,74,75,76,77)
 let out=Writer(buffer("request_test_json",256),256,0,0)
 let mask=0
 let status=0
 if argc!=9
  return 2
 end
 handle text_parse_u64(load64(argv+8),io_size(load64(argv+8)),18446744073709551615)
 ok bits
  set mask=bits
 err invalid_mask
  return 2
 end
 do field(values,1,load64(argv+16))
 do field(values,2,load64(argv+24))
 do field(values,7,load64(argv+32))
 do field(values,10,load64(argv+40))
 do field(values,3,load64(argv+48))
 do field(values,4,load64(argv+56))
 do field(values,5,load64(argv+64))
 handle booking_request(values,mask,request)
 ok complete
 err failure
  set status=failure
 end
 do writer_text(out,"[")
 do writer_number(out,status)
 do writer_text(out,",")
 do writer_number(out,request.action)
 do writer_text(out,",")
 do writer_number(out,request.expected)
 do writer_text(out,",")
 do writer_number(out,request.id)
 do writer_text(out,",")
 do writer_number(out,request.room)
 do writer_text(out,",")
 do writer_number(out,request.day)
 do writer_text(out,",")
 do writer_number(out,request.start)
 do writer_text(out,",")
 do writer_number(out,request.finish)
 do writer_text(out,"]\\n")
 handle io_write_all(1,out.data,out.used)
 ok sent
  return 0
 err write_error
  return write_error
 end
 return 201
end
'''
MAX=(1<<64)-1
def unsigned(text,maximum=MAX,positive=False):
 if not text or len(text)>20 or any(c not in'0123456789'for c in text)or(len(text)>1 and text[0]=='0'):raise ValueError()
 value=int(text)
 if value>maximum or(positive and value==0):raise ValueError()
 return value
def clock(text,end=False):
 if len(text)!=5 or text[2]!=':'or any(c not in'0123456789'for c in text[:2]+text[3:]):raise ValueError()
 h,m=int(text[:2]),int(text[3:])
 if m>59 or h>23:
  if not(end and h==24 and m==0):raise ValueError()
 return h*60+m
def expected(case):
 mask,rev,action,id,room,day,start,finish=case
 try:
  number=unsigned(rev);result=[0,0,number,0,0,0,0,0]
  if action=='reserve':
   if int(mask)!=1215:raise ValueError()
   if len(day)!=10 or day[4]!='-'or day[7]!='-':raise ValueError()
   date=datetime.datetime.strptime(day,'%Y-%m-%d').date()
   if date.strftime('%Y-%m-%d')!=day and date.year>=1000:raise ValueError()
   if any(c not in'0123456789-'for c in day):raise ValueError()
   begin,ending=clock(start),clock(finish,True)
   if begin>=ending:raise ValueError()
   result=[0,2,number,unsigned(id,positive=True),unsigned(room,16,True),date.toordinal(),begin,ending]
  elif action=='cancel':
   if int(mask)!=135:raise ValueError()
   result[1]=3;result[3]=unsigned(id,positive=True)
  else:
   if int(mask)!=7 or action not in('initialize','migrate','recover'):raise ValueError()
   result[1]={'initialize':1,'migrate':4,'recover':5}[action]
  return result
 except(ValueError,OverflowError):return [22,71,72,73,74,75,76,77]
base=['1215','2','reserve','7','3','2028-02-29','09:00','10:00']
cases=[base.copy()]
variants={0:['0','7','135','1214','1216',str(MAX)],1:['','0','01','-1','x',str(MAX),str(MAX+1)],2:['','Reserve','cancel','initialize','migrate','recover','unknown'],3:['','0','01','-1','x',str(MAX),str(MAX+1)],4:['','0','01','-1','17','x','16'],5:['2027-02-29','2028-2-29','0000-01-01','0001-01-01','9999-12-31','2000-02-29','1900-02-29','2028-04-31','２０２８-02-29'],6:['','24:00','09:60','9:00','00:00','23:59'],7:['','24:00','24:01','09:00','08:59','10:60']}
for index,values in variants.items():
 for value in values:case=base.copy();case[index]=value;cases.append(case)
for action,mask in [('cancel','135'),('initialize','7'),('migrate','7'),('recover','7')]:
 for rev in ['0','1',str(MAX),'01']:
  case=base.copy();case[:3]=[mask,rev,action];cases.append(case)
rng=random.Random(4901)
for i in range(80):
 day=datetime.date(2024+rng.randrange(8),1,1)+datetime.timedelta(days=rng.randrange(365));start=rng.randrange(1440);finish=rng.randrange(start+1,1441)
 case=['1215',str(rng.randrange(0,1<<64)),'reserve',str(rng.randrange(1,1<<64)),str(rng.randrange(1,17)),day.isoformat(),f'{start//60:02}:{start%60:02}',f'{finish//60:02}:{finish%60:02}'];cases.append(case)
for opt in(False,True):
 root=D/('sdk-opt'if opt else'sdk-plain');stage(root);exe=build('request-probe',HARNESS,opt,place=root)
 for i,case in enumerate(cases):
  q=subprocess.run([str(exe),*case],capture_output=True,timeout=5)
  try:actual=json.loads(q.stdout)
  except ValueError:actual=q.stdout.decode(errors='replace')
  check('request oracle '+str((opt,i)),q.returncode==0 and actual==expected(case),dict(input=case,actual=actual,expected=expected(case)))
report=dict(schema='rf2.typed-requests.native.v1',compilerSHA256=sha(C),baselineSHA256=sha(B),testSourceSHA256=sha(Path(__file__)),count=len(checks),allPassed=all(x['passed']for x in checks),requestCasesPerMode=len(cases),checks=checks)
(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(directory=str(D),count=len(checks),requestCasesPerMode=len(cases),allPassed=report['allPassed'])),flush=True)
