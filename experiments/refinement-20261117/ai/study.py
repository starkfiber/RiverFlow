"""Matched C/D source-proposal study. No network/native action on import or freeze."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,subprocess,sys,tempfile,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PIN='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
ORDER=[('C','manual'),('D','cli'),('C','cli'),('D','manual')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p,name):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def freeze(a):
    assert sha(a.compiler)==PIN;validation=a.golden_validation.resolve();g=json.loads(validation.read_text());assert g['allPassed']and len(g['runs'])==8 and g['conditionAdmissionControlsPassed']and all(x['passed']for x in g['conditionCompilerControls'])
    assert all(r['allPassed']and r['sourceSHA256']==sha(HERE/('golden-'+r['label'].split('-')[0]+'-'+r['label'].split('-')[1]+'.flow'))for r in g['runs'])
    sdk=Path(g['SDK']).resolve();assert sha(sdk/'text-report-cli.flow')==sha(ROOT/'experiments/acceptance-20261117/ai/text-report-cli.flow')
    assert all(sha(sdk/name)==want for name,want in g['SDKfiles'].items());assert g['oracleSHA256']==sha(HERE/'grade.py')
    d=a.out.resolve();d.mkdir(parents=True,exist_ok=False)
    names=['PROTOCOL.md','TASK-C.md','TASK-D.md','COMMON-GUIDE.md','study.py','grade.py','validate_goldens.py','make_goldens.py','golden-C-manual.flow','golden-C-cli.flow','golden-D-manual.flow','golden-D-cli.flow','controller_controls.py','manual-own-report.flow','manual-undefined-report.flow']
    files=[HERE/n for n in names]+[validation,validation.parent/'CONDITION-CONTROLS.json',ROOT/'experiments/acceptance-20261117/ai/transport.py',ROOT/'experiments/acceptance-20261117/ai/style.flow']+sorted(p for p in sdk.iterdir()if p.is_file())
    assert all(p.is_file()and not p.is_symlink()for p in files)
    f={'schema':'rf2.refinement.matched-study.freeze.v1','order':ORDER,'model':'deepseek-v4-pro','thinking':'enabled','effort':'low','maxCompletionTokens':10000,'httpTimeout':180,'transportTimeout':195,'maxCalls':8,'initialCalls':4,'repairsPerAttempt':1,'compiler':str(a.compiler.resolve()),'compilerSHA256':PIN,'SDK':str(sdk),'goldenValidationSHA256':sha(validation),'inputs':{str(p.resolve()):sha(p)for p in files},'guide':'Same COMMON-GUIDE.md bytes in every condition; only condition permission differs','retention':'project-local only; no Memory/KHC/Chain','scope':'Four ordered matched engineering attempts, no randomized population or causal universal saving claim'}
    (d/'FROZEN.json').write_text(json.dumps(f,indent=2)+'\n');print(json.dumps({'frozen':str(d/'FROZEN.json'),'sha256':sha(d/'FROZEN.json'),'providerCalls':0,'nativeRuns':0}))
def frozen(d):
    f=json.loads((d/'FROZEN.json').read_text());assert sha(f['compiler'])==PIN
    for p,want in f['inputs'].items():assert sha(p)==want,'Frozen input drift: '+p
    return f

def call(a):
    d=a.out.resolve();f=frozen(d);assert a.approved_freeze_sha==sha(d/'FROZEN.json'),'Root-reviewed frozen hash required'
    assert a.attempt in range(1,5)and a.round in [1,2];task,condition=ORDER[a.attempt-1];attempt=d/('attempt-'+str(a.attempt)+'-'+task+'-'+condition)
    assert len(list(d.glob('attempt-*/round-*/RECEIPT.json')))<8
    if a.attempt>1:assert(d/('attempt-'+str(a.attempt-1)+'-'+ORDER[a.attempt-2][0]+'-'+ORDER[a.attempt-2][1])/'CLOSED.json').exists(),'Close previous attempt before advancing'
    previous=attempt/'round-1'
    if a.round==2:
        assert(previous/'ASSESSMENT.json').exists(),'Repair only from actual reviewed native/controller feedback'
        assessed=json.loads((previous/'ASSESSMENT.json').read_text());assert not assessed['allPassed'];assert not(attempt/'CLOSED.json').exists()
    else:assert not attempt.exists(),'One initial call only; preserve failures'
    attempt.mkdir(exist_ok=True);r=attempt/('round-'+str(a.round));r.mkdir(exist_ok=False)
    content=(HERE/'COMMON-GUIDE.md').read_text()+'\nCONDITION: '+condition.upper()+'\nTASK\n'+(HERE/('TASK-'+task+'.md')).read_text()
    if a.round==2:content+='\nPREVIOUS PROPOSED SOURCE\n'+(previous/'main.flow').read_text()+'\nACTUAL CONTROLLER FEEDBACK\n'+json.dumps(assessed,ensure_ascii=False)
    assert len(content.encode())<=50000
    payload={'model':f['model'],'thinking':{'type':'enabled'},'reasoning_effort':f['effort'],'messages':[{'role':'system','content':'Implement the complete RF2 task and respect the supplied condition/import permissions. Return strict JSON exactly {"source":"complete main.flow"}. Source proposal only; no commands or execution claims.'},{'role':'user','content':content}],'max_tokens':10000,'stream':False,'response_format':{'type':'json_object'}}
    raw=json.dumps(payload,ensure_ascii=False).encode();(r/'request.json').write_bytes(raw);start=time.monotonic();receipt={'attempt':a.attempt,'round':a.round,'task':task,'condition':condition,'requestSHA256':hashlib.sha256(raw).hexdigest(),'frozenSHA256':sha(d/'FROZEN.json'),'automaticRetry':False,'sourceExecuted':False}
    try:
        command=load(ROOT/'experiments/acceptance-20261117/ai/transport.py','transport').remote_command(180)
        q=subprocess.run(command,input=raw,capture_output=True,timeout=195);receipt['transportExit']=q.returncode
        if q.returncode:receipt.update(failure='transport failure; no retry/repair without actual source assessment',stderr=q.stderr.decode(errors='replace')[:700])
        else:
            data=json.loads(q.stdout);(r/'response.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');choice=data['choices'][0];receipt.update(servedModel=data.get('model'),usage=data.get('usage'),finishReason=choice.get('finish_reason'))
            if choice.get('finish_reason')!='stop':receipt['failure']='incomplete completion; no assessment/repair'
            else:
                result=json.loads(choice['message']['content']);assert set(result)=={'source'}and isinstance(result['source'],str)
                source=result['source'].encode();assert 0<len(source)<=65536;(r/'main.flow').write_bytes(source);receipt['sourceSHA256']=sha(r/'main.flow')
    except(Exception,KeyboardInterrupt)as e:receipt['failure']=type(e).__name__+': '+str(e)[:700]
    receipt['elapsedSeconds']=time.monotonic()-start;(r/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

def condition_errors(text,condition):
    imports=re.findall(r'^[ \t]*use[ \t]+"([^"\n]+)"[ \t]*(?:#[^\n]*)?$',text,re.M)
    errors=[]
    allowed='@rf2/v1/text.flow'if condition=='manual'else'@rf2/v1/text-report-cli.flow'
    if imports!=[allowed]:errors.append('Condition requires exactly the documented '+allowed+' import; no local/additional imports')
    # This is a condition check, not a security sandbox; root reviews actual effects.
    code=re.sub(r'"(?:\\.|[^"\\])*"|#[^\n]*',' ',text)
    # Manual implementations may define their own report records/helpers. Imports
    # establish the SDK boundary; the compiler rejects undefined SDK symbols.
    if condition=='cli'and not(re.search(r'\bfn\s+text_report_fields\s*\(',code)and re.search(r'\btext_report_entry\s*\(',code)):errors.append('CLI condition requires callback plus main delegation')
    return errors

def assess(a):
    d=a.out.resolve();f=frozen(d);task,condition=ORDER[a.attempt-1];r=d/('attempt-'+str(a.attempt)+'-'+task+'-'+condition)/('round-'+str(a.round));source=r/'main.flow'
    assert sha(source)==a.reviewed_sha,'Separate exact source review required';assert not(r/'ASSESSMENT.json').exists();receipt=json.loads((r/'RECEIPT.json').read_text());assert receipt['sourceSHA256']==a.reviewed_sha
    result={'sourceSHA256':a.reviewed_sha,'manualReviewConfirmed':True,'allPassed':False,'conditionErrors':condition_errors(source.read_text(),condition)};start=time.monotonic()
    if result['conditionErrors']:result['feedback']=result['conditionErrors']
    else:
        assert os.environ.get('TMPDIR','').startswith('/Volumes/Mac Work Cache/'),'Use guarded local cache runner'
        tmp=Path(tempfile.mkdtemp(prefix='rf2-cd-assessment-',dir=os.environ['TMPDIR']));binary=tmp/'program'
        cmd=[f['compiler'],str(source),str(binary),'--compact','--opt','--sdk-root',f['SDK'],'--diagnostic-json']
        try:
            q=subprocess.run(cmd,capture_output=True,timeout=30);(r/'compile.stdout').write_bytes(q.stdout);(r/'compile.stderr').write_bytes(q.stderr);result.update(compileCommand=cmd,compileExit=q.returncode)
            if q.returncode:result['feedback']=q.stderr.decode(errors='replace')[:3000]
            else:
                subprocess.run(['codesign','-s','-',str(binary)],capture_output=True,check=True,timeout=10);result['binarySHA256']=sha(binary)
                q=subprocess.run([sys.executable,'-B',str(HERE/'grade.py'),task,'--binary',str(binary),'--out',str(r/'grade')],capture_output=True,timeout=180);(r/'grade.stdout').write_bytes(q.stdout);(r/'grade.stderr').write_bytes(q.stderr)
                if(r/'grade/RESULTS.json').exists():
                    g=json.loads((r/'grade/RESULTS.json').read_text());result.update(allPassed=g['allPassed'],passed=g['passed'],total=g['total'],feedback=[x for x in g['cases']if not x['passed']][:6])
                else:result['feedback']='grader failed: '+q.stderr.decode(errors='replace')[:2500]
        except(Exception,KeyboardInterrupt)as e:result['feedback']=type(e).__name__+': '+str(e)[:1200]
    result['buildAndTestSeconds']=time.monotonic()-start;(r/'ASSESSMENT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

def close(a):
    d=a.out.resolve();f=frozen(d);task,condition=ORDER[a.attempt-1];attempt=d/('attempt-'+str(a.attempt)+'-'+task+'-'+condition);assert not(attempt/'CLOSED.json').exists()
    receipts=sorted(attempt.glob('round-*/RECEIPT.json'));assert receipts
    last=receipts[-1];r=json.loads(last.read_text());assessment=last.parent/'ASSESSMENT.json'
    if r.get('sourceSHA256'):assert assessment.exists(),'Source needs actual review/assessment before closing'
    assessed=json.loads(assessment.read_text())if assessment.exists()else None
    if assessed and not assessed['allPassed']and r['round']==1:assert a.no_repair_reason,'Explicit reason required when declining available feedback repair'
    record={'task':task,'condition':condition,'rounds':len(receipts),'allPassed':bool(assessed and assessed['allPassed']),'lastReceiptSHA256':sha(last),'declinedRepairReason':a.no_repair_reason};(attempt/'CLOSED.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))

def costs(rows):
    usage=[x['usage']for x in rows if isinstance(x.get('usage'),dict)];unknown=len(rows)-len(usage)
    return {'knownRequests':len(usage),'unknownUsageRequests':unknown,'knownPromptTokens':sum(x.get('prompt_tokens',0)for x in usage),'knownCompletionTokens':sum(x.get('completion_tokens',0)for x in usage),'knownProviderTotalTokens':sum(x.get('total_tokens',0)for x in usage),'reasoningSubsetOfCompletion':sum(x.get('completion_tokens_details',{}).get('reasoning_tokens',0)for x in usage),'cacheSubsetOfPrompt':sum(x.get('prompt_tokens_details',{}).get('cached_tokens',0)for x in usage),'observedRequestSeconds':sum(x.get('elapsedSeconds',0)for x in rows),'buildTestSeconds':sum((x.get('assessment')or{}).get('buildAndTestSeconds',0)for x in rows)}
def summary(a):
    d=a.out.resolve();f=frozen(d);attempts=[];conditions={}
    for i,(task,condition)in enumerate(ORDER,1):
        attempt=d/('attempt-'+str(i)+'-'+task+'-'+condition);rows=[]
        for p in sorted(attempt.glob('round-*/RECEIPT.json')):
            row=json.loads(p.read_text());ap=p.parent/'ASSESSMENT.json';row['assessment']=json.loads(ap.read_text())if ap.exists()else None;rows.append(row)
        passed=any((x.get('assessment')or{}).get('allPassed')for x in rows);attempts.append({'attempt':i,'task':task,'condition':condition,'rounds':rows,'allRoundsCost':costs(rows),'passed':passed,'closed':(attempt/'CLOSED.json').exists()});conditions.setdefault(condition,[]).append(attempts[-1])
    groups={}
    for condition,items in conditions.items():
        allrows=[r for x in items for r in x['rounds']];cost=costs(allrows);passed=sum(x['passed']for x in items);groups[condition]={'tasksPassed':passed,'tasksDeclared':2,'costIncludingFailures':cost,'knownTokensPerPassingTask':cost['knownProviderTotalTokens']/passed if passed and cost['unknownUsageRequests']==0 else None}
    result={'schema':'rf2.refinement.matched-study.summary.v1','frozenSHA256':sha(d/'FROZEN.json'),'attempts':attempts,'conditions':groups,'scope':'Four ordered engineering attempts on two complete tasks; not randomized population/causal generalization, billing or source-size proxy'}
    dest=d/('SUMMARY-'+str(time.time_ns())+'.json');dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'summary':str(dest),'conditions':groups}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','call','assess','close','summary']);p.add_argument('--out',type=Path,required=True);p.add_argument('--compiler',type=Path);p.add_argument('--golden-validation',type=Path);p.add_argument('--attempt',type=int,choices=[1,2,3,4]);p.add_argument('--round',type=int,choices=[1,2]);p.add_argument('--approved-freeze-sha');p.add_argument('--reviewed-sha');p.add_argument('--no-repair-reason');a=p.parse_args();globals()[a.action](a)
