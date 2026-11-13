"""Matched frozen0.21 and native-rotate candidate SHA tasks. Retain every comparator/loss."""
from pathlib import Path
import subprocess,json,hashlib,statistics,random,time,platform,sys,os
R=Path(__file__).resolve().parents[1];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-0.22-self'));D=R/'artifacts/rotate-0.22'/('bench-'+str(time.time_ns()));D.mkdir(parents=True)
oldreport=json.loads((R/'docs/APPLICATION-BENCHMARKS-0.21.json').read_text());frozen=next((R/x['path']).parent for x in oldreport['artifacts']if x['path'].endswith('/sha-batch-rf2'));oldsha=(R/'artifacts/rotate-0.22/sha256-0.21.rf2').read_text().split('\n',1)[1];newsha=(R/'examples/evidence-contract/lib/sha256.rf2').read_text().split('\n',1)[1];rows=[];summaries=[]
for kind in ['sha','sha-batch']:
 original=(frozen/(kind+'-rf2.rf2')).read_text();assert original.count(oldsha)==1;source=D/(kind+'.rf2');source.write_text(original.replace(oldsha,newsha));out=D/kind;subprocess.run([C,source,out,'--opt'],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
 fixture=frozen/'payload.bin';data=bytearray(fixture.read_bytes())
 if kind=='sha':expected=hashlib.sha256(data).digest()
 else:
  total=0
  for j in range(50):data[0]=j;total+=hashlib.sha256(data).digest()[0]
  expected=total.to_bytes(8,'little')
 variants={'RF2 0.21':[str(frozen/(kind+'-rf2')),str(fixture)],'RF2 rotate candidate':[str(out),str(fixture)],'Clang/CommonCrypto':[str(frozen/(kind+'-clang')),str(fixture)],'Python/hashlib':[sys.executable,str(frozen/(kind+'-python.py')),str(fixture)]};samples={v:[]for v in variants}
 for name,cmd in variants.items():
  start=time.perf_counter_ns();q=subprocess.run(cmd,capture_output=True,timeout=10);assert q.returncode==0 and q.stdout==expected;rows.append({'task':kind,'variant':name,'excludedWarmupMs':(time.perf_counter_ns()-start)/1e6})
 for trial in range(21):
  order=list(variants);random.Random(2200+trial).shuffle(order)
  for name in order:
   start=time.perf_counter_ns();q=subprocess.run(variants[name],capture_output=True,timeout=10);ms=(time.perf_counter_ns()-start)/1e6;assert q.returncode==0 and q.stdout==expected;samples[name].append(ms);rows.append({'task':kind,'trial':trial,'variant':name,'ms':ms})
 summaries.append({'task':kind,'medianMs':{v:statistics.median(s)for v,s in samples.items()},'minMs':{v:min(s)for v,s in samples.items()},'maxMs':{v:max(s)for v,s in samples.items()}})
report={'passed':True,'host':platform.platform(),'pythonVersion':sys.version,'trials':21,'summary':summaries,'raw':rows,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'shaSourceSHA256':hashlib.sha256((R/'examples/evidence-contract/lib/sha256.rf2').read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'baselineReportSHA256':hashlib.sha256((R/'docs/APPLICATION-BENCHMARKS-0.21.json').read_bytes()).hexdigest(),'artifacts':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in D.iterdir()if p.is_file()],'scope':'Same runtime file and output oracle,21rotated fresh-process trials afterwarmup. Includesstartup; batch50 variesfirstbyte/hash. FrozenRF2baseline, CCommonCrypto andPythonhashlib retained. No isolated single-instruction, universal speed, energy, fullAI-task or billedtoken claim.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'summary':summaries},indent=2))
