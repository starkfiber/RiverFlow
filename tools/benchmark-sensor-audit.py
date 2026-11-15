"""Rotated process-inclusive benchmark; all three arms implement the v2 contract."""
from pathlib import Path
import hashlib,json,os,platform,random,statistics,subprocess,sys,tempfile,time
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2:raise SystemExit('benchmark-sensor-audit.py NATIVE-EXECUTABLE')
native=Path(sys.argv[1]).resolve();D=Path(tempfile.mkdtemp(prefix='sensor-runtime-',dir=R/'artifacts'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
arms={'rf2':[str(native)],'python-batch':[sys.executable,str(R/'examples/sensor-audit/reference.py')],'python-single-pass':[sys.executable,str(R/'examples/sensor-audit/reference_stream.py')]}
header=b'sensor_id,timestamp_ms,temperature_mC\n';rng=random.Random(49021);inputs={}
for n in [0,128,4096]:
 lines=[f'{i%32+1},{i+9007199254740991},{rng.randrange(-100000,200001)}'.encode()for i in range(n)]
 inputs['rows-'+str(n)]=header+b'\n'.join(lines)+(b'\n'if n else b'')
inputs['late-refusal']=inputs['rows-4096']+b'1,0,NaN\n'
paths={}
for name,data in inputs.items():p=D/(name+'.csv');p.write_bytes(data);paths[name]=p
plan=dict(schema='rf2.sensor-runtime-plan.v1',host=platform.platform(),python=sys.version,pythonExecutable=sys.executable,pythonExecutableSHA256=sha(Path(sys.executable)),nativeSHA256=sha(native),sourceSHA256={str(p.relative_to(R)):sha(p)for p in [R/'examples/sensor-audit/main.flow',R/'examples/sensor-audit/lib/sensor.flow',R/'examples/sensor-audit/reference.py',R/'examples/sensor-audit/reference_stream.py',Path(__file__)]},inputSHA256={k:sha(p)for k,p in paths.items()},arms=arms,warmups=2,trials=15,order='rotate three arms by trial index',invariants=['Same accepted v2 JSON values on every valid input','Same exit2 and empty stdout on refusal','Input bytes unchanged'],measurement='Wall clock for complete new process, file read, validation, exact statistics and complete JSON output. Warm OS/file caches. Compilation, model authoring, AI tokens, energy, deployment and external services excluded.',stop='One fixed run; retain every trial. No adaptive repeat-until-win.')
(D/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(directory=str(D))),flush=True)
rows=[];summary={};env=dict(os.environ,PATH='/nonexistent')
for workload,path in paths.items():
 expected=None
 if workload!='late-refusal':
  control=subprocess.run([*arms['python-single-pass'],str(path)],capture_output=True,env=env,timeout=10);control.check_returncode();expected=json.loads(control.stdout)
 names=list(arms)
 for round in range(-2,15):
  order=names[round%3:]+names[:round%3]
  for arm in order:
   started=time.perf_counter_ns();q=subprocess.run([*arms[arm],str(path)],capture_output=True,env=env,timeout=10);elapsed=time.perf_counter_ns()-started
   try:actual=json.loads(q.stdout)if q.stdout else None
   except ValueError:actual='invalid JSON'
   good=(q.returncode==0 and actual==expected)if expected is not None else(q.returncode==2 and q.stdout==b'')
   row=dict(workload=workload,arm=arm,round=round,warmup=round<0,nanoseconds=elapsed,exit=q.returncode,outputBytes=len(q.stdout),outputSHA256=hashlib.sha256(q.stdout).hexdigest(),passed=good)
   rows.append(row);(D/'RAW.json').write_text(json.dumps(rows,indent=2)+'\n')
   if not good:raise RuntimeError((row,q.stderr.decode(errors='replace')))
 assert sha(path)==plan['inputSHA256'][workload]
 summary[workload]={}
 for arm in names:
  values=[x['nanoseconds']/1e6 for x in rows if x['workload']==workload and x['arm']==arm and not x['warmup']];median=statistics.median(values)
  summary[workload][arm]=dict(trials=len(values),medianMS=median,minMS=min(values),maxMS=max(values),medianAbsoluteDeviationMS=statistics.median(abs(x-median)for x in values))
report=dict(plan=plan,planSHA256=sha(D/'PLAN.json'),rawSHA256=sha(D/'RAW.json'),summary=summary,allPassed=all(x['passed']for x in rows),measuredProcesses=sum(not x['warmup']for x in rows),retainedWarmups=sum(x['warmup']for x in rows),limits='One Mac and bounded recorded-data task. Process-inclusive runtime result is not model authoring, token saving, hardware sensor validation, general Python superiority or independent human adoption.')
(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(directory=str(D),summary=summary,allPassed=report['allPassed'])),flush=True)
