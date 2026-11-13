"""Matched SHA task trials; includes startup, all outputs and comparator losses."""
from pathlib import Path
import subprocess,json,hashlib,statistics,random,time,platform,sys,os
R=Path(__file__).resolve().parents[1];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-sha-next-self'));D=R/'artifacts/sha-next'/('qualified-bench-'+str(time.time_ns()));D.mkdir(parents=True)
previous=subprocess.check_output(['git','show','3ecbf7f4ab1fb7c262810cb39ddb784613186ebf:examples/evidence-contract/lib/sha256.rf2'],cwd=R,text=True).split('\n',1)[1]
new=(R/'examples/evidence-contract/lib/sha256.rf2').read_text().split('\n',1)[1]
main='fn main(argc,argv)\n let data=buffer("input",32769)\n let fd=open(load64(argv+8),0,0)\n if fd>>63\n  return 1\n end\n let n=0\n let got=1\n while got\n  set got=read(fd,data+n,32769-n)\n  if got>>63\n   do close(fd)\n   return 1\n  end\n  set n=n+got\n  if n>32768\n   do close(fd)\n   return 1\n  end\n end\n do close(fd)\n let j=0\n let total=0\n while j<50\n  do store8(data,j&255)\n  set total=total+load8(sha256(data,n))\n  set j=j+1\n end\n let result=buffer("batch_result",8)\n do store64(result,total)\n do write(1,result,8)\n return 0\nend\n'
csource='#include <stdio.h>\n#include <CommonCrypto/CommonDigest.h>\nint main(int c,char**v){unsigned char d[32769],h[32];FILE*f=fopen(v[1],"rb");if(!f)return 1;size_t n=fread(d,1,sizeof d,f);fclose(f);if(n>32768)return 1;unsigned long long total=0;for(int j=0;j<50;j++){d[0]=j;CC_SHA256(d,(CC_LONG)n,h);total+=h[0];}fwrite(&total,1,8,stdout);}\n'
pysource='import sys,hashlib,struct\nd=bytearray(open(sys.argv[1],"rb").read());total=0\nfor j in range(50):\n d[0]=j&255;total+=hashlib.sha256(d).digest()[0]\nsys.stdout.buffer.write(struct.pack("<Q",total))\n'
rows=[];summary=[];fixture=D/'payload.bin';fixture.write_bytes(bytes(range(256))*128)
for count in [50,2000]:
 variants={}
 for label,sha in [('RF2 0.22',previous),('RF2 SHA2 candidate',new)]:
  p=D/(str(count)+('-old'if label=='RF2 0.22'else'-new')+'.rf2');p.write_text(('profile RF2_SYSTEM_A64_V1\n'+sha+'\n'+main).replace('while j<50',f'while j<{count}'));out=p.with_suffix('');subprocess.run([C,p,out,'--opt'],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);variants[label]=[str(out),str(fixture)]
 p=D/f'{count}-clang.c';p.write_text(csource.replace('j<50',f'j<{count}'));exe=p.with_suffix('');subprocess.run(['/usr/bin/clang','-O3','-mcpu=native',p,'-o',exe],check=True,capture_output=True);variants['Clang/CommonCrypto']=[str(exe),str(fixture)]
 p=D/f'{count}-python.py';p.write_text(pysource.replace('range(50)',f'range({count})'));variants['Python/hashlib']=[sys.executable,str(p),str(fixture)]
 data=bytearray(fixture.read_bytes());total=0
 for j in range(count):data[0]=j&255;total+=hashlib.sha256(data).digest()[0]
 expected=total.to_bytes(8,'little');samples={k:[]for k in variants}
 for name,cmd in variants.items():q=subprocess.run(cmd,capture_output=True,timeout=15);assert q.returncode==0 and q.stdout==expected
 for trial in range(21):
  order=list(variants);random.Random(231113+trial).shuffle(order)
  for name in order:
   start=time.perf_counter_ns();q=subprocess.run(variants[name],capture_output=True,timeout=15);ms=(time.perf_counter_ns()-start)/1e6;assert q.returncode==0 and q.stdout==expected;samples[name].append(ms);rows.append({'hashes':count,'trial':trial,'variant':name,'ms':ms})
 diffs=[a-b for a,b in zip(samples['RF2 SHA2 candidate'],samples['Clang/CommonCrypto'])];rng=random.Random(231113);boot=sorted(statistics.median(rng.choices(diffs,k=len(diffs)))for _ in range(10000))
 summary.append({'hashes':count,'bytesPerHash':len(data),'medianMs':{k:statistics.median(v)for k,v in samples.items()},'minMs':{k:min(v)for k,v in samples.items()},'maxMs':{k:max(v)for k,v in samples.items()},'pairedCandidateMinusCMedianMs':statistics.median(diffs),'pairedMedianBootstrap95Ms':[boot[250],boot[9749]],'qualification':'Exploratory paired interval on one uncontrolled host; not cross-host or universal superiority.'})
report={'passed':True,'host':platform.platform(),'python':sys.version,'trials':21,'summary':summary,'raw':rows,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'shaSourceSHA256':hashlib.sha256((R/'examples/evidence-contract/lib/sha256.rf2').read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'feature':subprocess.check_output(['/usr/sbin/sysctl','hw.optional.arm.FEAT_SHA256'],text=True).strip(),'fixtureSHA256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'artifacts':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in D.iterdir()if p.is_file()],'scope':'21 rotated fresh-process trials after warmup. Same file, count, first-byte mutation and checked digest-byte sum. Startup and initial file reading included. RF2 0.22 scalar source rebuilt with candidate compiler; common compiler isolates source path. Both C and RF2 may use existing ARM SHA hardware. No new crypto, transistor mechanism, AI generation, billed tokens or universal performance claim.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'summary':summary},indent=2))
