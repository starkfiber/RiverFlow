"""In-process SHA API measurements. No startup/I/O included in reported engine interval."""
from pathlib import Path
import subprocess,struct,json,hashlib,statistics,random,time,platform,sys,os
R=Path(__file__).resolve().parents[1];D=R/'artifacts/sha-stream'/('steady-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-sha-prep3-self'));old=Path(os.environ.get('RF2_BASELINE_SHA',R/'tests/fixtures/sha-0.23-reference.rf2')).read_text().split('\n',1)[1];new=(R/'examples/evidence-contract/lib/sha256.rf2').read_text().split('\n',1)[1]
BASELINE=os.environ.get('RF2_BASELINE_LABEL','RF2 0.23')
BASELINE_COMPILER_SOURCE=Path(os.environ.get('RF2_BASELINE_COMPILER_SOURCE',R/'tests/fixtures/compiler-0.23-reference.rf2'))
BASELINE_SHA_SOURCE=Path(os.environ.get('RF2_BASELINE_SHA',R/'tests/fixtures/sha-0.23-reference.rf2'))
# Recreate the historical generator from retained RF2 source. Build time is excluded.
baseline_compiler=D/'rf2c-0.23-control'
subprocess.run([C,BASELINE_COMPILER_SOURCE,baseline_compiler],capture_output=True,check=True)
subprocess.run(['/usr/bin/codesign','-s','-',baseline_compiler],capture_output=True,check=True)
rf='''fn main(argc,argv)
 let data=buffer("input",32769)
 let fd=open(load64(argv+8),0,0)
 let n=read(fd,data,32769)
 do close(fd)
 if n>32768
  return 1
 end
 let tb=buffer("tb",8)
 if clock_timebase(tb)!=0
  return 2
 end
 do sha256(data,n)
 let j=0
 let total=0
 let start=vm_clock_ticks()
 while j<COUNT
  if n!=0
   do store8(data,j&255)
  end
  set total=total+load8(sha256(data,n))
  set j=j+1
 end
 let elapsed=vm_clock_ticks()-start
 let out=buffer("out",40)
 do store64(out,elapsed)
 do store64(out+8,load32(tb))
 do store64(out+16,load32(tb+4))
 do store64(out+24,total)
 do store64(out+32,j)
 do write(1,out,40)
 return 0
end
'''
csrc='''#include <stdio.h>
#include <stdint.h>
#include <mach/mach_time.h>
#include <CommonCrypto/CommonDigest.h>
int main(int argc,char**argv){unsigned char d[32769],h[32];FILE*f=fopen(argv[1],"rb");if(!f)return 1;size_t n=fread(d,1,sizeof d,f);fclose(f);if(n>32768)return 1;mach_timebase_info_data_t tb;if(mach_timebase_info(&tb))return 2;CC_SHA256(d,(CC_LONG)n,h);uint64_t total=0,start=mach_absolute_time();for(uint64_t j=0;j<COUNT;j++){if(n)d[0]=j&255;CC_SHA256(d,(CC_LONG)n,h);total+=h[0];}uint64_t out[5]={mach_absolute_time()-start,tb.numer,tb.denom,total,COUNT};fwrite(out,1,40,stdout);}
'''
pysrc='''import sys,hashlib,time,struct
d=bytearray(open(sys.argv[1],"rb").read());hashlib.sha256(d).digest();total=0
start=time.perf_counter_ns()
for j in range(COUNT):
 if len(d):d[0]=j&255
 total+=hashlib.sha256(d).digest()[0]
elapsed=time.perf_counter_ns()-start
sys.stdout.buffer.write(struct.pack("<5Q",elapsed,1,1,total,COUNT))
'''
rows=[];summary=[]
for n,count in [(0,20000),(64,20000),(4096,4000),(32768,2000)]:
 fixture=D/f'input-{n}';fixture.write_bytes(bytes(i&255 for i in range(n)));variants={}
 for name,sha in [(BASELINE,old),('RF2 preparation candidate',new)]:
  p=D/(f'{n}-'+('old'if name==BASELINE else'new')+'.rf2');p.write_text('profile RF2_SYSTEM_A64_V1\n'+sha+'\n'+rf.replace('COUNT',str(count)));out=p.with_suffix('');subprocess.run([baseline_compiler if name==BASELINE else C,p,out,'--opt'],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True);variants[name]=[str(out),str(fixture)]
 p=D/f'{n}-c.c';p.write_text(csrc.replace('COUNT',str(count)));out=p.with_suffix('');subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',p,'-o',out],capture_output=True,check=True);variants['Clang/CommonCrypto']=[str(out),str(fixture)]
 direct=csrc.replace('CC_SHA256(d,(CC_LONG)n,h);','memcpy(h,direct_call(d,n),32);')
 direct=(R/'tests/fixtures/sha256_direct_armv8.c').read_text()+direct
 p=D/f'{n}-direct.c';p.write_text(direct.replace('COUNT',str(count)));out=p.with_suffix('');subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',p,'-o',out],capture_output=True,check=True);variants['Clang/direct ARM SHA2']=[str(out),str(fixture)]
 p=D/f'{n}-py.py';p.write_text(pysrc.replace('COUNT',str(count)));variants['Python/hashlib']=[sys.executable,str(p),str(fixture)]
 data=bytearray(fixture.read_bytes());expected=0
 for j in range(count):
  if n:data[0]=j&255
  expected+=hashlib.sha256(data).digest()[0]
 samples={k:[]for k in variants}
 for trial in range(21):
  order=list(variants);random.Random(241113+trial).shuffle(order)
  for name in order:
   q=subprocess.run(variants[name],capture_output=True,timeout=10);assert q.returncode==0 and len(q.stdout)==40,(name,q.returncode,q.stdout,q.stderr);ticks,num,den,total,cnt=struct.unpack('<5Q',q.stdout);assert total==expected and cnt==count and num>0 and den>0;ms=ticks*num/den/1e6;samples[name].append(ms);rows.append({'bytesPerHash':n,'hashes':count,'trial':trial,'variant':name,'ms':ms,'ticks':ticks,'numerator':num,'denominator':den,'total':total})
 diffs=[a-b for a,b in zip(samples['RF2 preparation candidate'],samples['Clang/CommonCrypto'])];rng=random.Random(241113);bootstrap=sorted(statistics.median(rng.choices(diffs,k=21))for _ in range(10000))
 summary.append({'bytesPerHash':n,'hashes':count,'medianMs':{k:statistics.median(v)for k,v in samples.items()},'candidateMinusCMedianPairedMs':statistics.median(diffs),'candidateMinusCBootstrap95Ms':[bootstrap[250],bootstrap[9749]],'minMs':{k:min(v)for k,v in samples.items()},'maxMs':{k:max(v)for k,v in samples.items()}})
report={'passed':True,'host':platform.platform(),'trials':21,'summary':summary,'raw':rows,'previousCompilerSHA256':hashlib.sha256(baseline_compiler.read_bytes()).hexdigest(),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'shaSourceSHA256':hashlib.sha256((R/'examples/evidence-contract/lib/sha256.rf2').read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'directCSourceSHA256':hashlib.sha256((R/'tests/fixtures/sha256_direct_armv8.c').read_bytes()).hexdigest(),'previousCompilerSourceSHA256':hashlib.sha256(BASELINE_COMPILER_SOURCE.read_bytes()).hexdigest(),'previousShaSourceSHA256':hashlib.sha256(BASELINE_SHA_SOURCE.read_bytes()).hexdigest(),'feature':subprocess.check_output(['/usr/sbin/sysctl','hw.optional.arm.FEAT_SHA256'],text=True).strip(),'artifacts':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in D.iterdir()if p.is_file()],'directControl':'C uses a volatile function pointer so repeated empty-message calls cannot be hoisted or folded; every iteration must perform a call, matching opaque CommonCrypto and RF2 calls.','scope':'Same complete SHA API work, input mutation, digest-byte sum and verified result. Timed loops inside each process after a warmup hash. Excludes startup, file loading, allocation, first feature query and first constant initialization. Not compression-only or cycles; runtime/API overhead remains. One uncontrolled host; no universal speed, energy or AI-token claim.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'summary':summary},indent=2))
