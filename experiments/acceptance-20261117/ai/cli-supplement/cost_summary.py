"""Project-local cost/outcome ledger; unknown transport usage is never zero."""
from pathlib import Path
import argparse,hashlib,json

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def usage_sum(rows):
    known=[r['usage']for r in rows if isinstance(r.get('usage'),dict)]
    return {'knownUsageRequests':len(known),'unknownUsageRequests':len(rows)-len(known),'knownPromptTokens':sum(u.get('prompt_tokens',0)for u in known),'knownCompletionTokens':sum(u.get('completion_tokens',0)for u in known),'knownProviderTotalTokens':sum(u.get('total_tokens',0)for u in known),'reasoningTokensSubsetOfCompletion':sum(u.get('completion_tokens_details',{}).get('reasoning_tokens',0)for u in known),'cachedPromptTokensSubsetOfPrompt':sum(u.get('prompt_tokens_details',{}).get('cached_tokens',0)for u in known),'observedRequestSecondsIncludingFailedTransports':sum(r.get('elapsedSeconds',0)for r in rows),'buildTestSeconds':sum((r.get('assessment')or{}).get('buildAndTestSeconds',0)for r in rows)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--study',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=a.study.resolve();old=json.loads((d/'HISTORICAL-COSTS.json').read_text());groups={}
    for r in old:
        key=(r['study'],r['condition'],r['task'],r['attempt']);groups.setdefault(key,[]).append(r)
    historical=[]
    for key,rows in groups.items():
        rows=sorted(rows,key=lambda r:r['round']);passed=any((r.get('assessment')or{}).get('allPassed')for r in rows)
        historical.append({'study':key[0],'condition':key[1],'task':key[2],'attempt':key[3],'passed':passed,'initialRounds':[r for r in rows if r['round']==1],'repairRounds':[r for r in rows if r['round']>1],'allRoundsCost':usage_sum(rows),'costPerPassingTaskProviderTokens':usage_sum(rows)['knownProviderTotalTokens']if passed and all(r.get('usage')for r in rows)else None})
    new=[]
    for n in [1,2]:
        p=d/f'attempt-{n}/RECEIPT.json'
        if not p.exists():new.append({'attempt':n,'state':'not finished; no receipt yet'});continue
        row=json.loads(p.read_text());row['receiptSHA256']=sha(p);assess=p.parent/'ASSESSMENT.json';row['assessment']=json.loads(assess.read_text())if assess.exists()else None;new.append(row)
    new_receipts=[r for r in new if 'task'in r];new_cost=usage_sum(new_receipts);complete_pass=sum(bool((r.get('assessment')or{}).get('allPassed'))for r in new_receipts)
    result={'schema':'rf2.useful-output.cost-ledger.v1','historicalCostSnapshotSHA256':sha(d/'HISTORICAL-COSTS.json'),'historicalAttempts':historical,'historicalKnownTotals':usage_sum(old),'newCondition':'Two-call nonrandomized CLI library condition; not matched causal savings evidence','newAttempts':new,'newKnownTotals':new_cost,'newTasksPassingIndependentNativeOracle':complete_pass,'newKnownProviderTokensPerPassingTask':new_cost['knownProviderTotalTokens']/complete_pass if complete_pass and new_cost['unknownUsageRequests']==0 else None,'interpretation':['Unknown transport usage remains unknown, not zero.','All initial and repair usage/time retained separately and combined within its own historical attempt.','Reasoning tokens are reported as completion subsets, never added twice.','No source-size, billing, generalized causal token or hardware claim.']}
    assert not a.out.exists(),'Use a fresh receipt path';a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'historicalKnownTotals':result['historicalKnownTotals'],'historicalAttempts':len(historical),'newTasksPassingIndependentNativeOracle':complete_pass}))
if __name__=='__main__':main()
