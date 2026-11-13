"""Fresh matched programs, retained losses and raw trials; no whole-language/AI claim."""
from pathlib import Path
import subprocess,os,time,json,hashlib,statistics,random,platform,sys
R=Path(__file__).resolve().parents[1];D=R/'artifacts/mappings-0.21'/('bench-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/mappings-0.21-qualified/rf2c-self'));OLD=R/'output/ownership-0.20-final/rf2c-self';report={'passed':False,'host':platform.platform(),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'baselineCompilerSHA256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'pythonVersion':sys.version,'clang':subprocess.check_output(['/usr/bin/clang','--version'],text=True).splitlines()[0],'trials':9,'raw':[],'summary':[],'scope':'Fresh-process end-to-end wall time including startup/IO for four bounded tasks, rotated order, one uncontrolled Mac. Algorithm/library differences named explicitly. No AI model calls, bills, token, energy or universal language-speed claim.'}
def native(src,name,compiler=C):
 path=D/(name+'.rf2');path.write_text(src);out=D/name;subprocess.run([compiler,path,out,'--opt'],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);return[str(out)]
def cbuild(src,name):
 path=D/(name+'.c');path.write_text(src);out=D/name;subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',path,'-o',out],check=True,capture_output=True);return[str(out)]
def pybuild(src,name):
 p=D/(name+'.py');p.write_text(src);return[sys.executable,str(p)]
def measure(task,variants,expected,detail):
 times={k:[]for k in variants}
 for key,cmd in variants.items():
  t=time.perf_counter_ns();p=subprocess.run(cmd,capture_output=True,timeout=20);dt=(time.perf_counter_ns()-t)/1e6;assert p.returncode==0 and p.stdout==expected,(task,key,p.returncode,p.stdout[:100],expected[:100],p.stderr);report['raw'].append({'task':task,'variant':key,'excludedWarmupMs':dt})
 for trial in range(9):
  order=list(variants);random.Random(2100+trial).shuffle(order)
  for key in order:
   t=time.perf_counter_ns();p=subprocess.run(variants[key],capture_output=True,timeout=20);dt=(time.perf_counter_ns()-t)/1e6;assert p.returncode==0 and p.stdout==expected,(task,key,p.returncode);times[key].append(dt);report['raw'].append({'task':task,'trial':trial,'variant':key,'ms':dt})
 report['summary'].append({'task':task,'detail':detail,'medianMs':{k:statistics.median(v)for k,v in times.items()},'minMs':{k:min(v)for k,v in times.items()},'maxMs':{k:max(v)for k,v in times.items()}})
io=(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1];parse='fn parse(p)\n let n=0\n let i=0\n while load8(p+i)\n  set n=n*10+load8(p+i)-48\n  set i=i+1\n end\n return n\nend\n';main='fn main(argc,argv)\n do io_number(kernel(parse(load64(argv+8)),parse(load64(argv+16)),parse(load64(argv+24))))\n do io_print("\\n")\n return 0\nend\n'
bodies={'mixed':'set checksum=((checksum^i)*33+17)&4294967295','conditional':'if (i&3)==0\n set checksum=checksum+7\nelse\n set checksum=checksum+(i&31)\nend'}
for name,body in bodies.items():
 n=2000000 if name=='mixed' else 20000000;a=17;b=a+n;seed=987654321;args=list(map(str,[a,b,seed]));src='profile RF2_SYSTEM_A64_V1\n'+io+parse+'fn kernel(start,bound,checksum)\n let i=start\n while i<bound\n '+body+'\n set i=i+1\n end\n return checksum\nend\n'+main
 v={'RF2 0.21':native(src,name+'-rf2')+args,'RF2 0.20':native(src,name+'-old',OLD)+args}
 cbody='checksum=((checksum^i)*33+17)&4294967295ULL;'if name=='mixed'else'if((i&3)==0)checksum+=7;else checksum+=i&31;'
 csrc='#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\nuint64_t kernel(uint64_t a,uint64_t b,uint64_t checksum){for(uint64_t i=a;i<b;i++){'+cbody+'}return checksum;}\nint main(int c,char**v){printf("%llu\\n",(unsigned long long)kernel(strtoull(v[1],0,10),strtoull(v[2],0,10),strtoull(v[3],0,10)));}\n';v['Clang O3 loop']=cbuild(csrc,name+'-clang')+args
 if name=='conditional':
  def prefix(n):m=(n+3)//4;return n//32*496+(n%32)*(n%32-1)//2+m*7-4*(m//8*28+(m%8)*(m%8-1)//2)
  expected=seed+prefix(b)-prefix(a)
  formula='uint64_t base(uint64_t n,uint64_t p){uint64_t r=n%p;return(n/p)*(p*(p-1)/2)+(r*(r-1))/2;}uint64_t prefix(uint64_t n){uint64_t m=(n>>2)+((n&3)!=0);return base(n,32)+m*7-4*base(m,8);}';cformula=csrc.replace('uint64_t kernel(',formula+'uint64_t kernel(').replace('for(uint64_t i=a;i<b;i++){'+cbody+'}','if(a<b)checksum+=prefix(b)-prefix(a);');v['Clang O3 formula']=cbuild(cformula,name+'-formula')+args
  pysrc='import sys\na,b,s=map(int,sys.argv[1:])\ndef base(n,p):\n q,r=divmod(n,p);return q*(p*(p-1)//2)+r*(r-1)//2\ndef f(n):\n m=(n+3)//4;return base(n,32)+m*7-4*base(m,8)\nprint(s+f(b)-f(a))\n';label='Python formula'
 else:
  expected=seed
  for i in range(a,b):expected=((expected^i)*33+17)&4294967295
  pysrc='import sys\na,b,s=map(int,sys.argv[1:])\nfor i in range(a,b):s=((s^i)*33+17)&4294967295\nprint(s)\n';label='Python loop'
 v[label]=pybuild(pysrc,name+'-python')+args;measure(name,v,(str(expected)+'\n').encode(),{'iterations':n,'a':a,'b':b,'seed':seed,'formulaComparator':name=='conditional','classification':'numeric kernel, not a whole application'})
# Real CLI latency-summary application with parsing, sort and JSON output.
args=[str((i*7919)%100000)for i in range(128)];values=list(map(int,args));ordered=sorted(values);expected={'count':128,'min':ordered[0],'max':ordered[-1],'sum':sum(values),'median_lower':ordered[63],'p95_nearest_rank':ordered[121]};out=D/'latency-rf2';subprocess.run([C,R/'examples/latency/main.rf2',out,'--opt'],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
pysrc='import sys,json\nv=sorted(map(int,sys.argv[1:]));n=len(v);print(json.dumps(dict(count=n,min=v[0],max=v[-1],sum=sum(v),median_lower=v[(n-1)//2],p95_nearest_rank=v[(n*95+99)//100-1]),separators=(",",":")))\n'
# Exact valid-input C output matches RF2. qsort differs from RF2 insertion sort.
csrc='#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\nint cmp(const void*a,const void*b){uint64_t x=*(uint64_t*)a,y=*(uint64_t*)b;return(x>y)-(x<y);}\nint main(int c,char**a){uint64_t v[128],s=0;int n=c-1;for(int i=0;i<n;i++){v[i]=strtoull(a[i+1],0,10);s+=v[i];}qsort(v,n,8,cmp);printf("{\\"count\\":%d,\\"min\\":%llu,\\"max\\":%llu,\\"sum\\":%llu,\\"median_lower\\":%llu,\\"p95_nearest_rank\\":%llu}\\n",n,(unsigned long long)v[0],(unsigned long long)v[n-1],(unsigned long long)s,(unsigned long long)v[(n-1)/2],(unsigned long long)v[(n*95+99)/100-1]);}\n'
v={'RF2 0.21':[str(out),*args],'Clang O3 qsort':cbuild(csrc,'sort-clang')+args,'Python built-in sort':pybuild(pysrc,'sort-python')+args};measure('latency-summary',v,(json.dumps(expected,separators=(',',':'))+'\n').encode(),{'count':128,'classification':'whole bounded CLI application; different sorting libraries; valid-input comparison only'})
# File SHA-256: RF2 implementation versus optimized C/Python libraries, same exact bytes.
fixture=D/'payload.bin';fixture.write_bytes(bytes(range(256))*128);sha=(R/'examples/evidence-contract/lib/sha256.rf2').read_text().split('\n',1)[1];src='profile RF2_SYSTEM_A64_V1\n'+sha+'\nfn main(argc,argv)\n let data=buffer("input",32769)\n let fd=open(load64(argv+8),0,0)\n if fd>>63\n  return 1\n end\n let n=0\n let got=1\n while got\n  set got=read(fd,data+n,32769-n)\n  if got>>63\n   do close(fd)\n   return 1\n  end\n  set n=n+got\n  if n>32768\n   do close(fd)\n   return 1\n  end\n end\n do close(fd)\n do write(1,sha256(data,n),32)\n return 0\nend\n'
pysrc='import sys,hashlib\nsys.stdout.buffer.write(hashlib.sha256(open(sys.argv[1],"rb").read()).digest())\n';csrc='#include <stdio.h>\n#include <CommonCrypto/CommonDigest.h>\nint main(int c,char**v){unsigned char d[32769],h[32];FILE*f=fopen(v[1],"rb");if(!f)return 1;size_t n=fread(d,1,sizeof d,f);fclose(f);if(n>32768)return 1;CC_SHA256(d,(CC_LONG)n,h);fwrite(h,1,32,stdout);}\n';v={'RF2 0.21':native(src,'sha-rf2')+[str(fixture)],'Clang/CommonCrypto':cbuild(csrc,'sha-clang')+[str(fixture)],'Python/hashlib':pybuild(pysrc,'sha-python')+[str(fixture)]};measure('file-sha256-32KiB',v,hashlib.sha256(fixture.read_bytes()).digest(),{'bytes':32768,'classification':'whole file digest CLI; optimized library baselines, not identical SHA implementation'})
# Batch50 varies the first byte per hash, amortizing process startup without subtracting it.
bsrc=src.replace(' do write(1,sha256(data,n),32)',' let j=0\n let total=0\n while j<50\n  do store8(data,j&255)\n  set total=total+load8(sha256(data,n))\n  set j=j+1\n end\n let result=buffer("batch_result",8)\n do store64(result,total)\n do write(1,result,8)')
bpy='import sys,hashlib,struct\nd=bytearray(open(sys.argv[1],"rb").read());total=0\nfor j in range(50):\n d[0]=j&255;total+=hashlib.sha256(d).digest()[0]\nsys.stdout.buffer.write(struct.pack("<Q",total))\n'
bc=csrc.replace('CC_SHA256(d,(CC_LONG)n,h);fwrite(h,1,32,stdout);','unsigned long long total=0;for(int j=0;j<50;j++){d[0]=j;CC_SHA256(d,(CC_LONG)n,h);total+=h[0];}fwrite(&total,1,8,stdout);')
raw=bytearray(fixture.read_bytes());total=0
for j in range(50):raw[0]=j;total+=hashlib.sha256(raw).digest()[0]
v={'RF2 0.21':native(bsrc,'sha-batch-rf2')+[str(fixture)],'Clang/CommonCrypto':cbuild(bc,'sha-batch-clang')+[str(fixture)],'Python/hashlib':pybuild(bpy,'sha-batch-python')+[str(fixture)]};measure('sha256-batch50-32KiB',v,total.to_bytes(8,'little'),{'bytesPerHash':32768,'hashes':50,'classification':'50hash batch amortizes, but still includes process startup; different SHA implementations'})
report['controllerSHA256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
report['artifacts']=[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in D.iterdir()if p.is_file()];report['passed']=True;(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'summary':report['summary']},indent=2))
