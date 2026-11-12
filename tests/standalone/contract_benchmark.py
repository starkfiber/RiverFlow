"""Matched native reference-only / dual-validation overhead experiment.
No universal speed, energy, security or provider-token inference.
"""
from pathlib import Path
import subprocess,time,json,hashlib,random,statistics,struct
R=Path(__file__).resolve().parents[2];D=R/'artifacts/contract-next'/('benchmark-'+str(time.time_ns()));D.mkdir(parents=True)
C=R/'output/native-compiler/rf2c';engine=(R/'examples/evidence-contract/lib/engine.rf2').read_text().replace('module engine','profile RF2_SYSTEM_A64_V1',1)
cut=engine.index(' # Candidate:');reference=engine[:cut]+''' set i=0
 while i<n
  set data[i]=reference[i]
  set i=i+1
 end
 return 0
end
'''
rng=random.Random(14711);records=[]
for n,steps in [(8,1),(8,8),(8,32),(128,1),(128,8),(128,32)]:
 iterations=max(1000,2000000//(n*steps));ops=[(4,0)if j%3==1 else(2,(j*19+1)&255)for j in range(steps)]
 out=[]
 for label,src in [('reference-only',reference),('dual-validation',engine)]:
  setups='\n'.join(f' set codes[{j}]={code}\n set args[{j}]={arg}'for j,(code,arg)in enumerate(ops))
  probe=f'''
fn main(argc,argv)
 let data=Data()
 let codes=Ops()
 let args=Ops()
 let p=Plan({n},{steps},7,{2*n*steps})
 let r=Run(0,0,0,0,0,0)
 let i=0
 let j=0
 let acc=0
{setups}
 while j<{iterations}
  set i=0
  while i<{n}
   set data[i]=(i*17+j)&255
   set i=i+1
  end
  if execute(data,p,codes,args,r)!=0
   return 2
  end
  set acc=acc+data[j-(j//{n})*{n}]
  set j=j+1
 end
 let result=buffer("bench-result",32)
 do store64(result,acc)
 do store64(result+8,r.work)
 set i=0
 set acc=0
 while i<{n}
  set acc=acc+data[i]
  set i=i+1
 end
 do store64(result+16,acc)
 do store64(result+24,r.code)
 return write(1,result,32)!=32
end
'''
  source=D/f'{n}-{steps}-{label}.rf2';source.write_text(src+probe);exe=source.with_suffix('');p=subprocess.run([C,source,exe,'--opt'],capture_output=True,timeout=60);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',exe],check=True,capture_output=True)
  expected_acc=0;last=None
  for j in range(iterations):
   data=[(i*17+j)&255 for i in range(n)]
   for code,arg in ops:
    if code==4:data.reverse()
    else:data=[v^arg for v in data]
   expected_acc+=data[j%n];last=data
  expected=(expected_acc,n*steps*(2 if label=='dual-validation'else 1),sum(last),0)
  for _ in range(2):
   p=subprocess.run([exe],capture_output=True,check=True);assert struct.unpack('<4Q',p.stdout)==expected
  out.append({'name':label,'exe':exe,'expected':expected,'samples_ms':[],'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest()})
 for trial in range(21):
  order=list(out);rng.shuffle(order)
  for row in order:
   start=time.perf_counter_ns();p=subprocess.run([row['exe']],capture_output=True,check=True);elapsed=(time.perf_counter_ns()-start)/1e6;assert struct.unpack('<4Q',p.stdout)==row['expected'];row['samples_ms'].append(elapsed)
 for row in out:
  row['exe']=str(row['exe'].relative_to(R));row['median_ms']=statistics.median(row['samples_ms']);row['min_ms']=min(row['samples_ms']);row['max_ms']=max(row['samples_ms'])
 records.append({'bytes':n,'steps':steps,'iterations':iterations,'paths':out,'dual_over_reference_median':out[1]['median_ms']/out[0]['median_ms']})
 print(n,steps,records[-1]['dual_over_reference_median'],flush=True)
report={'target':'macOS ARM64','date':'2026-11-12','passed':True,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'engineSHA256':hashlib.sha256((R/'examples/evidence-contract/lib/engine.rf2').read_bytes()).hexdigest(),'trials':21,'warmups_per_path':2,'seed':14711,'records':records,'scope':'Native in-process repeated transforms with process startup included; equal input/output and checked reference semantics. Reference-only intentionally omits candidate execution/disagreement detection, so it provides fewer guarantees. Isolated benchmark code, not an unsafe production switch. No CLI parsing/hashing, no broad language comparison or token/energy measurement.'}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(D/'report.json')
