"""Runtime-input comparisons, including an equally specialised C baseline."""
from pathlib import Path
import subprocess,os,json,time,statistics,random,hashlib,platform
R=Path(__file__).resolve().parents[1];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c'));OLD=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/package/rf2-0.10.0/rf2c'));D=R/'artifacts'/os.environ.get('RF2_BENCH_RUN','performance-0.11-final');D.mkdir(exist_ok=False)
io=(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1];parse='''fn parse(text)
 let n=0
 let i=0
 while load8(text+i)!=0
 set n=n*10+load8(text+i)-48
 set i=i+1
 end
 return n
end
'''
main='''fn main(argc,argv)
 let a=parse(load64(argv+8))
 let b=parse(load64(argv+16))
 let c=parse(load64(argv+24))
 do io_number(kernel(a,b,c))
 do io_print("\\n")
 return 0
end
'''
bodies={'periodic':'set checksum=checksum+(i & 255)\nset i=i+1','mix':'set checksum=((checksum ^ i)*33+17)&4294967295\nset i=i+1','branches':'if (i&3)==0\nset checksum=checksum+7\nelse\nset checksum=checksum+(i&31)\nend\nset i=i+1'}
c_bodies={'periodic':'checksum += i & 255;','mix':'checksum=((checksum^i)*33+17)&4294967295ULL;','branches':'if((i&3)==0)checksum+=7;else checksum+=i&31;'}
report={'schema':'rf2.optimizer.measurements.v1','compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'baselineCompilerSHA256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'host':platform.platform(),'clang':subprocess.check_output(['/usr/bin/clang','--version'],text=True).splitlines()[0],'scope':'Runtime inputs for every variant; fresh-process wall time includes launch. Rotated matched trials. C -O3 -mcpu=native, plus equally specialised C formula. One host, uncontrolled system load; no universal performance or AI inference claim.','raw':[],'summary':[],'source':[]}
for name,body in bodies.items():
 source='profile RF2_SYSTEM_A64_V1\n'+io+parse+'fn kernel(start,bound,seed)\nlet i=start\nlet checksum=seed\nwhile i<bound\n'+body+'\nend\nreturn checksum\nend\n'+main;src=D/(name+'.rf2');src.write_text(source);variants={}
 for version,compiler in [('rf2-0.10',OLD),('rf2-0.11',C)]:
  out=D/(name+'-'+version);p=subprocess.run([compiler,src,out,'--opt'],capture_output=True);assert p.returncode==0,p.stderr;(D/(name+'-'+version+'-compile.txt')).write_bytes(p.stdout+p.stderr);subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);variants[version]=out
 csrc=D/(name+'.c');csrc.write_text('#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\nuint64_t kernel(uint64_t start,uint64_t bound,uint64_t checksum){for(uint64_t i=start;i<bound;i++){'+c_bodies[name]+'}return checksum;}\nint main(int argc,char**argv){uint64_t a=strtoull(argv[1],0,10),b=strtoull(argv[2],0,10),c=strtoull(argv[3],0,10);printf("%llu\\n",(unsigned long long)kernel(a,b,c));return 0;}\n')
 cout=D/(name+'-clang');cmd=['/usr/bin/clang','-O3','-mcpu=native','-Rpass=loop-vectorize','-Rpass-missed=loop-vectorize',str(csrc),'-o',str(cout)];p=subprocess.run(cmd,capture_output=True);assert p.returncode==0,p.stderr;(D/(name+'-clang-remarks.txt')).write_bytes(p.stderr);subprocess.run(['/usr/bin/clang','-O3','-mcpu=native','-S',str(csrc),'-o',str(D/(name+'-clang.s'))],check=True,capture_output=True);variants['clang-O3']=cout
 if name=='periodic':
  fsrc=D/'periodic-formula.c';fsrc.write_text(csrc.read_text().replace('for(uint64_t i=start;i<bound;i++){checksum += i & 255;}return checksum;','if(start<bound){uint64_t r=bound&255,s=start&255;checksum+=(bound>>8)*32640+((r*(r-1))>>1)-(start>>8)*32640-((s*(s-1))>>1);}return checksum;'));fout=D/'periodic-clang-formula';subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',fsrc,'-o',fout],check=True,capture_output=True);variants['clang-formula-O3']=fout
 for n in [1000,2000000,20000000]:
  a=17;nend=n+a;seed=987654321
  if name=='periodic':
   def f(x):q,r=divmod(x,256);return q*32640+r*(r-1)//2
   expected=seed+f(nend)-f(a)
  else:
   expected=seed
   for i in range(a,nend):
    expected=((expected^i)*33+17)&4294967295 if name=='mix' else expected+(7 if i&3==0 else i&31)
  expected&=(1<<64)-1;times={v:[]for v in variants}
  for version,path in variants.items():
   cold_start=time.perf_counter_ns();p=subprocess.run([path,str(a),str(nend),str(seed)],capture_output=True);assert p.returncode==0 and int(p.stdout)==expected;report['raw'].append({'kernel':name,'iterations':n,'variant':version,'coldOrWarmupMs':(time.perf_counter_ns()-cold_start)/1e6,'excludedFromMedian':True})
  for trial in range(7):
   order=list(variants);random.Random(trial+101).shuffle(order)
   for version in order:
    start=time.perf_counter_ns();p=subprocess.run([variants[version],str(a),str(nend),str(seed)],capture_output=True);elapsed=(time.perf_counter_ns()-start)/1e6;assert p.returncode==0 and int(p.stdout)==expected,(name,version,p.returncode,p.stdout,expected);times[version].append(elapsed);report['raw'].append({'kernel':name,'iterations':n,'start':a,'bound':nend,'seed':seed,'trial':trial,'variant':version,'ms':elapsed,'expected':expected})
  report['summary'].append({'kernel':name,'iterations':n,'medianMs':{v:statistics.median(x)for v,x in times.items()},'minMs':{v:min(x)for v,x in times.items()},'maxMs':{v:max(x)for v,x in times.items()}})
 report['source'] += [{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in [src,csrc]]
(R/'docs/OPTIMIZER-MEASUREMENTS-0.11.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
