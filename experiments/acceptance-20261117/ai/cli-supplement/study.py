"""Predeclared, two-call CLI-library condition; no provider/native action on import."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,time,uuid
HERE=Path(__file__).resolve().parent;AI=HERE.parent;ROOT=AI.parents[2]
COMPILER_SHA='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def freeze(a):
    assert a.prior_study,'Supply historical study roots; original/repair costs must remain visible'
    d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);assert sha(a.compiler)==COMPILER_SHA
    sdk=a.sdk_root.resolve();assert(sdk/'text-report-cli.flow').is_file()
    assert sha(sdk/'text-report-cli.flow')==sha(AI/'text-report-cli.flow')
    guide=load(AI/'study-wide.py','original_guide').guide('report')+'\n'+(AI/'CLI-API.md').read_text()+'''\nCLI LIBRARY CONDITION: import @rf2/v1/text-report-cli.flow. Implement the synchronous text_report_fields callback and main delegation. The library performs required shared argument/file validation and report output; implement task-specific calculations in the callback. Keep the exact task semantics. No task solution is supplied.\n'''
    (d/'guide.md').write_text(guide)
    files=[HERE/'PROTOCOL.md',Path(__file__),AI/'study-wide.py',AI/'style.flow',AI/'CLI-API.md',AI/'text-report-cli.flow',AI/'TASK-A.md',AI/'TASK-B.md',AI/'grade.py',AI/'transport.py',ROOT/'experiments/evolution-20261117/report/REPORT-API.md',ROOT/'experiments/sdk-task/SDK-RF2.md',d/'guide.md']
    files+=sorted(sdk.rglob('*'));files=[p for p in files if p.is_file()]
    assert all(not p.is_symlink()for p in files),'Freeze regular reviewed inputs only'
    historical=[]
    for prior in a.prior_study:
        receipts=sorted(prior.resolve().glob('attempt-*/round-*/RECEIPT.json'));assert 0<len(receipts)<=32
        for p in receipts:
            r=json.loads(p.read_text());assessment=p.parent/'ASSESSMENT.json'
            historical.append({'study':str(prior.resolve()),'receipt':str(p),'receiptSHA256':sha(p),'attempt':r.get('attempt'),'round':r.get('round'),'task':r.get('task'),'condition':r.get('condition'),'usage':r.get('usage'),'servedModel':r.get('servedModel'),'finishReason':r.get('finishReason'),'failure':r.get('failure'),'elapsedSeconds':r.get('elapsedSeconds'),'assessment':json.loads(assessment.read_text())if assessment.exists()else None})
            files.append(p)
            if assessment.exists():files.append(assessment)
    (d/'HISTORICAL-COSTS.json').write_text(json.dumps(historical,indent=2)+'\n');files.append(d/'HISTORICAL-COSTS.json')
    f={'schema':'rf2.cli-supplement.freeze.v1','condition':'new nonrandomized CLI-library condition, not matched causal token proof','order':['A','B'],'model':'deepseek-v4-pro','thinking':'enabled','effort':'low','maxCompletionTokens':10000,'httpTimeout':180,'transportTimeout':195,'maxCalls':2,'repairs':0,'compiler':str(a.compiler.resolve()),'compilerSHA256':COMPILER_SHA,'SDK':str(sdk),'inputs':{str(p.resolve()):sha(p)for p in files},'retention':'project-local only; no Memory/Chain/shared jobs'}
    (d/'FROZEN.json').write_text(json.dumps(f,indent=2)+'\n');print(json.dumps({'frozen':str(d/'FROZEN.json'),'sha256':sha(d/'FROZEN.json'),'providerCalls':0,'nativeExecutions':0}))
def frozen(d):
    f=json.loads((d/'FROZEN.json').read_text())
    for p,want in f['inputs'].items():assert sha(p)==want,'Frozen input drift: '+p
    assert sha(f['compiler'])==f['compilerSHA256'];return f
def call(a):
    d=a.out.resolve();f=frozen(d);assert a.approved_freeze_sha==sha(d/'FROZEN.json'),'Explicit reviewed frozen-input hash required before provider call';assert a.attempt in [1,2]
    if a.attempt==2:assert(d/'attempt-1/RECEIPT.json').exists(),'Preserve fixed A/B order'
    assert len(list(d.glob('attempt-*/RECEIPT.json')))<2
    r=d/f'attempt-{a.attempt}';r.mkdir(exist_ok=False);task=f['order'][a.attempt-1]
    content=(d/'guide.md').read_text()+'\nTASK\n'+(AI/f'TASK-{task}.md').read_text();assert len(content.encode())<=40000
    payload={'model':f['model'],'thinking':{'type':'enabled'},'reasoning_effort':f['effort'],'messages':[{'role':'system','content':'Implement the complete RF2 task using only the supplied language/SDK. Return strict JSON exactly {"source":"complete main.flow"}. Propose source only, no commands or execution claims.'},{'role':'user','content':content}],'max_tokens':10000,'stream':False,'response_format':{'type':'json_object'}}
    raw=json.dumps(payload,ensure_ascii=False).encode();(r/'request.json').write_bytes(raw);started=time.monotonic();receipt={'attempt':a.attempt,'round':1,'task':task,'condition':'cli-library-supplement','requestSHA256':hashlib.sha256(raw).hexdigest(),'frozenSHA256':sha(d/'FROZEN.json'),'sourceExecuted':False,'automaticRetry':False}
    try:
        command=load(AI/'transport.py','provider_transport').remote_command(180)
        q=subprocess.run(command,input=raw,capture_output=True,timeout=195);receipt['transportExit']=q.returncode
        if q.returncode:receipt.update(failure='transport failure, call consumed',stderr=q.stderr.decode(errors='replace')[:700])
        else:
            data=json.loads(q.stdout);(r/'response.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');choice=data['choices'][0];receipt.update(servedModel=data.get('model'),usage=data.get('usage'),finishReason=choice.get('finish_reason'))
            if choice.get('finish_reason')!='stop':receipt['failure']='incomplete completion, call consumed'
            else:
                result=json.loads(choice['message']['content']);assert set(result)=={'source'}and isinstance(result['source'],str)
                source=result['source'].encode();assert 0<len(source)<=65536;(r/'main.flow').write_bytes(source);receipt['sourceSHA256']=sha(r/'main.flow')
    except(Exception,KeyboardInterrupt)as e:receipt['failure']=type(e).__name__+': '+str(e)[:700]
    receipt['elapsedSeconds']=time.monotonic()-started;(r/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
def assess(a):
    d=a.out.resolve();f=frozen(d);r=d/f'attempt-{a.attempt}';source=r/'main.flow';assert sha(source)==a.reviewed_sha,'Separate manual review hash required';assert not(r/'ASSESSMENT.json').exists()
    receipt=json.loads((r/'RECEIPT.json').read_text());assert receipt['sourceSHA256']==a.reviewed_sha
    text=source.read_text();assert 'use "@rf2/v1/text-report-cli.flow"'in text and 'text_report_entry('in text and 'fn text_report_fields('in text,'CLI-library condition requires reviewed shared API use'
    assert os.environ.get('TMPDIR','').startswith('/Volumes/Mac Work Cache/'),'Use guarded local bank runner after checking status'
    tmp=Path(os.environ['TMPDIR'])/('rf2-cli-supplement-'+uuid.uuid4().hex);tmp.mkdir();binary=tmp/'program';started=time.monotonic()
    cmd=[f['compiler'],str(source),str(binary),'--compact','--opt','--sdk-root',f['SDK'],'--diagnostic-json']
    q=subprocess.run(cmd,capture_output=True,timeout=30);(r/'compile.stdout').write_bytes(q.stdout);(r/'compile.stderr').write_bytes(q.stderr)
    result={'sourceSHA256':a.reviewed_sha,'manualReviewConfirmed':True,'compileCommand':cmd,'compileExit':q.returncode,'allPassed':False}
    if q.returncode:result['feedback']=q.stderr.decode(errors='replace')[:3000]
    else:
        subprocess.run(['codesign','-s','-',str(binary)],capture_output=True,check=True)
        g=subprocess.run([sys.executable,'-B',str(AI/'grade.py'),f['order'][a.attempt-1],'--binary',str(binary),'--out',str(r/'grade')],capture_output=True,timeout=120);(r/'grade.stdout').write_bytes(g.stdout);(r/'grade.stderr').write_bytes(g.stderr)
        result['binarySHA256']=sha(binary)
        if(r/'grade/RESULTS.json').exists():
            x=json.loads((r/'grade/RESULTS.json').read_text());result.update(allPassed=x['allPassed'],passed=x['passed'],total=x['total'])
        else:result['feedback']='grader failed: '+g.stderr.decode(errors='replace')[:2500]
    result['buildAndTestSeconds']=time.monotonic()-started;(r/'ASSESSMENT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
def summary(a):
    d=a.out.resolve();f=frozen(d);attempts=[]
    for i in [1,2]:
        p=d/f'attempt-{i}/RECEIPT.json'
        if p.exists():
            row=json.loads(p.read_text());assessment=p.parent/'ASSESSMENT.json';row['assessment']=json.loads(assessment.read_text())if assessment.exists()else None;attempts.append(row)
    report={'schema':'rf2.cli-supplement.summary.v1','condition':f['condition'],'historicalAttemptsAndRepairsSeparate':json.loads((d/'HISTORICAL-COSTS.json').read_text()),'newConditionAttempts':attempts,'newTasksPassed':sum(bool(x.get('assessment')and x['assessment'].get('allPassed'))for x in attempts),'usageInterpretation':'Raw provider usage per attempt; missing usage unknown. Reasoning may be a completion subset. No source-size proxy, causal saving or billing claim.'}
    (d/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'attempts':len(attempts),'newTasksPassed':report['newTasksPassed']}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','call','assess','summary']);p.add_argument('--out',type=Path,required=True);p.add_argument('--compiler',type=Path);p.add_argument('--sdk-root',type=Path);p.add_argument('--prior-study',type=Path,action='append',default=[]);p.add_argument('--attempt',type=int,choices=[1,2]);p.add_argument('--reviewed-sha');p.add_argument('--approved-freeze-sha');a=p.parse_args();globals()[a.action](a)
