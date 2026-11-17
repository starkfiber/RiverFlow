"""Explicit post-failure routing amendment; preserves original frozen phase."""
from pathlib import Path
import argparse,fcntl,hashlib,importlib.util,json,math,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
ROUTER=ROOT/'experiments/ai-grounded-routing-20261117/router.py'
PHASE=ROOT/'experiments/ai-transport-phases-20261117'
spec=importlib.util.spec_from_file_location('original_finite_router',ROUTER);router=importlib.util.module_from_spec(spec);spec.loader.exec_module(router)
DEFINITIONS={'manual':'The application source owns argument validation, selected-file input, report serialization and checked output directly. It imports text.flow, not the shared CLI.','cli':'The application source delegates common argument/input/report/output plumbing to shared TextReportCLI via text_report_entry and a synchronous task callback.'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def corrected_payload(task,condition,prior=None,feedback=None):
 p=router.payload(task,condition)
 p['messages'][0]['content']+=' Implementation labels have the explicit definitions supplied below. Match the trusted requestedImplementation exactly; it selects plumbing, not a new capability. Do not substitute cli for manual or vice versa.'
 p['messages'][1]['content']='IMPLEMENTATION DEFINITIONS\n'+json.dumps(DEFINITIONS)+'\nTRUSTED REQUEST CONFIGURATION\n'+json.dumps({'requestedImplementation':condition})+'\n'+p['messages'][1]['content']
 if prior is not None:
  p['messages'][1]['content']+='\nACTUAL REJECTED SELECTION\n'+json.dumps(prior)+'\nACTUAL VALIDATOR FEEDBACK\n'+feedback+'\nReturn one complete corrected selection object matching the same original requested behavior and trusted implementation. The previous selection remains a recorded failure.'
 return p

def plan(a):
 f=router.frozen(a.out);assert not a.amendment.exists()
 first=a.out/'attempt-1';r=read(first/'RECEIPT.json');res=read(first/'RESOLUTION.json')
 assert r.get('transportExit')==0 and r.get('finishReason')=='stop'and(first/'SELECTION.json').is_file()and not res['matched'],'Only existing valid wrong choice qualifies for explicit repair'
 assert f['rawCalls']==7 and len(list(a.out.glob('attempt-*/CALL-STARTED.json')))==1,'Reviewed amendment starts after exactly7raw+1routing calls'
 files=list(HERE.glob('*.py'))+list(HERE.glob('*.md'))+list(PHASE.glob('*.py'))+list(PHASE.glob('*.md'))
 v={'schema':'rf2.ai-routing.completion-amendment.v1','routingFreezeSHA256':sha(a.out/'FROZEN.json'),'routingDirectory':str(a.out.resolve()),'inputs':{str(p.resolve()):sha(p)for p in sorted(files)},'preservedFirstAttempt':{str(p.resolve()):sha(p)for p in first.iterdir()if p.is_file()},'definitions':DEFINITIONS,'remainingInitials':[2,3,4],'logicalRepairsAllowed':1,'repairTarget':1,'repairAfterAllFourResolved':True,'maxPhaseCalls':5,'maxCombinedCalls':12,'reportedTokenStopCombined':180000,'sourceOrOracleChanges':False,'providerCalls':0,'scope':'Define implementation labels and explicit trusted caller implementation; same strict capability/implementation oracle. One declared feedback repair of the observed logical failure after3remaining initial calls. No transport retries.'}
 save(a.amendment,v);print(json.dumps({'amendmentSHA256':sha(a.amendment),'providerCalls':0}))
def approved(a):
 assert sha(a.amendment)==a.approved_amendment_sha,'Root-reviewed amendment SHA required'
 m=read(a.amendment);assert m['routingDirectory']==str(a.out.resolve());assert m['routingFreezeSHA256']==sha(a.out/'FROZEN.json')==a.approved_freeze_sha
 for key in ['inputs','preservedFirstAttempt']:
  for p,v in m[key].items():assert sha(p)==v,'Amendment source/evidence drift'
 return m,router.frozen(a.out)

def initial(a):
 approved(a);assert a.attempt in [2,3,4]
 original_payload=router.payload;original_load=router.load
 # corrected_payload uses the original pure payload, not this installed wrapper.
 def prepare(task,condition):
  router.payload=original_payload
  try:return corrected_payload(task,condition)
  finally:router.payload=prepare
 def selected(path,name):return original_load(PHASE/'call_transport.py',name)if Path(path)==router.TRANSPORT/'call_transport.py'else original_load(path,name)
 router.payload=prepare;router.load=selected
 router.call(a)
 p=a.out/f'attempt-{a.attempt}'/'RECEIPT.json';r=read(p);r.update(completionAmendmentSHA256=sha(a.amendment),explicitImplementationDefinitions=True,callerImplementationExplicit=True,transportImplementationSHA256=sha(PHASE/'provider_transport.py'),transportSupervisorSHA256=sha(PHASE/'call_transport.py'))
 save(p,r);print(json.dumps({'amendmentApplied':True,'receipt':str(p)}))
def phase_paths(d):return sorted(d.glob('attempt-*/CALL-STARTED.json'))+list(d.glob('choice-1-repair/CALL-STARTED.json'))
def phase_receipts(d):return sorted(d.glob('attempt-*/RECEIPT.json'))+list(d.glob('choice-1-repair/RECEIPT.json'))
def phase_records(d):
 rows=[]
 for start in phase_paths(d):
  receipt=start.parent/'RECEIPT.json'
  if receipt.is_file():rows.append(read(receipt))
  else:rows.append({'usage':None,'usageKnown':False,'elapsedSeconds':None,'receiptMissing':True,'callStartSHA256':sha(start),'requestMayHaveBeenSent':'unknown','failure':'Call started but final receipt unavailable; usage and duration unknown','sourceExecuted':False})
 return rows
def phase_cost(rows):
 normalized=[];unknown_time=0
 for row in rows:
  value=row.get('elapsedSeconds');known=type(value)in [int,float]and math.isfinite(value)and value>=0
  if not known:unknown_time+=1
  normalized.append(dict(row,elapsedSeconds=value if known else 0))
 result=router.cost(normalized);result['knownObservationSeconds']=result.pop('observedRequestSeconds');result['unknownTimingRequests']=unknown_time
 return result

def repair(a):
 m,f=approved(a)
 assert all((a.out/f'attempt-{i}'/'RESOLUTION.json').is_file()for i in range(1,5)),'All4initial selections must be resolved before explicit logical repair'
 first=a.out/'attempt-1';res=read(first/'RESOLUTION.json');r0=read(first/'RECEIPT.json');assert not res['matched']and r0.get('transportExit')==0 and r0.get('finishReason')=='stop'
 assert(first/'SELECTION.json').is_file(),'No repair of transport/missing-output failures'
 lock=(a.out/'CALL.lock').open('a')
 try:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  consumed=phase_paths(a.out);assert len(consumed)==4 and f['rawCalls']+len(consumed)<12
  costs=router.cost([read(p)for p in phase_receipts(a.out)]);assert f['rawCosts']['knownProviderTotalTokens']+costs['knownProviderTotalTokens']<180000
  d=a.out/'choice-1-repair';d.mkdir(exist_ok=False)
  prior=router.selection((first/'SELECTION.json').read_text());feedback=res.get('failure','Incorrect selection')+'; requested behavior is the original C request; trusted requestedImplementation is manual. cli means shared delegation and does not satisfy that caller setting.'
  raw=json.dumps(corrected_payload('C','manual',prior,feedback),ensure_ascii=False).encode();(d/'request.json').write_bytes(raw)
  started={'attempt':1,'logicalRepair':1,'parentReceiptSHA256':sha(first/'RECEIPT.json'),'parentResolutionSHA256':sha(first/'RESOLUTION.json'),'amendmentSHA256':sha(a.amendment),'frozenSHA256':sha(a.out/'FROZEN.json'),'requestSHA256':sha(d/'request.json'),'automaticRetry':False,'startedAtUnix':time.time()};save(d/'CALL-STARTED.json',started)
  tr=router.load(PHASE/'call_transport.py','amended_routing_transport');receipt,response=tr.invoke(raw,http_timeout=180,outer_timeout=420)
  receipt.update(schema='rf2.ai-grounded-routing.logical-repair.receipt.v1',attempt=1,logicalRepair=1,expectedTask='C',expectedCondition='manual',parentReceiptSHA256=sha(first/'RECEIPT.json'),parentResolutionSHA256=sha(first/'RESOLUTION.json'),amendmentSHA256=sha(a.amendment),frozenSHA256=sha(a.out/'FROZEN.json'),requestSHA256=sha(d/'request.json'),sourceExecuted=False,sourceGenerated=False,transportImplementationSHA256=sha(PHASE/'provider_transport.py'),transportSupervisorSHA256=sha(PHASE/'call_transport.py'))
  if response is not None:
   save(d/'response.json',response)
   try:
    choice=response['choices'][0];receipt.update(servedModel=response.get('model'),finishReason=choice.get('finish_reason'))
    if choice.get('finish_reason')!='stop':receipt['failure']='Incomplete selection; no retry'
    else:
     v=router.selection(choice['message']['content']);save(d/'SELECTION.json',v);receipt['selectionSHA256']=sha(d/'SELECTION.json')
   except(Exception,)as e:receipt['failure']='SelectionContract:'+type(e).__name__
  save(d/'RECEIPT.json',receipt);print(json.dumps(receipt))
 finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close()

def resolve_repair(a):
 _,f=approved(a);d=a.out/'choice-1-repair';r=read(d/'RECEIPT.json');assert not(d/'RESOLUTION.json').exists()
 result={'schema':'rf2.ai-grounded-routing.logical-repair.resolution.v1','attempt':1,'logicalRepair':1,'matched':False,'sourceExecuted':False,'sourceGenerated':False,'rootNativeReviewRequired':True,'receiptSHA256':sha(d/'RECEIPT.json'),'originalWrongSelectionPreserved':True}
 if(d/'SELECTION.json').exists():
  assert r['selectionSHA256']==sha(d/'SELECTION.json');v=router.selection((d/'SELECTION.json').read_text());result['selection']=v
  if v=={'capability':'log-severity','implementation':'manual'}:
   item=f['sources']['log-severity/manual'];assert sha(item['path'])==item['sha256'];result.update(matched=True,source=item['path'],sourceSHA256=item['sha256'],sourceKind=item['sourceKind'])
  else:result['failure']='Wrong selection after sole logical repair; no fallback or further repair'
 else:result['failure']=r.get('failure','No valid repair selection')
 save(d/'RESOLUTION.json',result);print(json.dumps(result))

def summary(a):
 m,f=approved(a);rows=phase_records(a.out);initials=[read(p)for p in sorted(a.out.glob('attempt-*/RESOLUTION.json'))];rp=a.out/'choice-1-repair/RESOLUTION.json';rr=read(rp)if rp.exists()else None
 effective=[rr if i==0 and rr is not None and rr['matched']else v for i,v in enumerate(initials)]
 result={'schema':'rf2.ai-routing.amended-summary.v1','amendmentSHA256':sha(a.amendment),'frozenSHA256':sha(a.out/'FROZEN.json'),'initialSelections':initials,'logicalRepair':rr,'effectiveSelections':effective,'matchedInitials':sum(x['matched']for x in initials),'matchedAfterDeclaredRepair':sum(x['matched']for x in effective),'declaredArms':4,'callsIncludingFailedFirstSelection':len(phase_paths(a.out)),'combinedCalls':f['rawCalls']+len(phase_paths(a.out)),'phaseCostIncludingFailures':phase_cost(rows),'rawCostIncludingFailures':f['rawCosts'],'scope':'Finite selection from2existingalgorithms with caller-specified plumbing, not source generation or causal token comparison','sourceGenerated':False,'sourceExecuted':False,'CodexEngineeringTokens':'unavailable and excluded from DeepSeek reported totals','originalWrongSelectionPreserved':True}
 p=a.out/f'AMENDED-SUMMARY-{time.time_ns()}.json';save(p,result);print(json.dumps({'summary':str(p),'matchedInitials':result['matchedInitials'],'matchedAfterDeclaredRepair':result['matchedAfterDeclaredRepair'],'cost':result['phaseCostIncludingFailures'],'combinedCalls':result['combinedCalls']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','initial','repair','resolve-repair','summary']);p.add_argument('--out',type=Path,required=True);p.add_argument('--amendment',type=Path,required=True);p.add_argument('--approved-amendment-sha');p.add_argument('--approved-freeze-sha');p.add_argument('--attempt',type=int,choices=[2,3,4]);a=p.parse_args();a.out=a.out.resolve();a.amendment=a.amendment.resolve();globals()[a.action.replace('-','_')](a)
