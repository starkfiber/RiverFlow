"""Additional adversarial data distributions, outside the prefix-probe corpus.

Uses existing source-bound native binaries; preserves all regressions.
"""
import argparse,hashlib,importlib.util,json,random,statistics,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sdk_oracle',HERE/'qualify.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prior',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();prior=a.prior.resolve();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((prior/'RESULTS.json').read_text());assert receipt['allPassed']and receipt['sources']['experiments/evolution-20261117/sdk/json_spans.flow']==module.sha(HERE/'json_spans.flow')
    builds={Path(x['command'][2]).parent.name:x for x in receipt['builds']}
    for name,b in builds.items():assert module.sha(prior/name/'program')==b['programSHA256']
    size=65536;patterns={'late-escape':b'a'*32+b'"'*(size-32),'front-escape':b'"'*32+b'a'*(size-32),'middle-burst':b'a'*16384+b'"'*32768+b'a'*16384,'alternating-blocks':(b'a'*64+b'"'*64)*(size//128)}
    rng=random.Random(17112026);rows=[];controls=[]
    for label,data in patterns.items():
        p=d/(label+'.txt');p.write_bytes(data);expected=module.report_oracle(data)
        for mode in ['plain','opt']:
            exes={v:prior/(mode+'-'+v)/'program'for v in ['baseline','candidate']};times={v:[]for v in exes};order=[]
            for trial in range(11):
                names=list(exes);rng.shuffle(names);order.append(names)
                for v in names:
                    t=time.perf_counter_ns();q=subprocess.run([str(exes[v]),'1',str(p),'16','16777216','0','0','0'],capture_output=True,timeout=10);elapsed=(time.perf_counter_ns()-t)/1e9
                    assert q.returncode==0 and q.stdout==expected;times[v].append(elapsed)
            rows.append({'label':label,'mode':mode,'bytes':size,'repeats':16,'pairs':11,'order':order,'seconds':times,'baselineMedian':statistics.median(times['baseline']),'candidateMedian':statistics.median(times['candidate']),'speedup':statistics.median(times['baseline'])/statistics.median(times['candidate'])})
            for cap in [0,1,31,32,33,63,64,65,255,256,257,len(data),2*len(data)+2]:
                want=module.raw_oracle(data,cap)
                for v,exe in exes.items():
                    q=subprocess.run([str(exe),'0',str(p),'1',str(cap),'0','0','1'],capture_output=True,timeout=10)
                    assert (q.returncode,q.stdout,q.stderr)==want
                    controls.append([label,mode,cap,v])
    result={'schema':'rf2.json-distribution-controls.v1','rows':rows,'exactCapacityControls':len(controls),'samePriorBinaries':True,'candidateSourceSHA256':module.sha(HERE/'json_spans.flow'),'interpretation':'Prefix-density dispatch is a heuristic; mixed-distribution losses must remain visible. Not whole-application or universal speed.'}
    (d/'RESULTS.json').write_text(json.dumps(result,indent=2));print(json.dumps({'controls':len(controls),'rows':[{k:v for k,v in x.items()if k not in ['seconds','order']}for x in rows]}))
if __name__=='__main__':main()
