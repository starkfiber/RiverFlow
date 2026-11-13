"""Actual .flow native applications, independent integer oracles and shared modules."""
from pathlib import Path
import hashlib,json,os,random,shutil,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();D=R/'artifacts/collection-apps'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
ROOT=R/'examples/collection-tools';ROWS=[];IMAGES=[];rng=random.Random(330512);MASK=(1<<64)-1
SOURCES={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(ROOT.rglob('*'))if p.is_file()and p.suffix in ['.rf2','.flow']}
def run(args,data=b'',**kw):return subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=90,env={'PATH':'/nonexistent'},**kw)
def build(src,out,opt):
 q=run([C,src,out,'--compact',*(['--opt']if opt else[])]);assert q.returncode==0,(src,q.stderr)
 unsigned=hashlib.sha256(out.read_bytes()).hexdigest();q=run(['/usr/bin/codesign','-s','-',out]);assert q.returncode==0,q.stderr;return unsigned

def expected(app,values):
 ordered=sorted(values)
 if app=='telemetry-summary':
  assert values and sum(values)<=MASK
  return dict(count=len(values),minimum=ordered[0],maximum=ordered[-1],sum=sum(values),median_lower=ordered[(len(values)-1)//2])
 pairs=[]
 for value in ordered:
  if pairs and pairs[-1]['value']==value:pairs[-1]['count']+=1
  else:pairs.append(dict(value=value,count=1))
 return dict(count=len(values),unique=len(pairs),frequencies=pairs)

def encode(values,mode):
 sep=[b' ',b',',b'\n',b', \r\n'][mode];return sep.join(str(v).encode()for v in values)

def good(binary,app,values,data,label,opt):
 q=run([binary],data);assert q.returncode==0,(app,label,q.returncode,q.stderr[:300]);assert not q.stderr,(app,label,q.stderr);assert json.loads(q.stdout)==expected(app,values),(app,label,q.stdout[:600]);ROWS.append(dict(case=label,app=app,optimized=opt,values=len(values),inputBytes=len(data),inputSHA256=hashlib.sha256(data).hexdigest()))

def bad(binary,app,data,label,opt,exit=1):
 q=run([binary],data);assert q.returncode==exit and not q.stdout and q.stderr,(app,label,q.returncode,q.stdout[:100],q.stderr);ROWS.append(dict(case=label,app=app,optimized=opt,refused=True,inputBytes=len(data)))

for opt in [False,True]:
 for app in ['telemetry-summary','value-frequency']:
  binary=D/(app+'-'+str(opt));unsigned=build(ROOT/(app+'.flow'),binary,opt);IMAGES.append(dict(app=app,optimized=opt,binary=str(binary.relative_to(R)),unsignedSHA256=unsigned,signedSHA256=hashlib.sha256(binary.read_bytes()).hexdigest()))
  samples=[[0],[1],[1,2],[2,1],[3,1,3,2,0],[MASK]if app=='telemetry-summary'else[MASK,0,MASK,1]]
  for i in range(40):samples.append([rng.randrange(100000)for _ in range(rng.choice([1,2,7,16,17,31,32,65,257,1025]))])
  for i,values in enumerate(samples):good(binary,app,values,encode(values,i%4),'independent integer oracle '+str(i),opt)
  for count in [4097,16384,65536]:
   values=[(count-i)%1009 for i in range(count)];good(binary,app,values,encode(values,1),'actual growth beyond prior stack arena '+str(count),opt)
  for data in [b'1\n2\n',b'\t1 ,\r\n 2 \n',b'0,0,0']:
   values=[1,2]if data!=b'0,0,0'else[0,0,0];good(binary,app,values,data,'separator boundaries',opt)
  if app=='value-frequency':good(binary,app,[],b'','empty frequency table',opt);good(binary,app,[],b' \n\t','whitespace-only frequency table',opt)
  else:bad(binary,app,b'','empty summary refuses',opt);bad(binary,app,b' \n\t','whitespace-only summary refuses',opt);bad(binary,app,(str(MASK)+',1').encode(),'checked sum overflow',opt)
  for data in [b',1',b'1,',b'1,  ',b'1,,2',b'1 , ,2',b'01',b'00',b'-1',b'+1',b'1.0',b'1e2',b'12x',b'1\x002',b'1\xff',b'\v1',b'\f1',b'18446744073709551616']:
   bad(binary,app,data,'invalid canonical numeric input',opt)
  bad(binary,app,b'0,'*65536+b'0','collection limit overflow',opt)
  bad(binary,app,b' '*1048577,'stdin limit overflow',opt)
  q=run([binary,'unexpected']);assert q.returncode==2 and not q.stdout and q.stderr;ROWS.append(dict(case='unexpected argument refuses',app=app,optimized=opt))
  q=run([binary],preexec_fn=lambda:os.close(0));assert q.returncode==1 and not q.stdout and b'Error 3' in q.stderr;ROWS.append(dict(case='closed input descriptor refuses',app=app,optimized=opt))
  q=run([binary],b'1,2,3',preexec_fn=lambda:os.close(1));assert q.returncode==1 and b'Error 5'in q.stderr;ROWS.append(dict(case='closed output descriptor refuses',app=app,optimized=opt))
# One isolated shared module mutation must change both applications, not canonical source.
copy=D/'isolated';shutil.copytree(ROOT,copy);p=copy/'lib/numbers.rf2';s=p.read_text();assert s.count('return ok(values.length)')==1;s=s.replace('return ok(values.length)','return err(777)',1);p.write_text(s)
for app in ['telemetry-summary','value-frequency']:
 binary=D/(app+'-mutated-library');build(copy/(app+'.flow'),binary,True);q=run([binary],b'3,1,2');assert q.returncode==1 and not q.stdout and b'Error 777'in q.stderr,(app,q.returncode,q.stderr);ROWS.append(dict(case='one isolated shared parser mutation reaches both apps',app=app))
for name,h in SOURCES.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h,name
report=dict(passed=True,schema='rf2.collection.apps.verification.v1',cases=len(ROWS),rows=ROWS,images=IMAGES,sources=SOURCES,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sourceEntriesUseFlowExtension=True,oneCanonicalParserAndSortModule=True,maxValues=65536,maxInputBytes=1048576,limits='Actual bounded native CLI programs on one Apple Silicon Mac; supplied integer samples and independent Python sorting/frequency oracles. .flow filename acceptance is not an embedded/ESP32 target. No field observations, float precision, cross-platform, speed, energy, model-usage, general heap or full memory-safety claim. Standard output can be partial on output/fatal cleanup failures; signals/traps are outside ordinary cleanup.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),passed=True,cases=len(ROWS))))
