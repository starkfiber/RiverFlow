"""Frozen native-loop and enclosing-process JSON report benchmark.

Preparation may run with correctness jobs. Measurement requires the root's
exclusive timing slot. Only rebuildable binaries use the disposable TMPDIR;
source, fixtures, frozen configuration and all unique measurements persist.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,platform,random,shutil,statistics,subprocess,tempfile,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
COMPILER_SHA='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
oracle=load_module('sdk_benchmark_oracle',HERE/'qualify.py')
SAMPLE_LOG=None
SAMPLE_CONTEXT={}
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
    if SAMPLE_LOG is not None:
        with SAMPLE_LOG.open('a')as event:event.write(json.dumps({'context':SAMPLE_CONTEXT,'args':args,'exit':p.returncode,'processSeconds':elapsed,'stdoutSHA256':hashlib.sha256(p.stdout).hexdigest(),'wantedSHA256':hashlib.sha256(wanted).hexdigest(),'stderr':p.stderr.decode(errors='replace')})+'\n')
        if p.returncode!=0 or p.stdout!=wanted:
            SAMPLE_LOG.with_suffix('.failed-stdout').write_bytes(p.stdout)
    assert p.returncode==0 and p.stdout==wanted,(args,p.returncode,p.stderr[:300])
    fields=p.stderr.strip().split(b':');assert len(fields)==5,p.stderr
    used,error,native_us,consumed,observed_repeats=map(int,fields)
    assert used==len(wanted)and error==0 and observed_repeats==repeats
    assert consumed==repeats*(used+wanted[0]+wanted[-1])
    # Reject invalid native elapsed/envelope results; never retry a sample.
    assert native_us>=0 and native_us/1e6<=elapsed+0.002,(native_us,elapsed)
    return {'nativeUs':native_us,'processSeconds':elapsed,'checksum':consumed,'outputSHA256':hashlib.sha256(wanted).hexdigest()}
def main():
    global SAMPLE_LOG,SAMPLE_CONTEXT
    ap=argparse.ArgumentParser();ap.add_argument('--compiler',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--measure',action='store_true');ap.add_argument('--baseline-record',type=Path);a=ap.parse_args();a.compiler=a.compiler.resolve();assert sha(a.compiler)==COMPILER_SHA
    d=a.out.resolve();commands=[]
    if not a.measure:
        d.mkdir(parents=True,exist_ok=False);(d/'inputs').mkdir()
        current=load_module('sdk_current_stage',HERE/'stage_sdk.py');previous=load_module('sdk_previous_stage',HERE.parent/'stage_sdk.py')
        shutil.copytree(ROOT/'sdk/v1',d/'baseline-sdk');current.stage(d/'candidate-sdk');previous.stage(d/'previous-sdk')
        template=(HERE/'bench-task.flow.in').read_text().replace('__CANDIDATE_IMPORT__','').replace('__JSON__','writer_json')
        (d/'bench.flow').write_text(template);(d/'clock.flow').write_bytes((HERE/'clock.flow').read_bytes())
        assert a.baseline_record is not None,'Supply preserved baseline receipt'
        baseline_record=json.loads(a.baseline_record.read_text());assert baseline_record['complete']
        preserved={(x['profile']['size'],x['profile']['density'],x['mode']):x for x in baseline_record['rows']}
        frozen={'schema':'rf2.sdk.native-benchmark.v2','compilerSHA256':COMPILER_SHA,'controllerSHA256':sha(Path(__file__)),'oracleSHA256':sha(HERE/'qualify.py'),'templateSHA256':sha(HERE/'bench-task.flow.in'),'clockSourceSHA256':sha(HERE/'clock.flow'),'entrySHA256':sha(d/'bench.flow'),'candidateSourceSHA256':sha(HERE/'json_spans.flow'),'trials':31,'warmupIterationsPerProcess':16,'bootstrapResamples':10000,'orderSeed':1172026,'smallGate':{'candidateBaselineMedianRatioAtMost':1.03,'upper95AtMost':1.05,'minimumNativeMicroseconds':50000},'nativeClock':'Darwin mach_absolute_time via vm_clock_ticks; subtractticks before checked timebase scaling to microseconds, monotonic elapsed not CPUcycles','processClock':'Python monotonic_ns enclosing startup, input, initialHTML conversion, warmups, repeated serialization and output','noRetries':True,'profiles':[],'calibration':{'method':'Baseline-only current warmup, initial counts from preserved R3 baseline, then freeze all counts before comparisons','targetNativeMicroseconds':100000,'sourceReceiptSHA256':sha(a.baseline_record),'noTrimmingOrRetries':True},'affectedGate':{'mode':'opt','size':16384,'density':'escaped','pointAtMost':1.03,'upper95AtMost':1.05,'minimumNativeMicroseconds':50000,'candidateVsR3Upper95AtMost':1.0},'modules':{v:{p.name:sha(p)for p in sorted((d/(v+'-sdk')).iterdir())if p.is_file()}for v in ['baseline','candidate','previous']}}
        for size in [0,32,1024,16384,262144]:
            for density in ['plain','mixed','escaped']:
                if size==0 and density!='plain':continue
                seed={'plain':b'alpha beta gamma 0123456789 ','mixed':b'alpha "beta" <gamma> & line\nsecond\tline ','escaped':b'"\\\n\t\r'}[density]
                data=(seed*((size+len(seed)-1)//len(seed)))[:size];path=d/'inputs'/f'{size}-{density}.txt';path.write_bytes(data)
                initial={}
                for mode in ['plain','opt']:
                    prior=preserved[size,density,mode];repeat=prior['profile']['repeats'];duration=prior['ratios']['candidate']['baselineMedianUs'];initial[mode]=max(1,min(2000000,round(repeat*100000/duration)))
                frozen['profiles'].append({'size':size,'density':density,'input':str(path),'inputSHA256':sha(path),'initialBaselineRepeats':initial,'variants':['baseline','previous','candidate']})
        (d/'FROZEN.json').write_text(json.dumps(frozen,indent=2))
    else:
        assert not(d/'STARTED.json').exists(),'Never reuse a measured campaign'
        frozen=json.loads((d/'FROZEN.json').read_text());assert frozen['controllerSHA256']==sha(Path(__file__))and frozen['oracleSHA256']==sha(HERE/'qualify.py')and frozen['templateSHA256']==sha(HERE/'bench-task.flow.in')and frozen['clockSourceSHA256']==sha(HERE/'clock.flow')and frozen['clockSourceSHA256']==sha(d/'clock.flow');assert frozen['compilerSHA256']==sha(a.compiler)and frozen['entrySHA256']==sha(d/'bench.flow')and frozen['candidateSourceSHA256']==sha(HERE/'json_spans.flow')
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
    smokes={}
    for (mode,variant),binary in programs.items():smokes[mode+'-'+variant]=invoke(binary,path,1,wanted)
    (d/('MEASURE-SMOKE.json'if a.measure else'PREPARE-SMOKE.json')).write_text(json.dumps({'comparativeTiming':False,'inputSHA256':sha(path),'exactOutputSHA256':hashlib.sha256(wanted).hexdigest(),'checks':smokes},indent=2))
    if not a.measure:
        print(json.dumps({'prepared':True,'programs':identities,'frozenSHA256':sha(d/'FROZEN.json')}));return
    for v in ['baseline','candidate','previous']:
        for name,want in frozen['modules'][v].items():assert sha(d/(v+'-sdk')/name)==want
    (d/'STARTED.json').write_text(json.dumps({'frozenSHA256':sha(d/'FROZEN.json'),'UTC':time.time(),'platform':platform.platform(),'exclusiveSlot':'Root granted; other sprint CPU jobs idle, unrelated Mac load not controlled'}))
    SAMPLE_LOG=d/'SAMPLES.jsonl'
    counts={};calibration=[]
    for profile in frozen['profiles']:
        path=Path(profile['input']);wanted=oracle.report_oracle(path.read_bytes())
        for mode in ['plain','opt']:
            initial=profile['initialBaselineRepeats'][mode];SAMPLE_CONTEXT={'phase':'calibration','size':profile['size'],'density':profile['density'],'mode':mode};sample=invoke(programs[mode,'baseline'],path,initial,wanted);assert sample['nativeUs']>0
            count=max(1,min(2000000,round(initial*100000/sample['nativeUs'])));key=str(profile['size'])+'-'+profile['density']+'-'+mode;counts[key]=count;calibration.append({'key':key,'initialRepeats':initial,'sample':sample,'frozenRepeats':count})
    (d/'COUNTS-FROZEN.json').write_text(json.dumps({'baseFrozenSHA256':sha(d/'FROZEN.json'),'counts':counts,'baselineOnlyCalibration':calibration},indent=2))
    result={'schema':'rf2.sdk.native-benchmark-result.v2','frozenSHA256':sha(d/'FROZEN.json'),'programSHA256':identities,'rows':[],'complete':False};rng=random.Random(frozen['orderSeed'])
    def save():(d/'RESULTS.json').write_text(json.dumps(result,indent=2))
    try:
        for profile in frozen['profiles']:
            path=Path(profile['input']);assert sha(path)==profile['inputSHA256'];wanted=oracle.report_oracle(path.read_bytes())
            for mode in ['plain','opt']:
                repeats=counts[str(profile['size'])+'-'+profile['density']+'-'+mode]
                trials=[]
                for trial in range(31):
                    order=list(profile['variants']);rng.shuffle(order);measurements={}
                    for v in order:
                        SAMPLE_CONTEXT={'phase':'comparison','size':profile['size'],'density':profile['density'],'mode':mode,'trial':trial,'variant':v}
                        measurements[v]=invoke(programs[mode,v],path,repeats,wanted)
                    trials.append({'trial':trial,'order':order,'measurements':measurements})
                    with(d/'TRIALS.jsonl').open('a')as f:f.write(json.dumps({'profile':profile['size'],'density':profile['density'],'mode':mode,**trials[-1]})+'\n')
                row={'profile':{**profile,'measuredRepeats':repeats},'mode':mode,'trials':trials,'ratios':{}}
                for v in profile['variants'][1:]:
                    base=[t['measurements']['baseline']['nativeUs']for t in trials];candidate=[t['measurements'][v]['nativeUs']for t in trials];assert min(base)>0 and min(candidate)>0
                    ratio=bootstrap_ratio(base,candidate,frozen['orderSeed']+len(result['rows']));ratio.update(baselineMedianUs=statistics.median(base),candidateMedianUs=statistics.median(candidate),minimumNativeUs=min(base+candidate),speedup=1/ratio['point']);row['ratios'][v]=ratio
                    if profile['size']<=32 and v=='candidate':ratio['smallGatePassed']=ratio['point']<=1.03 and ratio['upper95']<=1.05 and ratio['minimumNativeUs']>=50000
                prev=[t['measurements']['previous']['nativeUs']for t in trials];new=[t['measurements']['candidate']['nativeUs']for t in trials];row['candidateVsR3']=bootstrap_ratio(prev,new,frozen['orderSeed']+2000+len(result['rows']))
                if profile['size']==16384 and profile['density']=='escaped'and mode=='opt':
                    x=row['ratios']['candidate'];x['affectedGatePassed']=x['point']<=1.03 and x['upper95']<=1.05 and x['minimumNativeUs']>=50000 and row['candidateVsR3']['upper95']<=1.0
                result['rows'].append(row);save()
        result['complete']=True;result['affectedGatePassed']=all(row['ratios']['candidate'].get('affectedGatePassed',True)for row in result['rows']);result['smallGatesPassed']=all(row['ratios']['candidate']['smallGatePassed']for row in result['rows']if row['profile']['size']<=32);save()
    except BaseException as e:
        result['failure']=type(e).__name__+': '+str(e);save();raise
    print(json.dumps({'complete':True,'rows':len(result['rows']),'smallGatesPassed':result['smallGatesPassed'],'affectedGatePassed':result['affectedGatePassed']}))
if __name__=='__main__':main()
