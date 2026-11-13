"""Matched complete compiler runs, including reuse validation and unit I/O."""
from pathlib import Path
import hashlib,json,os,platform,random,resource,statistics,subprocess,time
R=Path(__file__).resolve().parents[1]
C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
D=R/'artifacts/function-reuse'/('bench-'+str(time.time_ns()));D.mkdir(parents=True)
N=int(os.environ.get('RF2_BENCH_TRIALS','21'));assert 5<=N<=101
fixture=D/'numeric-helpers.rf2'
fixture.write_text('profile RF2_SYSTEM_A64_V1\n'+''.join('fn helper'+str(i)+'(x)\n return '+ ' + '.join(['x']+list(map(str,range(1,97))))+'\nend\n' for i in range(96))+'fn main(argc,argv)\n return helper0(1)!=4657\nend\n')
tasks=[('small-example',R/'examples/function-changes/main.rf2'),('file-checksum',R/'examples/file-checksum.rf2'),('numeric-helper-fixture',fixture)]
rows=[];setup=[];variants=['direct clean','empty unit cache','retained unit cache']
def run(args):return subprocess.run([str(x)for x in args],capture_output=True,timeout=60,env={'PATH':'/nonexistent'})
for name,source in tasks:
 oracle=D/(name+'-oracle');q=run([C,source,oracle,'--opt','--compact']);assert q.returncode==0,q.stderr;expected=oracle.read_bytes()
 warm=D/(name+'-units');warm.mkdir(mode=0o700);out=D/(name+'-setup');start=time.perf_counter_ns();q=run([C,source,out,'--opt','--compact','--reuse-cache',warm]);elapsed=(time.perf_counter_ns()-start)/1e6;assert q.returncode==0 and out.read_bytes()==expected,q.stderr
 setup.append(dict(task=name,ms=elapsed,receipt=json.loads(Path(str(out)+'.reuse.json').read_text())))
 for trial in range(N):
  order=variants[:];random.Random(28011+trial).shuffle(order)
  for variant in order:
   out=D/f'out-{len(rows)}';args=[C,source,out,'--opt','--compact']
   if variant!='direct clean':
    cache=warm
    if variant=='empty unit cache':cache=D/f'empty-{len(rows)}';cache.mkdir(mode=0o700)
    args+=['--reuse-cache',cache]
   usage=resource.getrusage(resource.RUSAGE_CHILDREN);cpu=usage.ru_utime+usage.ru_stime;start=time.perf_counter_ns();q=run(args);ms=(time.perf_counter_ns()-start)/1e6;usage=resource.getrusage(resource.RUSAGE_CHILDREN);cpu_ms=(usage.ru_utime+usage.ru_stime-cpu)*1000;assert q.returncode==0 and out.read_bytes()==expected,(name,variant,q.stderr)
   receipt=None if variant=='direct clean'else json.loads(Path(str(out)+'.reuse.json').read_text())
   if variant=='retained unit cache':assert receipt['reused']>0,(name,receipt)
   if variant=='empty unit cache':assert receipt['reused']==0
   rows.append(dict(task=name,trial=trial,variant=variant,ms=ms,observedChildCpuMs=cpu_ms,reuse=receipt,unsignedSHA256=hashlib.sha256(expected).hexdigest()))
summary=[]
for name,_ in tasks:
 med={v:statistics.median(x['ms']for x in rows if x['task']==name and x['variant']==v)for v in variants}
 summary.append(dict(task=name,medianMs=med,cleanOverRetainedRatio=med['direct clean']/med['retained unit cache']))
report=dict(passed=True,schema='rf2.function.reuse.measurements.v1',trialsPerVariant=N,summary=summary,raw=rows,firstCacheSetups=setup,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources={name:hashlib.sha256(p.read_bytes()).hexdigest()for name,p in tasks},host=platform.platform(),limits='One host warm filesystem, complete compiler processes including actual executable hashing, semantic whitelist validation, file I/O and new output creation. Same compiler/options/sources and byte oracle for each task. The numeric-helper case is an explicit generated benchmark fixture, not field work. Retained unit cache initialized separately. No application execution, energy, billed model-token or universal performance claim.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'summary':summary}))
