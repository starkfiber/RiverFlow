"""Compare the guarded conditional reduction with prior RF2 and matched Clang baselines."""
from pathlib import Path
import subprocess,time,json,hashlib,statistics,random,os,platform
R=Path(__file__).resolve().parents[1];D=R/'artifacts'/os.environ.get('RF2_BENCH_RUN','conditional-performance');D.mkdir(exist_ok=False);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-0.12-corrected'));OLD=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/rf2c-0.11-final'));variants={};report={'schema':'rf2.conditional.measurements.v1','host':platform.platform(),'clang':subprocess.check_output(['/usr/bin/clang','--version'],text=True).splitlines()[0],'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'baselineCompilerSHA256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'scope':'Identical runtime inputs; seven rotated process trials after separately retained cold/warmup. Wall time includes process launch on one uncontrolled Mac. Clang loop, scalar-only loop and equally specialized closed form retained. No energy, token, full-stack or universal speed claim.','raw':[],'summary':[],'compileRaw':[]}
src=D/'conditional.rf2';src.write_text((R/'examples/systems/conditional-sum.rf2').read_text())
for name,c in [('rf2-0.11',OLD),('rf2-candidate',C)]:
 out=D/name;p=subprocess.run([c,src,out,'--opt'],capture_output=True);assert p.returncode==0,p.stderr;(D/(name+'-compile.txt')).write_bytes(p.stderr);subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);variants[name]=out
 # Repeated compiler execution uses fresh output paths; no signing time in this series.
 for j in range(5):
  t=time.perf_counter_ns();p=subprocess.run([c,src,D/(name+f'-build-{j}'),'--opt'],capture_output=True);assert p.returncode==0;report['compileRaw'].append({'variant':name,'trial':j,'ms':(time.perf_counter_ns()-t)/1e6})
csrc=D/'conditional.c';csrc.write_text('#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\nuint64_t kernel(uint64_t start,uint64_t bound,uint64_t checksum){for(uint64_t i=start;i<bound;i++){if((i&3)==0)checksum+=7;else checksum+=i&31;}return checksum;}\nint main(int argc,char**argv){uint64_t a=strtoull(argv[1],0,10),b=strtoull(argv[2],0,10),c=strtoull(argv[3],0,10);printf("%llu\\n",(unsigned long long)kernel(a,b,c));return 0;}\n')
for name,flags in [('clang-O3',[]),('clang-scalar',['-fno-vectorize','-fno-slp-vectorize'])]:
 out=D/name;p=subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',*flags,'-Rpass=loop-vectorize','-Rpass-missed=loop-vectorize',csrc,'-o',out],capture_output=True);assert p.returncode==0,p.stderr;(D/(name+'-remarks.txt')).write_bytes(p.stderr);variants[name]=out
formula=D/'formula.c';s=csrc.read_text();start=s.index('for(uint64_t i=start;');end=s.index('return checksum;',start)
s=s[:start]+'if(start<bound){checksum+=prefix(bound)-prefix(start);}'+s[end:]
helper='uint64_t base(uint64_t n,uint64_t p){uint64_t r=n%p;return(n/p)*(p*(p-1)/2)+(r*(r-1))/2;}\nuint64_t prefix(uint64_t n){uint64_t m=(n>>2)+((n&3)!=0);return base(n,32)+m*7-4*base(m,8);}\n'
s=s.replace('uint64_t kernel(',helper+'uint64_t kernel(');formula.write_text(s);out=D/'clang-formula';subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',formula,'-o',out],check=True,capture_output=True);variants['clang-formula']=out
for n in [1000,2000000,20000000]:
 a=17;b=a+n;seed=987654321;expected=seed+sum(7 if(i&3)==0 else i&31 for i in range(a,b));times={v:[]for v in variants}
 for name,path in variants.items():
  t=time.perf_counter_ns();p=subprocess.run([path,str(a),str(b),str(seed)],capture_output=True);assert p.returncode==0 and int(p.stdout)==expected;report['raw'].append({'variant':name,'iterations':n,'coldOrWarmupMs':(time.perf_counter_ns()-t)/1e6,'excludedFromMedian':True})
 for j in range(7):
  order=list(variants);random.Random(1200+j).shuffle(order)
  for name in order:
   t=time.perf_counter_ns();p=subprocess.run([variants[name],str(a),str(b),str(seed)],capture_output=True);dt=(time.perf_counter_ns()-t)/1e6;assert p.returncode==0 and int(p.stdout)==expected;times[name].append(dt);report['raw'].append({'variant':name,'iterations':n,'trial':j,'start':a,'bound':b,'seed':seed,'expected':expected,'ms':dt})
 report['summary'].append({'iterations':n,'medianMs':{v:statistics.median(t)for v,t in times.items()},'minMs':{v:min(t)for v,t in times.items()},'maxMs':{v:max(t)for v,t in times.items()}})
report['artifacts']=[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in [src,csrc,formula,*variants.values()]]
(R/'docs/CONDITIONAL-REDUCTION-MEASUREMENTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
