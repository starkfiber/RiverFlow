"""Explicit bounded RF2 source campaign. Import/freeze never invoke a provider."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys,tempfile,time
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/refinement-20261117/ai'
PIN='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
ORDER=[('C','manual'),('D','cli'),('C','cli'),('D','manual')]
SYSTEM=('Implement the supplied RF2 task with exactly the permitted import. Return a JSON object with only source. '
        'The source value must be the entire actual compilable program, beginning with profile RF2_SYSTEM_A64_V1. '
        'Never return a placeholder, filename, description or Markdown. You are proposing source, not executing it. '
        'Do not invent APIs. Follow the supplied grammar and exact output bytes.')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,obj):Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def freeze(a):
 assert sha(a.compiler)==PIN
 g=read(a.golden_validation);assert g['allPassed'] and len(g['runs'])==8 and g['conditionAdmissionControlsPassed']
 assert all(x['passed']for x in g['conditionCompilerControls'])
 assert g['oracleSHA256']==sha(OLD/'grade.py')
 expected_labels={t+'-'+c+'-'+m for t,c in ORDER for m in ['plain','opt']}
 assert {r['label']for r in g['runs']}==expected_labels
 assert all(r['allPassed']and r['sourceSHA256']==sha(OLD/('golden-'+r['label'].split('-')[0]+'-'+r['label'].split('-')[1]+'.flow'))for r in g['runs'])
 sdk=Path(g['SDK']).resolve();assert all(sha(sdk/n)==v for n,v in g['SDKfiles'].items())
 files=list(HERE.glob('*.py'))+list(HERE.glob('*.md'))+[OLD/'study.py',OLD/'grade.py',a.golden_validation.resolve()]+sorted(p for p in sdk.iterdir()if p.is_file())
 assert all(p.is_file()and not p.is_symlink()for p in files)
 a.out.mkdir(parents=True,exist_ok=False)
 f={'schema':'rf2.ai-completion.freeze.v1','order':ORDER,'model':'deepseek-v4-pro','thinking':'disabled','temperature':0,'maxCompletionTokens':16384,'httpTimeout':180,'transportTimeout':420,'maxCalls':12,'repairsPerAttempt':2,'compiler':str(a.compiler.resolve()),'compilerSHA256':PIN,'SDK':str(sdk),'oracle':str(OLD/'grade.py'),'oracleSHA256':sha(OLD/'grade.py'),'expectedChecksPerMode':{'C':86,'D':116},'inputs':{str(p.resolve()):sha(p)for p in sorted(set(files))},'goldenValidationSHA256':sha(a.golden_validation),'scope':'Engineering completion campaign, changed prompt/transport/thinking/token ceiling; not matched causal productivity experiment','retention':'Project-local only; no Memory/KHC/Chain','budget':'At most12 sequential requests; no automatic retry after transport or missing-source failure. Reported usage threshold checked between calls, not hard billing cap.','reportedTokenStop':180000}
 save(a.out/'FROZEN.json',f);print(json.dumps({'frozen':str(a.out/'FROZEN.json'),'sha256':sha(a.out/'FROZEN.json'),'providerCalls':0}))
def frozen(d):
 f=read(d/'FROZEN.json');assert sha(f['compiler'])==f['compilerSHA256']==PIN
 for p,v in f['inputs'].items():assert sha(p)==v,'Frozen input drift: '+p
 return f

def arm(d,i):
 t,c=ORDER[i-1];return d/f'attempt-{i}-{t}-{c}'
def round_dir(a):return arm(a.out,a.attempt)/f'round-{a.round}'
def build_payload(task,condition,previous=None,feedback=None):
 content=(HERE/'COMMON-GUIDE.md').read_text()+'\nCONDITION: '+condition.upper()+'\nTASK\n'+(HERE/f'TASK-{task}.md').read_text()
 if previous is not None:content+='\nPREVIOUS SOURCE PROPOSAL\n'+previous+'\nACTUAL CONTROLLER FEEDBACK\n'+json.dumps(feedback,ensure_ascii=False)
 assert len(content.encode())<=100000
 return {'model':'deepseek-v4-pro','thinking':{'type':'disabled'},'temperature':0,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':content}],'max_tokens':16384,'stream':False,'response_format':{'type':'json_object'}}
def call(a):
 d=a.out;f=frozen(d);assert a.approved_freeze_sha==sha(d/'FROZEN.json')
 assert not(arm(d,a.attempt)/'CLOSED.json').exists()
 if a.attempt>1:assert(arm(d,a.attempt-1)/'CLOSED.json').exists(),'Finish previous arm first'
 receipts=list(d.glob('attempt-*/round-*/RECEIPT.json'));assert len(receipts)<f['maxCalls']
 rows=[read(p)for p in receipts];known=sum((x.get('usage')or{}).get('total_tokens',0)for x in rows)
 assert known<f['reportedTokenStop'],'Declared reported-token stop reached'
 previous=feedback=None
 if a.round>1:
  p=arm(d,a.attempt)/f'round-{a.round-1}';assert(p/'ASSESSMENT.json').exists(),'Actual source review and assessment required before repair'
  feedback=read(p/'ASSESSMENT.json');assert not feedback['allPassed'],'No repair of passed arm'
  previous=(p/'main.flow').read_text()
 else:assert not arm(d,a.attempt).exists()
 r=round_dir(a);r.mkdir(parents=True,exist_ok=False)
 task,condition=ORDER[a.attempt-1];payload=build_payload(task,condition,previous,feedback);raw=json.dumps(payload,ensure_ascii=False).encode();(r/'request.json').write_bytes(raw)
 transport=load(HERE/'call_transport.py','ai_completion_transport')
 receipt,response=transport.invoke(raw,http_timeout=f['httpTimeout'],outer_timeout=f['transportTimeout'])
 receipt.update(schema='rf2.ai-completion.receipt.v1',attempt=a.attempt,round=a.round,task=task,condition=condition,requestSHA256=sha(r/'request.json'),frozenSHA256=sha(d/'FROZEN.json'),sourceExecuted=False)
 if response is not None:
  save(r/'response.json',response)
  try:
   choice=response['choices'][0];receipt.update(servedModel=response.get('model'),finishReason=choice.get('finish_reason'))
   if choice.get('finish_reason')!='stop':receipt['failure']='incomplete completion; arm stops without automatic retry'
   else:
    result=json.loads(choice['message']['content']);assert isinstance(result,dict)and set(result)=={'source'}and isinstance(result['source'],str)
    source=result['source'].encode();assert 0<len(source)<=65536
    (r/'main.flow').write_bytes(source);receipt['sourceSHA256']=sha(r/'main.flow')
  except(Exception,)as e:receipt['failure']='InvalidSourceContract:'+type(e).__name__
 save(r/'RECEIPT.json',receipt);print(json.dumps(receipt))

def assess(a):
 d=a.out;f=frozen(d);r=round_dir(a);p=r/'main.flow';assert sha(p)==a.reviewed_sha==read(r/'RECEIPT.json')['sourceSHA256'];assert not(r/'ASSESSMENT.json').exists()
 task,condition=ORDER[a.attempt-1];legacy=load(OLD/'study.py','legacy_admission');errors=legacy.condition_errors(p.read_text(),condition)
 result={'sourceSHA256':a.reviewed_sha,'manualReviewConfirmed':True,'allPassed':False,'conditionErrors':errors,'runs':[]};start=time.monotonic()
 if errors:result['feedback']=errors
 else:
  assert os.environ.get('TMPDIR','').startswith('/Volumes/Mac Work Cache/'),'Use guarded cache runner for generated native outputs'
  tmp=Path(tempfile.mkdtemp(prefix='rf2-complete-',dir=os.environ['TMPDIR']))
  for mode in ['plain','opt']:
   binary=tmp/mode/'program';binary.parent.mkdir();out=r/mode;out.mkdir()
   cmd=[f['compiler'],str(p),str(binary),'--compact','--sdk-root',f['SDK'],'--diagnostic-json']+(['--opt']if mode=='opt'else[])
   one={'mode':mode,'allPassed':False}
   try:
    q=subprocess.run(cmd,capture_output=True,timeout=30);(out/'compile.stdout').write_bytes(q.stdout);(out/'compile.stderr').write_bytes(q.stderr);one['compileExit']=q.returncode
    if q.returncode:one['feedback']=q.stderr.decode(errors='replace')[:5000]
    else:
     subprocess.run(['codesign','-s','-',str(binary)],capture_output=True,check=True,timeout=10);one['binarySHA256']=sha(binary)
     q=subprocess.run([sys.executable,'-B',f['oracle'],task,'--binary',str(binary),'--out',str(out/'grade')],capture_output=True,timeout=180)
     (out/'grade.stdout').write_bytes(q.stdout);(out/'grade.stderr').write_bytes(q.stderr)
     if(out/'grade/RESULTS.json').exists():
      g=read(out/'grade/RESULTS.json');assert g['total']==f['expectedChecksPerMode'][task]
      one.update(graderExit=q.returncode,allPassed=q.returncode==0 and g['allPassed'],passed=g['passed'],total=g['total'],feedback=[x for x in g['cases']if not x['passed']][:8])
     else:one['feedback']='Missing grader receipt; '+q.stderr.decode(errors='replace')[:1200]
   except(Exception,KeyboardInterrupt)as e:one['feedback']=type(e).__name__+': '+str(e)[:1200]
   result['runs'].append(one)
  result['allPassed']=len(result['runs'])==2 and all(x['allPassed']for x in result['runs']);result['feedback']=[{'mode':x['mode'],'feedback':x.get('feedback')}for x in result['runs']if not x['allPassed']]
 result['buildAndTestSeconds']=time.monotonic()-start;save(r/'ASSESSMENT.json',result);print(json.dumps(result))
def close(a):
 frozen(a.out);p=arm(a.out,a.attempt);assert not(p/'CLOSED.json').exists();receipts=sorted(p.glob('round-*/RECEIPT.json'));assert receipts
 last=read(receipts[-1]);ap=receipts[-1].parent/'ASSESSMENT.json';assessment=read(ap)if ap.exists()else None
 if last.get('sourceSHA256'):assert assessment is not None,'Every proposal needs source review/assessment'
 if assessment and not assessment['allPassed'] and last['round']<3:assert a.no_repair_reason,'Declining permitted repair needs reason'
 result={'allPassed':bool(assessment and assessment['allPassed']),'rounds':len(receipts),'lastReceiptSHA256':sha(receipts[-1]),'declinedRepairReason':a.no_repair_reason}
 save(p/'CLOSED.json',result);print(json.dumps(result))
def cost(rows):
 usages=[x['usage']for x in rows if isinstance(x.get('usage'),dict)];unknown=len(rows)-len(usages)
 return {'requests':len(rows),'knownRequests':len(usages),'unknownUsageRequests':unknown,'knownProviderTotalTokens':sum(x.get('total_tokens',0)for x in usages),'knownPromptTokens':sum(x.get('prompt_tokens',0)for x in usages),'knownCompletionTokens':sum(x.get('completion_tokens',0)for x in usages),'requestSeconds':sum(x.get('elapsedSeconds',0)for x in rows),'buildTestSeconds':sum((x.get('assessment')or{}).get('buildAndTestSeconds',0)for x in rows),'reasoningSubsetOfCompletion':sum((x.get('completion_tokens_details')or{}).get('reasoning_tokens',0)for x in usages),'cacheSubsetOfPrompt':sum((x.get('prompt_tokens_details')or{}).get('cached_tokens',0)for x in usages),'usageIsBilling':False}
def summary(a):
 f=frozen(a.out);attempts=[];rows=[]
 for i,(task,condition)in enumerate(ORDER,1):
  rs=[]
  for p in sorted(arm(a.out,i).glob('round-*/RECEIPT.json')):
   x=read(p);ap=p.parent/'ASSESSMENT.json';x['assessment']=read(ap)if ap.exists()else None;rs.append(x)
  passed=any((x['assessment']or{}).get('allPassed')for x in rs)
  attempts.append({'attempt':i,'task':task,'condition':condition,'passed':passed,'closed':(arm(a.out,i)/'CLOSED.json').exists(),'rounds':rs,'costIncludingFailures':cost(rs)});rows+=rs
 result={'schema':'rf2.ai-completion.summary.v1','frozenSHA256':sha(a.out/'FROZEN.json'),'attempts':attempts,'tasksPassed':sum(x['passed']for x in attempts),'tasksDeclared':4,'costIncludingFailures':cost(rows),'scope':f['scope'],'stableChanged':False}
 p=a.out/f'SUMMARY-{time.time_ns()}.json';save(p,result);print(json.dumps({'summary':str(p),'tasksPassed':result['tasksPassed'],'costIncludingFailures':result['costIncludingFailures']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','call','assess','close','summary']);p.add_argument('--out',type=Path,required=True);p.add_argument('--compiler',type=Path);p.add_argument('--golden-validation',type=Path);p.add_argument('--attempt',type=int,choices=[1,2,3,4]);p.add_argument('--round',type=int,choices=[1,2,3]);p.add_argument('--approved-freeze-sha');p.add_argument('--reviewed-sha');p.add_argument('--no-repair-reason');a=p.parse_args();a.out=a.out.resolve();globals()[a.action](a)
