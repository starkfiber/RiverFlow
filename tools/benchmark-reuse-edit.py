"""Real partial-edit rebuilds: SHA40 entry errors change; checked kernels remain unchanged."""
from pathlib import Path
import hashlib,json,os,random,statistics,subprocess,time
R=Path(__file__).resolve().parents[1];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();D=R/'artifacts/function-reuse'/('edit-bench-'+str(time.time_ns()));D.mkdir(parents=True)
N=int(os.environ.get('RF2_BENCH_TRIALS','21'));assert 5<=N<=101
project=D/'project';project.mkdir();source=project/'main.rf2';template=(R/'examples/sha40/main.rf2').read_text();(project/'rounds.rf2').write_bytes((R/'examples/sha40/rounds.rf2').read_bytes());source.write_text(template);cache=D/'units';cache.mkdir(mode=0o700);rows=[]
def invoke(args,**kw):return subprocess.run(list(map(str,args)),capture_output=True,timeout=40,**kw)
q=invoke([C,source,D/'setup','--opt','--compact','--reuse-cache',cache]);assert q.returncode==0,q.stderr
for trial in range(N):
 # The accepted40byte computation is unchanged; an actual entry error code evolves.
 source.write_text(template.replace('return 2','return '+str(trial+2),1));order=['clean','reuse'];random.Random(29060+trial).shuffle(order);outputs={}
 for route in order:
  out=D/f'{route}-{trial}';args=[C,source,out,'--opt','--compact']
  if route=='reuse':args+=['--reuse-cache',cache]
  start=time.perf_counter_ns();q=invoke(args);ms=(time.perf_counter_ns()-start)/1e6;assert q.returncode==0,q.stderr;outputs[route]=out
  receipt=None if route=='clean'else json.loads(Path(str(out)+'.reuse.json').read_text())
  if receipt:assert receipt['reused']==4 and receipt['validationReused']==4,receipt
  rows.append({'trial':trial,'route':route,'ms':ms,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'reuse':receipt})
 assert outputs['clean'].read_bytes()==outputs['reuse'].read_bytes()
 # Behavior is independently checked outside the compile timer.
 out=outputs['reuse'];assert invoke(['/usr/bin/codesign','-s','-',out]).returncode==0;data=bytes((i+trial)&255 for i in range(40));q=invoke([out],input=data);assert q.returncode==0 and q.stdout==hashlib.sha256(data).digest();assert invoke([out,'bad'],input=data).returncode==trial+2
clean=[x['ms']for x in rows if x['route']=='clean'];reuse=[x['ms']for x in rows if x['route']=='reuse'];delta=[b-a for a,b in zip(clean,reuse)];rng=random.Random(29060);boot=sorted(statistics.median(rng.choices(delta,k=N))for _ in range(10000));med={k:statistics.median(x['ms']for x in rows if x['route']==k)for k in ['clean','reuse']}
report={'passed':True,'schema':'rf2.partial.edit.measurements.v1','trials':N,'medianMs':med,'cleanOverReuseRatio':med['clean']/med['reuse'],'pairedCandidateMinusCleanMedianMs':statistics.median(delta),'bootstrap95Ms':[boot[250],boot[9749]],'raw':rows,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'kernelSourceSHA256':hashlib.sha256((project/'rounds.rf2').read_bytes()).hexdigest(),'limits':'One Mac warm filesystem, complete compiler processes/output creation. Each trial changes actual entry-function code while preserving kernel source; exact clean bytes and complete hashlib digest/error behavior checked outside timer. Not application execution, AI usage or universal performance.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'medianMs':med,'ratio':report['cleanOverReuseRatio'],'bootstrap95Ms':report['bootstrap95Ms']}))
