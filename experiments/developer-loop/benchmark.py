"""Frozen rotated warm compile comparison. No model/provider/runtime claims."""
from pathlib import Path
import hashlib,json,platform,shutil,statistics,subprocess,sys,tempfile,time
from replay import study_snapshot

R=Path(__file__).resolve().parents[2]
if len(sys.argv)!=4:raise SystemExit('benchmark.py BASELINE INITIAL_CANDIDATE RANGE_CANDIDATE')
compilers={name:Path(path).resolve()for name,path in zip(('baseline047','byteMap048A','rangeMap048B'),sys.argv[1:])}
D=Path(tempfile.mkdtemp(prefix='developer-loop-benchmark-',dir=R/'artifacts'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=D/'source';source.mkdir();small=source/'small.flow';small.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return argc+7\nend\n')
study=source/'study';study_snapshot(study)
compilerSource=source/'compiler.flow';shutil.copy2(compilers['rangeMap048B'].parent.parent/'compiler.flow',compilerSource)
workloads={'small':small,'studyRooms':study/'main.flow','compiler':compilerSource}
plan=dict(schema='rf2.developer-loop.compile-plan.v1',host=platform.platform(),compilerSHA256={k:sha(p)for k,p in compilers.items()},sourceFiles={str(p.relative_to(D)):sha(p)for p in source.rglob('*')if p.is_file()},warmups=2,trials=15,order='rotate three arms by trial index',options=['--compact','--opt'],scope='Whole native process compilation on one warm Mac. Signing, model authoring, tokens, app runtime and energy excluded. No adaptive sampling.')
(D/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(directory=str(D))),flush=True)
rows=[];digests={};names=list(compilers)
for workload,entry in workloads.items():
    digests[workload]={}
    for round in range(-2,15):
        order=names[round%3:]+names[:round%3]
        for arm in order:
            output=D/(workload+'-'+arm+'-'+str(round))
            started=time.perf_counter_ns()
            q=subprocess.run([str(compilers[arm]),str(entry),str(output),'--compact','--opt'],capture_output=True,timeout=60)
            elapsed=time.perf_counter_ns()-started
            row=dict(workload=workload,arm=arm,round=round,warmup=round<0,nanoseconds=elapsed,exit=q.returncode,stderr=q.stderr.decode(errors='replace'))
            rows.append(row);(D/'RAW.json').write_text(json.dumps(rows,indent=2)+'\n')
            if q.returncode:raise RuntimeError(row)
            value=sha(output);digests[workload].setdefault(arm,[]).append(value)
    assert len({digest for values in digests[workload].values()for digest in values})==1,('Unchanged source emitted different code',workload,digests[workload])
summary={}
for workload in workloads:
    summary[workload]={}
    for arm in names:
        values=[x['nanoseconds']/1e6 for x in rows if x['workload']==workload and x['arm']==arm and not x['warmup']]
        median=statistics.median(values)
        summary[workload][arm]=dict(trials=len(values),medianMS=median,minMS=min(values),maxMS=max(values),medianAbsoluteDeviationMS=statistics.median(abs(x-median)for x in values))
report=dict(plan=plan,planSHA256=sha(D/'PLAN.json'),rawSHA256=sha(D/'RAW.json'),summary=summary,unsignedImageSHA256={k:next(iter(v.values()))[0]for k,v in digests.items()},byteIdenticalAcrossArms=True)
(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(directory=str(D),summary=summary,byteIdenticalAcrossArms=True)),flush=True)
