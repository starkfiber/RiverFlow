"""Matched empty project-cache builds with/without an explicitly retained compiler store."""
from pathlib import Path
import subprocess,time,os,json,hashlib,random,statistics,platform
R=Path(__file__).resolve().parents[1];D=R/'artifacts/cold-profile-028'/('bench-store-'+str(time.time_ns()));D.mkdir(parents=True)
C=Path(os.environ['RF2_TEST_COMPILER']).resolve();OLD=Path(os.environ['RF2_OLD_BUILDER']).resolve();NEW=Path(os.environ['RF2_BUILD_BIN']).resolve();N=int(os.environ.get('RF2_BENCH_TRIALS','21'));assert 5<=N<=101
runtime=D/'runtime.rf2';runtime.write_text(''.join((R/x).read_text()for x in ['native/rf2.rf2','native/core.rf2','native/attendance.rf2','native/attendance-kernel.rf2','native/fingerprint.rf2','native/invoice.rf2','native/invoice-kernel.rf2','native/prepared.rf2','native/workspace.rf2','native/editor.rf2']))
tasks=[('checksum',R/'examples/file-checksum.rf2'),('runtime',runtime),('compiler',R/'native/compiler/compiler.rf2')];store=D/'compiler-store';store.mkdir(mode=0o700);rows=[];setup_cache=D/'initial-cache';setup_cache.mkdir(mode=0o700);setup_out=D/'initial-output';start=time.perf_counter_ns();q=subprocess.run([NEW,C,tasks[0][1],setup_out,setup_cache,'--opt','--compact','--compiler-store',store],capture_output=True,timeout=30,env={'PATH':'/nonexistent'});assert q.returncode==0,q.stderr;setup_ms=(time.perf_counter_ns()-start)/1e6;compiler_name=hashlib.sha256(C.read_bytes()).hexdigest()+'.compiler';original_inode=(store/compiler_name).stat().st_ino
variants=['previous empty project','new empty project','new empty project retained compiler']
for task,source in tasks:
 oracle=D/(task+'-oracle');q=subprocess.run([C,source,oracle,'--opt','--compact'],capture_output=True,check=True);expected=oracle.read_bytes()
 for trial in range(N):
  order=variants[:];random.Random(28000+trial).shuffle(order)
  for variant in order:
   out=D/f'out-{len(rows)}';cache=D/f'cache-{len(rows)}';cache.mkdir(mode=0o700);builder=OLD if variant==variants[0]else NEW;args=[builder,C,source,out,cache,'--opt','--compact']
   if variant==variants[2]:args+=['--compiler-store',store]
   start=time.perf_counter_ns();q=subprocess.run(args,capture_output=True,timeout=30,env={'PATH':'/nonexistent'});ms=(time.perf_counter_ns()-start)/1e6;assert q.returncode==0,q.stderr;assert json.loads(q.stdout)['cache']=='miss';assert out.read_bytes()==expected;assert (store/compiler_name).stat().st_ino==original_inode
   rows.append(dict(task=task,trial=trial,variant=variant,ms=ms,unsignedSHA256=hashlib.sha256(expected).hexdigest()))
summary=[]
for task,_ in tasks:
 med={v:statistics.median(x['ms']for x in rows if x['task']==task and x['variant']==v)for v in variants};summary.append({'task':task,'medianMs':med,'previousOverRetainedRatio':med[variants[0]]/med[variants[2]],'newDefaultOverRetainedRatio':med[variants[1]]/med[variants[2]]})
report={'passed':True,'schema':'rf2.compiler.store.measurements.v1','trialsPerVariant':N,'summary':summary,'raw':rows,'firstStoreSetupMs':setup_ms,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'builderSHA256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [OLD,NEW]},'sourceSHA256':{name:hashlib.sha256(p.read_bytes()).hexdigest()for name,p in tasks},'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'host':platform.platform(),'limits':'One host warm filesystem. Every timed target cache starts empty. Retained-store variant reuses a checked compiler inode after separately reported one-time store setup; this is not a faster first-ever compiler launch. Complete build/publication time, no application-runtime, energy, token or cross-platform claim.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'summary':summary,'firstStoreSetupMs':setup_ms}))
