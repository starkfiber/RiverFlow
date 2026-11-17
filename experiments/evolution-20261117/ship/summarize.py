from pathlib import Path
import csv,json,statistics,platform,subprocess,hashlib
S=Path(__file__).resolve().parent;A=S.parents[2]/'artifacts/evolution-20261117/ship'
out={'scope':'ARM64 host-native full bounded AEAD calls; no guest throughput or network/energy/token claim','host':platform.platform(),'architecture':platform.machine(),'compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0],'iterationsPerSample':4000,'pairedAlternatingOrderSamples':11,'warmupCalls':20,'workloads':{}}
for name in ['TIMINGS.csv','TIMINGS-OZ.csv']:
 rows=list(csv.DictReader((A/name).open()));results=[]
 for n in [0,16,64,128,72]:
  r=[x for x in rows if int(x['data_bytes'])==n];assert len(r)==11
  b=[float(x['baseline_ns']) for x in r];c=[float(x['candidate_ns']) for x in r]
  results.append(dict(dataBytes=n,aadBytes=int(r[0]['aad_bytes']),baselineMedianNs=statistics.median(b),candidateMedianNs=statistics.median(c),medianSpeedup=statistics.median(b)/statistics.median(c),pairedMinSpeedup=min(x/y for x,y in zip(b,c)),pairedMaxSpeedup=max(x/y for x,y in zip(b,c))))
 out['workloads'][name]=results
(A/'PERFORMANCE.json').write_text(json.dumps(out,indent=2)+'\n')
r={'sourceHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in S.iterdir() if p.is_file()}}
for n in ['baseline','candidate']:
 p=A/('guest-'+n)
 if not (p/'SECURE-VERIFICATION.json').exists():continue
 j=json.loads((p/'SECURE-VERIFICATION.json').read_text());r[n]={'passed':j['passed'],'completed':j['completed'],'machines':[{k:v for k,v in x.items() if k in ['machine','passed','error']} for x in j['rows']],'imageSHA256':hashlib.sha256((p/'rf2ship.img').read_bytes()).hexdigest(),'imageBytes':(p/'rf2ship.img').stat().st_size}
r['qemuPath']=subprocess.check_output(['which','qemu-system-x86_64'],text=True).strip();r['qemuVersion']=subprocess.check_output(['qemu-system-x86_64','--version'],text=True).splitlines()[0]
compiler=Path('/Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program');r['compilerSHA256']=hashlib.sha256(compiler.read_bytes()).hexdigest()
r['sourceOriginalStillMatches']=hashlib.sha256(Path('/Users/ik/Projects/RiverFlow/experiments/rf2ship/secure-transport-018/aead_reference.c').read_bytes()).hexdigest()==r['sourceHashes']['baseline.c']
(A/'RECEIPT.json').write_text(json.dumps(r,indent=2)+'\n')
print('Performance summary and source-bound receipt refreshed.')
