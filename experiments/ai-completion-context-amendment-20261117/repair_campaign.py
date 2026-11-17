"""Source-context repair amendment; original frozen campaign remains intact."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE=ROOT/'experiments/ai-completion-20261117'
CONTEXT=ROOT/'experiments/ai-repair-context-20261117'
cspec=importlib.util.spec_from_file_location('repair_advice',CONTEXT/'context.py');advice=importlib.util.module_from_spec(cspec);cspec.loader.exec_module(advice)
sys.path.insert(0,str(BASE))
spec=importlib.util.spec_from_file_location('original_campaign',BASE/'campaign.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
DIRECTIVE='''REPAIR REQUIRED: The previous source failed actual compiler/acceptance checks. You must fix the reported failures and return the COMPLETE corrected program, not repeat the previous source. Read the actual diagnostic and source excerpt below. Also review all existing guide grammar rules: no try in untyped main (use an IO function with a handled main); no break; local binding names must be unique in their function, including distinct branches/loops; record locals belong at function root. Validate complete json/html argument strings, not just a four-byte prefix. These are supplied language/contract reminders, not a task solution. Do not return explanations, patches, Markdown or a placeholder. Return only the JSON object containing the entire corrected source. Preserve the specified task behavior and permitted import. No code is executed by you.'''
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,obj):Path(p).write_text(json.dumps(obj,indent=2)+'\n')
def excerpts(previous,feedback,expected_path):
 lines=previous.splitlines();locations=set()
 for run in feedback.get('runs',[]):
  raw=run.get('feedback')
  if not isinstance(raw,str):continue
  try:
   diag=json.loads(raw);loc=diag.get('location')or{};n=loc.get('line')
   if loc.get('origin')=='source' and loc.get('path')==str(expected_path.resolve()) and isinstance(n,int)and 1<=n<=len(lines):locations.add(n)
  except(ValueError,TypeError):continue
 return '\n'.join('Actual diagnostic line '+str(n)+':\n'+'\n'.join(str(i+1)+': '+lines[i]for i in range(max(0,n-5),min(len(lines),n+4)))for n in sorted(locations))
def plan(a):
 base.frozen(a.campaign);assert not a.amendment.exists()
 files=[HERE/'repair_campaign.py',HERE/'AMENDMENT.md']+sorted(CONTEXT.glob('*.py'))+sorted(CONTEXT.glob('*.md'))
 value={'schema':'rf2.ai-completion.repair-amendment.v1','campaign':str(a.campaign.resolve()),'originalFrozenSHA256':sha(a.campaign/'FROZEN.json'),'inputs':{str(p.resolve()):sha(p)for p in files},'changes':'Add bounded lexical advisory diagnostics from actual source and enable low-effort thinking for repairs within unchanged completion/call/time caps; no task solutions or oracle changes','capsUnchanged':True,'providerCalls':0,'originalFrozenInputsChanged':False}
 save(a.amendment,value);print(json.dumps({'amendment':str(a.amendment),'sha256':sha(a.amendment),'providerCalls':0}))
def call(a):
 assert sha(a.amendment)==a.approved_amendment_sha,'Root-reviewed amendment hash required'
 m=read(a.amendment);assert m['campaign']==str(a.campaign.resolve());assert m['originalFrozenSHA256']==sha(a.campaign/'FROZEN.json')==a.approved_freeze_sha
 for p,v in m['inputs'].items():assert sha(p)==v,'Amendment input drift'
 assert a.round in [2,3],'Amendment only applies to actual feedback repair'
 previousdir=base.arm(a.campaign,a.attempt)/f'round-{a.round-1}'
 previous=(previousdir/'main.flow').read_text();feedback=read(previousdir/'ASSESSMENT.json');assert not feedback['allPassed']
 original=base.build_payload
 def amended(task,condition,previous=None,feedback=None):
  assert previous is not None and feedback is not None
  p=original(task,condition,previous,feedback)
  p['messages'][0]['content']+=' '+DIRECTIVE+' Address all applicable advisory findings below, not only the first compiler error. Boolean expressions must use all/any or eager bitwise operators, never word and/or.'
  p['thinking']={'type':'enabled'}
  p['reasoning_effort']='low'
  p['messages'][1]['content']+='\nEXPLICIT REPAIR ACTION\n'+DIRECTIVE+'\nACTUAL DIAGNOSTIC SOURCE EXCERPT\n'+excerpts(previous,feedback,previousdir/'main.flow')+'\nBOUNDED ADVISORY SOURCE REVIEW (not compiler authority)\n'+json.dumps(advice.collect(previous.encode()),ensure_ascii=False)
  assert len(json.dumps(p).encode())<=120000
  return p
 base.build_payload=amended
 a.out=a.campaign
 base.call(a)
 r=base.round_dir(a);receipt=read(r/'RECEIPT.json')
 receipt.update(amendmentSHA256=sha(a.amendment),amendmentPath=str(a.amendment.resolve()),repairDirectiveExplicit=True,lexicalRepairContext=True,repairThinking='enabled/low')
 if(r/'main.flow').exists():
  same=(r/'main.flow').read_text().rstrip()==previous.rstrip();receipt['sameSourceIgnoringTrailingWhitespace']=same
  if same:receipt['failure']='Repeated failing source after explicit repair; original source retained for review'
 save(r/'RECEIPT.json',receipt)
 save(r/'AMENDMENT-APPLIED.json',{'amendmentSHA256':sha(a.amendment),'requestSHA256':sha(r/'request.json'),'receiptSHA256':sha(r/'RECEIPT.json'),'originalFrozenSHA256':sha(a.campaign/'FROZEN.json'),'sourceChanged':not receipt.get('sameSourceIgnoringTrailingWhitespace',False)if(r/'main.flow').exists()else None})
 print(json.dumps({'amendmentApplied':True,'receipt':str(r/'RECEIPT.json'),'sameSource':receipt.get('sameSourceIgnoringTrailingWhitespace')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','call']);p.add_argument('--campaign',type=Path,required=True);p.add_argument('--amendment',type=Path,required=True);p.add_argument('--approved-amendment-sha');p.add_argument('--approved-freeze-sha');p.add_argument('--attempt',type=int,choices=[1,2,3,4]);p.add_argument('--round',type=int,choices=[2,3]);a=p.parse_args();a.campaign=a.campaign.resolve();a.amendment=a.amendment.resolve();globals()[a.action](a)
