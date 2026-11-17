"""Frozen native-loop and enclosing-process JSON report benchmark.

Preparation may run with correctness jobs. Measurement requires the root's
exclusive timing slot. Only rebuildable binaries use the disposable TMPDIR;
source, fixtures, frozen configuration and all unique measurements persist.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,platform,random,shutil,statistics,subprocess,tempfile,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
COMPILER_SHA='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
oracle=load_module('sdk_benchmark_oracle',HERE/'qualify.py')
def bootstrap_ratio(base,candidate,seed):
    ratios=[c/b for b,c in zip(base,candidate)];rng=random.Random(seed)
    samples=sorted(statistics.median([ratios[rng.randrange(len(ratios))]for _ in ratios])for _ in range(10000))
    return dict(point=statistics.median(ratios),lower95=samples[249],upper95=samples[9749],method='paired bootstrap median candidate/baseline ratio,10000resamples, fixed seed')
def build(compiler,entry,binary,sdk,mode,receipt):
    cmd=[str(compiler),str(entry),str(binary),'--compact','--sdk-root',str(sdk)]+(['--opt']if mode=='opt'else[])
    p=subprocess.run(cmd,capture_output=True,timeout=30);receipt.append({'command':cmd,'exit':p.returncode,'stderr':p.stderr.decode(errors='replace')});assert p.returncode==0,p.stderr
    subprocess.run(['codesign','-s','-',str(binary)],check=True,capture_output=True)
    return sha(binary)
def invoke(binary,path,repeats,wanted):
    args=[str(binary),'1',str(path),str(repeats),'16777216','0','0','0']
    start=time.monotonic_ns();p=subprocess.run(args,capture_output=True,timeout=20);elapsed=(time.monotonic_ns()-start)/1e9
    assert p.returncode==0 and p.stdout==wanted,(args,p.returncode,p.stderr[:300])
    fields=p.stderr.strip().split(b':');assert len(fields)==5,p.stderr
    used,error,native_us,consumed,observed_repeats=map(int,fields)
    assert used==len(wanted)and error==0 and observed_repeats==repeats
    assert consumed==repeats*(used+wanted[0]+wanted[-1])
    # Reject an observed wall-clock jump rather than silently repeating a sample.
    assert native_us>=0 and native_us/1e6<=elapsed+0.002,(native_us,elapsed)
    return {'nativeUs':native_us,'processSeconds':elapsed,'checksum':consumed,'outputSHA256':hashlib.sha256(wanted).hexdigest()}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--compiler',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--measure',action='store_true');a=ap.parse_args();a.compiler=a.compiler.resolve();assert sha(a.compiler)==COMPILER_SHA
    d=a.out.resolve();commands=[]
    if not a.measure:
        d.mkdir(parents=True,exist_ok=False);(d/'inputs').mkdir()
        current=load_module('sdk_current_stage',HERE/'stage_sdk.py');previous=load_module('sdk_previous_stage',ROOT/'experiments/evolution-20261117/sdk/stage_sdk.py')
        shutil.copytree(ROOT/'sdk/v1',d/'baseline-sdk');current.stage(d/'candidate-sdk');previous.stage(d/'previous-sdk')
        template=(HERE/'bench-task.flow.in').read_text().replace('__CANDIDATE_IMPORT__','').replace('__JSON__','writer_json')
        (d/'bench.flow').write_text(template)
        frozen={'schema':'rf2.sdk.native-benchmark.v2','compilerSHA256':COMPILER_SHA,'controllerSHA256':sha(Path(__file__)),'oracleSHA256':sha(HERE/'qualify.py'),'templateSHA256':sha(HERE/'bench-task.flow.in'),'entrySHA256':sha(d/'bench.flow'),'candidateSourceSHA256':sha(HERE/'json_spans.flow'),'trials':31,'warmupIterationsPerProcess':16,'bootstrapResamples':10000,'orderSeed':1172026,'smallGate':{'candidateBaselineMedianRatioAtMost':1.03,'upper95AtMost':1.05,'minimumNativeMicroseconds':50000},'nativeClock':'Darwin gettimeofday syscall116, microseconds; wall-time not a monotonic/CPU clock','processClock':'Python monotonic_ns enclosing startup, input, initialHTML conversion, warmups, repeated serialization and output','noRetries':True,'profiles':[],'modules':{v:{p.name:sha(p)for p in sorted((d/(v+'-sdk')).iterdir())if p.is_file()}for v in ['baseline','candidate','previous']}}
        for size in [0,32,1024,16384,262144]:
            for density in ['plain','mixed','escaped']:
                seed={'plain':b'alpha beta gamma 0123456789 ','mixed':b'alpha "beta" <gamma> & line\nsecond\tline ','escaped':b'"\\\n\t\r'}[density]
                data=(seed*((size+len(seed)-1)//len(seed)))[:size];path=d/'inputs'/f'{size}-{density}.txt';path.write_bytes(data)
                repeats=1048576 if size==0 else max(1,8388608//size)
                frozen['profiles'].append({'size':size,'density':density,'input':str(path),'inputSHA256':sha(path),'repeats':repeats,'variants':['baseline','previous','candidate']if size<=32 else['baseline','candidate']})
        (d/'FROZEN.json').write_text(json.dumps(frozen,indent=2))
    else:
        assert not(d/'STARTED.json').exists(),'Never reuse a measured campaign'
        frozen=json.loads((d/'FROZEN.json').read_text());assert frozen['controllerSHA256']==sha(Path(__file__))and frozen['oracleSHA256']==sha(HERE/'qualify.py')and frozen['templateSHA256']==sha(HERE/'bench-task.flow.in');assert frozen['compilerSHA256']==sha(a.compiler)and frozen['entrySHA256']==sha(d/'bench.flow')and frozen['candidateSourceSHA256']==sha(HERE/'json_spans.flow')
    # Rebuild the exact frozen sources into this job slot, even if previous cache
    # binaries were reclaimed. Basenames/flags and sources are unchanged.
    binary_dir=Path(tempfile.mkdtemp(prefix='sdk-native-matrix-',dir=os.environ['TMPDIR']));programs={};identities={}
    for mode in ['plain','opt']:
        for v in ['baseline','previous','candidate']:
            binary=binary_dir/(mode+'-'+v);identities[mode+'-'+v]=build(a.compiler,d/'bench.flow',binary,d/(v+'-sdk'),mode,commands);programs[mode,v]=binary
    (d/('MEASURE-BUILD.json'if a.measure else'PREPARE-BUILD.json')).write_text(json.dumps({'commands':commands,'programSHA256':identities,'binaryDirectory':str(binary_dir)},indent=2))
    # One smoke iteration proves clock/consumption/output plumbing without a
    # performance comparison. Results are not included as timed benchmark rows.
    sample=frozen['profiles'][1];path=Path(sample['input']);wanted=oracle.report_oracle(path.read_bytes())
    for binary in programs.values():invoke(binary,path,1,wanted)
    if not a.measure:
        print(json.dumps({'prepared':True,'programs':identities,'frozenSHA256':sha(d/'FROZEN.json')}));return
    for v in ['baseline','candidate','previous']:
        for name,want in frozen['modules'][v].items():assert sha(d/(v+'-sdk')/name)==want
    (d/'STARTED.json').write_text(json.dumps({'frozenSHA256':sha(d/'FROZEN.json'),'UTC':time.time(),'platform':platform.platform(),'exclusiveSlot':'Root granted; other sprint CPU jobs idle, unrelated Mac load not controlled'}))
    result={'schema':'rf2.sdk.native-benchmark-result.v2','frozenSHA256':sha(d/'FROZEN.json'),'programSHA256':identities,'rows':[],'complete':False};rng=random.Random(frozen['orderSeed'])
    def save():(d/'RESULTS.json').write_text(json.dumps(result,indent=2))
    try:
        for profile in frozen['profiles']:
            path=Path(profile['input']);assert sha(path)==profile['inputSHA256'];wanted=oracle.report_oracle(path.read_bytes())
            for mode in ['plain','opt']:
                trials=[]
                for trial in range(31):
                    order=list(profile['variants']);rng.shuffle(order);measurements={}
                    for v in order:measurements[v]=invoke(programs[mode,v],path,profile['repeats'],wanted)
                    trials.append({'trial':trial,'order':order,'measurements':measurements})
                    with(d/'TRIALS.jsonl').open('a')as f:f.write(json.dumps({'profile':profile['size'],'density':profile['density'],'mode':mode,**trials[-1]})+'\n')
                row={'profile':profile,'mode':mode,'trials':trials,'ratios':{}}
                for v in profile['variants'][1:]:
                    base=[t['measurements']['baseline']['nativeUs']for t in trials];candidate=[t['measurements'][v]['nativeUs']for t in trials];assert min(base)>0 and min(candidate)>0
                    ratio=bootstrap_ratio(base,candidate,frozen['orderSeed']+len(result['rows']));ratio.update(baselineMedianUs=statistics.median(base),candidateMedianUs=statistics.median(candidate),minimumNativeUs=min(base+candidate),speedup=1/ratio['point']);row['ratios'][v]=ratio
                    if profile['size']<=32 and v=='candidate':ratio['smallGatePassed']=ratio['point']<=1.03 and ratio['upper95']<=1.05 and ratio['minimumNativeUs']>=50000
                result['rows'].append(row);save()
        result['complete']=True;result['smallGatesPassed']=all(row['ratios']['candidate']['smallGatePassed']for row in result['rows']if row['profile']['size']<=32);save()
    except BaseException as e:
        result['failure']=type(e).__name__+': '+str(e);save();raise
    print(json.dumps({'complete':True,'rows':len(result['rows']),'smallGatesPassed':result['smallGatesPassed']}))
if __name__=='__main__':main()
