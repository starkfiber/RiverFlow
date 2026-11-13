"""Full native CLI comparison on fixed snapshots of actual RF2 project files."""
from pathlib import Path
import subprocess,json,hashlib,statistics,random,time,platform,os
R=Path(__file__).resolve().parents[1];D=R/'artifacts/sha-memory'/('files-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-memory-final-self'))
oldc=D/'old-compiler';subprocess.run([C,R/'tests/fixtures/compiler-0.24-reference.rf2',oldc],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',oldc],capture_output=True,check=True)
app='\n'.join((R/'examples/file-checksum.rf2').read_text().splitlines()[2:]);variants={}
for name,compiler,sha in [('RF2 0.24',oldc,R/'tests/fixtures/sha-0.24-reference.rf2'),('RF2 memory candidate',C,R/'examples/evidence-contract/lib/sha256.rf2')]:
 src=D/('old.rf2'if name=='RF2 0.24'else'new.rf2');src.write_text('profile RF2_SYSTEM_A64_V1\n'+sha.read_text().split('\n',1)[1]+'\n'+app+'\n');exe=src.with_suffix('');subprocess.run([compiler,src,exe,'--opt'],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True);variants[name]=exe
cmain='''
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
int main(int argc,char**argv){if(argc!=2)return 2;int fd=open(argv[1],O_RDONLY|O_NONBLOCK|O_NOFOLLOW);if(fd<0)return 2;struct stat st;if(fstat(fd,&st)||!S_ISREG(st.st_mode)){close(fd);return 2;}static unsigned char d[1048577];size_t n=0;for(;;){ssize_t got=read(fd,d+n,sizeof(d)-n);if(got<0){close(fd);return 2;}n+=(size_t)got;if(n>1048576){close(fd);return 2;}if(!got)break;}if(close(fd))return 2;const unsigned char*h=direct_call(d,n);char text[65],hex[]="0123456789abcdef";for(int i=0;i<32;i++){text[i*2]=hex[h[i]>>4];text[i*2+1]=hex[h[i]&15];}text[64]='\\n';return write(1,text,65)==65?0:2;}
''';src=D/'direct.c';src.write_text((R/'tests/fixtures/sha256_direct_armv8.c').read_text()+cmain);exe=D/'direct';subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',src,'-o',exe],capture_output=True,check=True);variants['Clang/direct ARM SHA2']=exe
paths=['README.md','native/compiler/compiler.rf2','examples/file-checksum.rf2','examples/evidence-contract/lib/auth.rf2','docs/BYTE-REFERENCE.md','book/RiverFlow-First-Edition.md','docs/SHA-PREPARATION-MEASUREMENTS.json','tests/fixtures/sha256_direct_armv8.c','site/assets/rf2-capabilities.svg']
# Include a real produced Mach-O object, rather than inventing binary field data.
obj=D/'chain.o';subprocess.run(['/usr/bin/clang','-target','arm64-apple-macos11','-march=armv8-a+crypto','-c',R/'tests/standalone/sha256_chain_armv8.s','-o',obj],capture_output=True,check=True)
corpus=[]
for i,source in enumerate([*(R/p for p in paths),obj]):
 raw=source.read_bytes();assert len(raw)<=1048576;p=D/(str(i)+'-'+source.name);p.write_bytes(raw);corpus.append({'source':str(source.relative_to(R)),'snapshot':str(p.relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
rows=[];samples={name:[]for name in variants};warmups=[]
for name,exe in variants.items():
 for f in corpus:
  q=subprocess.run([exe,R/f['snapshot']],capture_output=True,timeout=5);assert q.returncode==0 and q.stdout==(f['sha256']+'\n').encode();warmups.append({'variant':name,'source':f['source'],'checked':True})
for trial in range(21):
 order=list(variants);random.Random(251113+trial).shuffle(order);files=corpus[:];random.Random(251114+trial).shuffle(files)
 for name in order:
  total=0
  for f in files:
   start=time.perf_counter_ns();q=subprocess.run([variants[name],R/f['snapshot']],capture_output=True,timeout=5);ms=(time.perf_counter_ns()-start)/1e6;assert q.returncode==0 and q.stdout==(f['sha256']+'\n').encode();total+=ms;rows.append({'trial':trial,'variant':name,'source':f['source'],'ms':ms})
  samples[name].append(total)
diffs=[a-b for a,b in zip(samples['RF2 memory candidate'],samples['Clang/direct ARM SHA2'])];rng=random.Random(251113);boot=sorted(statistics.median(rng.choices(diffs,k=21))for _ in range(10000));report={'passed':True,'host':platform.platform(),'trials':21,'corpus':corpus,'corpusBytes':sum(f['bytes']for f in corpus),'warmups':warmups,'medianCorpusMs':{n:statistics.median(v)for n,v in samples.items()},'minCorpusMs':{n:min(v)for n,v in samples.items()},'maxCorpusMs':{n:max(v)for n,v in samples.items()},'candidateMinusDirectCPairedMedianMs':statistics.median(diffs),'candidateMinusDirectCBootstrap95Ms':[boot[250],boot[9749]],'raw':rows,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'shaSourceSHA256':hashlib.sha256((R/'examples/evidence-contract/lib/sha256.rf2').read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'artifacts':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in D.iterdir()if p.is_file()],'scope':'Ten actual project file/artifact snapshots. One CLI process per input, produce-digest mode. Includes startup, open/type-check/read/close, hashing and output capture; warm OS cache after correctness warmup. No cold-disk or field deployment claim. Different executable/load/I/O implementations remain confounders. No universal speed claim.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'medianCorpusMs':report['medianCorpusMs'],'paired95':report['candidateMinusDirectCBootstrap95Ms']},indent=2))
