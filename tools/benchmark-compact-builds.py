"""Matched legacy/compact native build tasks; observations are not joule measurements."""
from pathlib import Path
import subprocess,time,os,json,hashlib,random,statistics,resource,platform,shutil
R=Path(__file__).resolve().parents[1];D=R/'artifacts/compact-images'/('bench-'+str(time.time_ns()));D.mkdir(parents=True)
oldc=Path(os.environ['RF2_OLD_COMPILER']).resolve();oldb=Path(os.environ['RF2_OLD_BUILDER']).resolve();newc=Path(os.environ['RF2_TEST_COMPILER']).resolve();newb=Path(os.environ['RF2_BUILD_BIN']).resolve();trials=int(os.environ.get('RF2_BENCH_TRIALS','21'));assert 5<=trials<=101
cache={}
for family in ['old','new']:cache[family]=D/f'{family}-cache';cache[family].mkdir(mode=0o700)
runtime=D/'runtime.rf2';runtime.write_text(''.join((R/x).read_text()for x in ['native/rf2.rf2','native/core.rf2','native/attendance.rf2','native/attendance-kernel.rf2','native/fingerprint.rf2','native/invoice.rf2','native/invoice-kernel.rf2','native/prepared.rf2','native/workspace.rf2','native/editor.rf2']))
tasks=[('compiler',R/'native/compiler/compiler.rf2'),('runtime',runtime),('checksum',R/'examples/file-checksum.rf2')];raw=[];sizes={}
variants=['old direct','old forced','old warm','old cold','compact direct','compact forced','compact warm','compact cold']
for task,source in tasks:
 expected={}
 for family,c,b,flags in [('old',oldc,oldb,[]),('new',newc,newb,['--compact'])]:
  out=D/f'{task}-{family}-oracle';q=subprocess.run([c,source,out,'--opt',*flags],capture_output=True,timeout=30,env={'PATH':'/nonexistent'});assert q.returncode==0,q.stderr;expected[family]=out.read_bytes();sizes[task+' '+family]=len(expected[family]);out=D/f'{task}-{family}-warmup';q=subprocess.run([b,c,source,out,cache[family],'--opt',*flags],capture_output=True,timeout=30,env={'PATH':'/nonexistent'});assert q.returncode==0 and out.read_bytes()==expected[family],q.stderr
 for trial in range(trials):
  order=variants[:];random.Random(271113+trial).shuffle(order)
  for variant in order:
   family='old'if variant.startswith('old')else'new';c=oldc if family=='old'else newc;b=oldb if family=='old'else newb;flags=[]if family=='old'else['--compact'];out=D/f'out-{len(raw)}';selected_cache=cache[family]
   if variant.endswith('cold'):selected_cache=D/f'cold-{len(raw)}';selected_cache.mkdir(mode=0o700)
   cmd=[c,source,out,'--opt',*flags]if variant.endswith('direct')else[b,c,source,out,selected_cache,'--opt',*flags,*(['--clean']if variant.endswith('forced')else[])];ru=resource.getrusage(resource.RUSAGE_CHILDREN);cpu0=ru.ru_utime+ru.ru_stime;start=time.perf_counter_ns();q=subprocess.run(cmd,capture_output=True,timeout=30,env={'PATH':'/nonexistent'});elapsed=(time.perf_counter_ns()-start)/1e6;ru=resource.getrusage(resource.RUSAGE_CHILDREN);cpu=(ru.ru_utime+ru.ru_stime-cpu0)*1000;assert q.returncode==0 and out.read_bytes()==expected[family],(task,variant,q.stderr)
   if not variant.endswith('direct'):assert json.loads(q.stdout)['cache']==('hit'if variant.endswith('warm')else'miss')
   raw.append({'task':task,'trial':trial,'variant':variant,'ms':elapsed,'observedChildCpuMs':cpu,'unsignedBytes':out.stat().st_size});out.unlink()
   if variant.endswith('cold'):shutil.rmtree(selected_cache)
rows=[]
for task,_ in tasks:
 med={v:statistics.median(x['ms']for x in raw if x['task']==task and x['variant']==v)for v in variants};pairs={}
 for old,new in [('old warm','compact warm'),('old forced','compact forced'),('old direct','compact direct'),('old cold','compact cold')]:
  a=[x['ms']for x in raw if x['task']==task and x['variant']==old];b=[x['ms']for x in raw if x['task']==task and x['variant']==new];delta=[y-x for x,y in zip(a,b)];rng=random.Random(271113);bs=sorted(statistics.median(rng.choices(delta,k=trials))for _ in range(10000));pairs[new]={'candidateMinusLegacyPairedMedianMs':statistics.median(delta),'bootstrap95Ms':[bs[250],bs[9749]],'legacyOverCompactRatio':med[old]/med[new]}
 rows.append({'task':task,'medianMs':med,'comparisons':pairs})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'passed':True,'schema':'rf2.compact.build.measurements.v1','trialsPerTaskVariant':trials,'rows':rows,'unsignedImageBytes':sizes,'raw':raw,'binarySHA256':{str(p):sha(p)for p in [oldc,oldb,newc,newb]},'controllerSHA256':sha(Path(__file__)),'host':platform.platform(),'limits':'One host, warm filesystem, rotated process-inclusive build and output-publication tasks; cold variants use a fresh empty cache and include compiler snapshot creation; forced and warm variants reuse an existing cache. Each format compared byte-for-byte against its own direct clean oracle; legacy and compact layouts intentionally differ. Child CPU observations are not watts, joules, physical memory, model tokens or Clang/Python runtime comparisons.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'rows':rows,'unsignedImageBytes':sizes}))
