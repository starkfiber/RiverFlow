"""Measure complete compiler/check operations, retaining overhead and byte oracles."""
from pathlib import Path
import hashlib,json,os,platform,random,statistics,subprocess,time
R=Path(__file__).resolve().parents[1];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();OLD=Path(os.environ['RF2_OLD_COMPILER']).resolve();D=R/'artifacts/check-only'/('bench-'+str(time.time_ns()));D.mkdir(parents=True);N=int(os.environ.get('RF2_BENCH_TRIALS','21'));assert 5<=N<=101
routes=['baseline compile','final compile','final check'];rows=[];tasks=[('small',R/'examples/function-changes/main.rf2'),('checksum',R/'examples/file-checksum.rf2'),('sha40',R/'examples/sha40/main.rf2')]
def run(args):return subprocess.run(list(map(str,args)),capture_output=True,timeout=30,env={'PATH':'/nonexistent'})
for name,src in tasks:
 # --check intentionally accepts no options. Compare default image layout for both compile routes.
 expected=D/(name+'-default');q=run([OLD,src,expected]);assert q.returncode==0,q.stderr;raw=expected.read_bytes()
 for trial in range(N):
  order=routes[:];random.Random(31061+trial).shuffle(order)
  for route in order:
   out=D/f'out-{len(rows)}';args=[C,'--check',src]if route=='final check'else[OLD if route=='baseline compile'else C,src,out]
   t=time.perf_counter_ns();q=run(args);ms=(time.perf_counter_ns()-t)/1e6;assert q.returncode==0,(name,route,q.stderr)
   if route=='final check':assert not out.exists() and q.stdout==b'RF2 source checked; no executable written.\n'
   else:assert out.read_bytes()==raw;out.unlink()
   rows.append(dict(task=name,trial=trial,route=route,ms=ms))
summary=[dict(task=name,medianMs={route:statistics.median(x['ms']for x in rows if x['task']==name and x['route']==route)for route in routes})for name,_ in tasks]
report=dict(passed=True,trials=N,summary=summary,raw=rows,baselineCompilerSHA256=hashlib.sha256(OLD.read_bytes()).hexdigest(),compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources={n:hashlib.sha256(s.read_bytes()).hexdigest()for n,s in tasks},host=platform.platform(),limits='One Mac warm filesystem; full processes. Compile routes both use default codegen/layout, no opt/compact. Check validates same default codegen through relocation/header but omits image publication. Compile byte oracle is preserved prior compiler. Check-only output-file absence uses a non-passed sentinel; actual unchanged workspace/nonexecution is covered separately by check_only_verify. No arbitrary application, runtime, AI/token or energy speed result.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),summary=summary)))
