"""Complete compile costs, matched sources, byte equality and rotated route order."""
from pathlib import Path
import hashlib,json,os,platform,random,statistics,subprocess,time
R=Path(__file__).resolve().parents[1];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();OLD=Path(os.environ['RF2_OLD_COMPILER']).resolve()
D=R/'artifacts/function-pack'/('bench-'+str(time.time_ns()));D.mkdir(parents=True)
N=int(os.environ.get('RF2_BENCH_TRIALS','21'));assert 5<=N<=101
fixture=D/'numeric.rf2';fixture.write_text('profile RF2_SYSTEM_A64_V1\n'+''.join('fn helper'+str(i)+'(x)\n return '+' + '.join(['x']+list(map(str,range(1,97))))+'\nend\n'for i in range(96))+'fn main(argc,argv)\n return helper0(1)!=4657\nend\n')
tasks=[('small',R/'examples/function-changes/main.rf2'),('checksum',R/'examples/file-checksum.rf2'),('sha40',R/'examples/sha40/main.rf2'),('numeric',fixture)]
variants=['0.29 clean','candidate clean','warm files','cold pack','warm pack'];rows=[];setup=[]
def run(args):return subprocess.run(list(map(str,args)),capture_output=True,timeout=60,env={'PATH':'/nonexistent'})
for name,source in tasks:
 oracle=D/(name+'-oracle');q=run([OLD,source,oracle,'--opt','--compact']);assert q.returncode==0,q.stderr;expected=oracle.read_bytes()
 caches={}
 for mode in ['files','pack']:
  cache=D/(name+'-'+mode);cache.mkdir(mode=0o700);caches[mode]=cache;out=D/(name+'-setup-'+mode)
  t=time.perf_counter_ns();q=run([C,source,out,'--opt','--compact','--reuse-'+('cache'if mode=='files'else'pack'),cache]);ms=(time.perf_counter_ns()-t)/1e6
  assert q.returncode==0 and out.read_bytes()==expected,q.stderr;setup.append(dict(task=name,mode=mode,ms=ms))
 for trial in range(N):
  order=variants[:];random.Random(3001+trial).shuffle(order)
  for variant in order:
   out=D/f'out-{len(rows)}';args=[OLD if variant=='0.29 clean'else C,source,out,'--opt','--compact']
   if variant in ['warm files','warm pack','cold pack']:
    cache=caches['files'if variant=='warm files'else'pack']
    if variant=='cold pack':cache=D/f'cold-{len(rows)}';cache.mkdir(mode=0o700)
    args+=['--reuse-cache'if variant=='warm files'else'--reuse-pack',cache]
   t=time.perf_counter_ns();q=run(args);ms=(time.perf_counter_ns()-t)/1e6
   assert q.returncode==0 and out.read_bytes()==expected,(name,variant,q.stderr)
   receipt=json.loads(Path(str(out)+'.reuse.json').read_text())if'pack'in variant or variant=='warm files'else None
   if variant.startswith('warm'):assert receipt['reused']>0
   if variant=='cold pack':assert receipt['reused']==0
   rows.append(dict(task=name,trial=trial,route=variant,ms=ms,receipt=receipt))
summary=[dict(task=name,medianMs={v:statistics.median(x['ms']for x in rows if x['task']==name and x['route']==v)for v in variants})for name,_ in tasks]
report=dict(passed=True,trials=N,summary=summary,raw=rows,firstSetups=setup,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),baselineSHA256=hashlib.sha256(OLD.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources={n:hashlib.sha256(s.read_bytes()).hexdigest()for n,s in tasks},host=platform.platform(),limits='One Mac, warm filesystem, complete compiler process and output creation. Exact unsigned output equality for every observation. Generated numeric workload is a benchmark fixture. No runtime, token, energy, universal or cross-host claim.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),summary=summary)))
