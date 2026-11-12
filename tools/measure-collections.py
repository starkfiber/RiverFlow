"""Matched latency-summary programs: process timings, correctness and explicit baselines."""
from pathlib import Path
import os,subprocess,time,statistics,hashlib,json,random,platform,re
R=Path(__file__).resolve().parents[1];D=R/'artifacts'/os.environ.get('RF2_BENCH_RUN','collections-performance');D.mkdir(exist_ok=False);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-arrays'));OLD=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/rf2c-0.11-final'));variants={}
for opt in [False,True]:
 name='rf2-checked-'+('opt'if opt else'default');path=D/name;p=subprocess.run([C,R/'examples/latency/main.rf2',path]+(['--opt']if opt else[]),capture_output=True);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',path],check=True,capture_output=True);variants[name]=path
# Same valid-input algorithm through the old raw global-buffer API. It has different lifetime/bounds semantics.
sources=[R/'examples/latency/lib/io.rf2',R/'examples/latency/lib/samples.rf2',R/'examples/latency/main.rf2'];text='profile RF2_SYSTEM_A64_V1\n'+'\n'.join('\n'.join(line for line in p.read_text().splitlines()if not line.startswith(('module ','use ','profile ','array ')))for p in sources)
text=text.replace(': Samples','').replace('let samples = Samples()','let samples = buffer("sample_values",1024)').replace('values.length','128')
# The source fixture's subscripts do not contain nested bracket operations.
text=re.sub(r'set (samples|values)\[([^\]]+)\] = ([^\n]+)',lambda m:'do store64('+m[1]+'+('+m[2]+')*8, '+m[3]+')',text)
text=re.sub(r'(samples|values)\[([^\]]+)\]',lambda m:'load64('+m[1]+'+('+m[2]+')*8)',text);raw=D/'raw.rf2';raw.write_text(text);path=D/'rf2-011-raw';p=subprocess.run([OLD,raw,path,'--opt'],capture_output=True);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',path],check=True,capture_output=True);variants['rf2-011-raw-global-buffer']=path
csrc=D/'latency.c';csrc.write_text(r'''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
static int cmp(const void*a,const void*b){uint64_t x=*(const uint64_t*)a,y=*(const uint64_t*)b;return(x>y)-(x<y);}
int main(int argc,char**argv){if(argc<2||argc>129)return 1;uint64_t v[128]={0},sum=0;size_t n=argc-1;for(size_t i=0;i<n;i++){char*p=argv[i+1];size_t len=0;uint64_t value=0;while(p[len]){if(p[len]<'0'||p[len]>'9'||len>=10)return 1;value=value*10+p[len]-'0';if(value>UINT32_MAX)return 1;len++;}if(!len)return 1;v[i]=value;sum+=value;}
#ifdef QSORT
qsort(v,n,sizeof(v[0]),cmp);
#else
for(size_t i=1;i<n;i++){uint64_t key=v[i];size_t j=i;while(j>0&&v[j-1]>key){v[j]=v[j-1];j--;}v[j]=key;}
#endif
printf("{\"count\":%zu,\"min\":%"PRIu64",\"max\":%"PRIu64",\"sum\":%"PRIu64",\"median_lower\":%"PRIu64",\"p95_nearest_rank\":%"PRIu64"}\n",n,v[0],v[n-1],sum,v[(n-1)/2],v[(n*95+99)/100-1]);return 0;}
''')
for name,flags in [('clang-insertion',[]),('clang-qsort',['-DQSORT'])]:
 path=D/name;subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',*flags,csrc,'-o',path],check=True,capture_output=True);variants[name]=path
report={'schema':'rf2.collections.measurements.v1','compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'host':platform.platform(),'clang':subprocess.check_output(['/usr/bin/clang','--version'],text=True).splitlines()[0],'scope':'Seven rotated fresh-process trials after retained cold/warmup, one uncontrolled Mac. Includes process launch, parsing, sorting and JSON output. The old raw-global-buffer RF2 variant has different lifetime and bounds semantics; C qsort also changes the sorting algorithm. No isolated check-overhead, general speed, energy or AI-token claim.','raw':[],'summary':[]}
rng=random.Random(20261112)
for n in [1,32,128]:
 for shape in ['random','descending']:
  values=[rng.randrange(100000)for _ in range(n)];values=sorted(values,reverse=True)if shape=='descending'else values;ordered=sorted(values);expected={'count':n,'min':min(values),'max':max(values),'sum':sum(values),'median_lower':ordered[(n-1)//2],'p95_nearest_rank':ordered[(n*95+99)//100-1]};args=list(map(str,values));times={v:[]for v in variants}
  for name,path in variants.items():
   start=time.perf_counter_ns();p=subprocess.run([path,*args],capture_output=True);assert p.returncode==0 and json.loads(p.stdout)==expected;report['raw'].append({'variant':name,'count':n,'shape':shape,'coldOrWarmupMs':(time.perf_counter_ns()-start)/1e6,'excludedFromMedian':True})
  for j in range(7):
   order=list(variants);random.Random(2026+j).shuffle(order)
   for name in order:
    t=time.perf_counter_ns();p=subprocess.run([variants[name],*args],capture_output=True);dt=(time.perf_counter_ns()-t)/1e6;assert p.returncode==0 and json.loads(p.stdout)==expected;times[name].append(dt);report['raw'].append({'variant':name,'count':n,'shape':shape,'trial':j,'ms':dt,'input':values,'expected':expected})
  report['summary'].append({'count':n,'shape':shape,'medianMs':{k:statistics.median(v)for k,v in times.items()},'minMs':{k:min(v)for k,v in times.items()},'maxMs':{k:max(v)for k,v in times.items()}})
report['artifacts']=[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in [raw,csrc,*variants.values()]]
(R/'docs/COLLECTIONS-MEASUREMENTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
