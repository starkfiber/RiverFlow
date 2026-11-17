"""Explicitly separate bounded output-contract pilot; no action on import."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys,tempfile,time
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PIN='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def freeze(a):
    prior=a.prior.resolve();old=json.loads((prior/'FROZEN.json').read_text())
    for i,(task,condition)in enumerate([('C','manual'),('D','cli'),('C','cli'),('D','manual')],1):assert(prior/('attempt-'+str(i)+'-'+task+'-'+condition)/'CLOSED.json').exists(),'Close complete prior study first'
    assert sha(old['compiler'])==PIN
    for p,want in old['inputs'].items():assert sha(p)==want
    request=a.request.resolve();payload=json.loads(request.read_text());assert payload['model']=='deepseek-v4-pro'and payload['thinking']=={'type':'enabled'}and payload['reasoning_effort']=='low'and payload['max_tokens']==10000
    assert payload['response_format']=={'type':'json_object'}and not payload['stream']
    assert '"source":"complete main.flow"' not in request.read_text()
    sdk=Path(old['SDK']);files=[Path(__file__).resolve(),HERE/'PROMPT-CONTRACT-PILOT.md',HERE/'study.py',HERE/'grade.py',HERE/'COMMON-GUIDE.md',HERE/'TASK-C.md',ROOT/'experiments/acceptance-20261117/ai/transport.py',request,prior/'FROZEN.json']+sorted(prior.glob('attempt-*/CLOSED.json'))+sorted(p for p in sdk.iterdir()if p.is_file())
    d=a.out.resolve();d.mkdir(parents=True,exist_ok=False)
    f={'schema':'rf2.refinement.prompt-contract-pilot.freeze.v1','task':'C','condition':'cli','priorStudy':str(prior),'initialRequest':str(request),'initialRequestSHA256':sha(request),'compiler':old['compiler'],'compilerSHA256':PIN,'SDK':str(sdk),'maxCalls':2,'maxRepairs':1,'httpTimeout':180,'transportTimeout':195,'initialThenActualFeedbackRepair':True,'automaticRetry':False,'inputs':{str(p):sha(p)for p in files},'scope':'Separate prompt-contract repair pilot, no manual/CLI comparison or causal token-saving claim','retention':'Project local; no Memory/KHC/Chain'}
    (d/'FROZEN.json').write_text(json.dumps(f,indent=2)+'\n');print(json.dumps({'frozen':str(d/'FROZEN.json'),'sha256':sha(d/'FROZEN.json'),'providerCalls':0}))
def frozen(d):
    f=json.loads((d/'FROZEN.json').read_text());assert sha(f['compiler'])==PIN
    for p,want in f['inputs'].items():assert sha(p)==want,'Frozen pilot drift: '+p
    return f

def call(a):
    d=a.out.resolve();f=frozen(d);assert a.approved_freeze_sha==sha(d/'FROZEN.json'),'Root-reviewed frozen pilot hash required'
    assert a.round in [1,2]and not(d/'CLOSED.json').exists();assert len(list(d.glob('round-*/RECEIPT.json')))<2
    payload=json.loads(Path(f['initialRequest']).read_text())
    if a.round==2:
        previous=d/'round-1';assessed=json.loads((previous/'ASSESSMENT.json').read_text());assert not assessed['allPassed']
        payload['messages'][-1]['content']+='\nPREVIOUS PROPOSED SOURCE\n'+(previous/'main.flow').read_text()+'\nACTUAL CONTROLLER FEEDBACK\n'+json.dumps(assessed,ensure_ascii=False)
    else:assert not(d/'round-1').exists()
    raw=json.dumps(payload,ensure_ascii=False).encode();assert len(raw)<=120000
    r=d/('round-'+str(a.round));r.mkdir(exist_ok=False);(r/'request.json').write_bytes(raw)
    receipt={'round':a.round,'task':'C','condition':'cli','requestSHA256':sha(r/'request.json'),'frozenSHA256':sha(d/'FROZEN.json'),'automaticRetry':False,'sourceExecuted':False};start=time.monotonic()
    try:
        command=load(ROOT/'experiments/acceptance-20261117/ai/transport.py','transport').remote_command(180)
        q=subprocess.run(command,input=raw,capture_output=True,timeout=195);receipt['transportExit']=q.returncode
        if q.returncode:receipt.update(failure='Transport failed; no automatic retry',stderr=q.stderr.decode(errors='replace')[:700])
        else:
            data=json.loads(q.stdout);(r/'response.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');choice=data['choices'][0];receipt.update(servedModel=data.get('model'),usage=data.get('usage'),finishReason=choice.get('finish_reason'))
            if choice.get('finish_reason')!='stop':receipt['failure']='Incomplete completion; no assessment or retry'
            else:
                result=json.loads(choice['message']['content']);assert set(result)=={'source'}and isinstance(result['source'],str)
                source=result['source'].encode();assert 0<len(source)<=65536;(r/'main.flow').write_bytes(source);receipt['sourceSHA256']=sha(r/'main.flow')
    except subprocess.TimeoutExpired:receipt['failure']='TimeoutExpired: provider transport observation budget elapsed; usage unknown'
    except(Exception,KeyboardInterrupt)as e:receipt['failure']=type(e).__name__+': '+str(e)[:700]
    receipt['elapsedSeconds']=time.monotonic()-start;(r/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

def assess(a):
    d=a.out.resolve();f=frozen(d);r=d/('round-'+str(a.round));source=r/'main.flow'
    assert sha(source)==a.reviewed_sha;assert not(r/'ASSESSMENT.json').exists();receipt=json.loads((r/'RECEIPT.json').read_text());assert receipt['sourceSHA256']==a.reviewed_sha
    text=source.read_text();errors=load(HERE/'study.py','study').condition_errors(text,'cli')
    if not text.lstrip().startswith('profile RF2_SYSTEM_A64_V1'):errors.append('source must contain actual program text beginning with the required profile')
    result={'sourceSHA256':a.reviewed_sha,'manualReviewConfirmed':True,'allPassed':False,'conditionErrors':errors};start=time.monotonic()
    if errors:result['feedback']=errors
    else:
        assert os.environ.get('TMPDIR','').startswith('/Volumes/Mac Work Cache/'),'Use guarded disposable bank for native assessment'
        tmp=Path(tempfile.mkdtemp(prefix='rf2-contract-pilot-',dir=os.environ['TMPDIR']));binary=tmp/'program';cmd=[f['compiler'],str(source),str(binary),'--compact','--opt','--sdk-root',f['SDK'],'--diagnostic-json']
        try:
            q=subprocess.run(cmd,capture_output=True,timeout=30);(r/'compile.stdout').write_bytes(q.stdout);(r/'compile.stderr').write_bytes(q.stderr);result.update(compileCommand=cmd,compileExit=q.returncode)
            if q.returncode:result['feedback']=q.stderr.decode(errors='replace')[:3000]
            else:
                subprocess.run(['codesign','-s','-',str(binary)],capture_output=True,check=True,timeout=10);result['binarySHA256']=sha(binary)
                q=subprocess.run([sys.executable,'-B',str(HERE/'grade.py'),'C','--binary',str(binary),'--out',str(r/'grade')],capture_output=True,timeout=180);(r/'grade.stdout').write_bytes(q.stdout);(r/'grade.stderr').write_bytes(q.stderr)
                if(r/'grade/RESULTS.json').exists():
                    g=json.loads((r/'grade/RESULTS.json').read_text());result.update(allPassed=g['allPassed'],passed=g['passed'],total=g['total'],feedback=[x for x in g['cases']if not x['passed']][:6])
                else:result['feedback']='Grader failed: '+q.stderr.decode(errors='replace')[:2500]
        except(Exception,KeyboardInterrupt)as e:result['feedback']=type(e).__name__+': '+str(e)[:1200]
    result['buildAndTestSeconds']=time.monotonic()-start;(r/'ASSESSMENT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

def close(a):
    d=a.out.resolve();f=frozen(d);assert not(d/'CLOSED.json').exists();paths=sorted(d.glob('round-*/RECEIPT.json'));assert paths
    last=paths[-1];receipt=json.loads(last.read_text());assessment=last.parent/'ASSESSMENT.json'
    if receipt.get('sourceSHA256'):assert assessment.exists(),'Complete source needs root review and actual assessment'
    grade=json.loads(assessment.read_text())if assessment.exists()else None
    if grade and not grade['allPassed']and len(paths)==1:assert a.no_repair_reason
    rows=[]
    for p in paths:
        row=json.loads(p.read_text());ap=p.parent/'ASSESSMENT.json';row['assessment']=json.loads(ap.read_text())if ap.exists()else None;rows.append(row)
    record={'schema':'rf2.refinement.prompt-contract-pilot.closed.v1','allPassed':bool(grade and grade['allPassed']),'rounds':len(rows),'costIncludingFailures':load(HERE/'study.py','study').costs(rows),'declinedRepairReason':a.no_repair_reason,'scope':f['scope']};(d/'CLOSED.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','call','assess','close']);p.add_argument('--out',type=Path,required=True);p.add_argument('--prior',type=Path);p.add_argument('--request',type=Path);p.add_argument('--round',type=int,choices=[1,2]);p.add_argument('--approved-freeze-sha');p.add_argument('--reviewed-sha');p.add_argument('--no-repair-reason');a=p.parse_args();globals()[a.action](a)
