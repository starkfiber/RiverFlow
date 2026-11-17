"""Source-bound native-region experiment; comparative measurement needs root grant.

All unique source, inputs and evidence persist. Only native images use TMPDIR.
"""
from pathlib import Path
import argparse, ast, hashlib, importlib.util, json, os, platform, random
import shutil, statistics, struct, subprocess, time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'experiments/acceptance-20261117/net'
COMPILER = Path('/Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program')
COMPILER_SHA = '4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
PARSER_SHA = {
    'dhcp': {'baseline': 'a97e44b3b52c6c584e0cf5c256e30fdcf2bfbafbc8bcb38c1d7b089d9e4570cb',
             'candidate': 'ddfea2e07811ef42ba14428b3edc5d68c4ea5f387416cb82df1805e5110945ad'},
    'dhcp-durable': {'baseline': '0b4e9f166823185b63957d965a2318c7649ff6e7f314cf3c7cbf697dad41982c',
                     'candidate': '0dd7483d90d2fffab33e5066d8e99c67f73c49e9ae7266f1cf2f19cb7aac369a'}}
MASK = (1 << 64) - 1

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

def dependency_hashes():
    paths = [HERE / n for n in ['controller.py', 'PLAN.json', 'probe.flow', 'clock.flow', 'clock-controls.flow', 'io-result.flow']]
    paths += [OLD / 'parser_transform.py', OLD / 'snapshot/dhcp/verify.py']
    paths += [OLD / 'snapshot' / f / 'dhcp.flow' for f in PARSER_SHA]
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}

def oracle():
    ns = {'struct': struct, 'hashlib': hashlib, 'SERVER': 0x0a4d0002, 'BASE': 0x0a4d0064}
    src = OLD / 'snapshot/dhcp/verify.py'
    for node in ast.parse(src.read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in ['packet', 'Oracle']:
            exec(compile(ast.Module([node], type_ignores=[]), str(src), 'exec'), ns)
    return ns

def statistics_for(base, candidate, seed, samples=10000):
    ratios = [c / b for b, c in zip(base, candidate)]
    rng = random.Random(seed)
    boot = sorted(statistics.median(ratios[rng.randrange(len(ratios))] for _ in ratios) for _ in range(samples))
    return {'point': statistics.median(ratios), 'lower95': boot[249], 'upper95': boot[9749],
            'method': 'median paired C/B ratios; percentile bootstrap of whole ratios',
            'historicalRatioOfMedians': statistics.median(candidate) / statistics.median(base)}

def estimator_controls():
    b, c = [1, 100, 1000], [2, 50, 1000]
    r = statistics_for(b, c, 1)
    assert r['point'] == 1 and r['historicalRatioOfMedians'] == .5
    scales = [100, 1, .001]
    scaled = statistics_for([v*s for v,s in zip(b,scales)], [v*s for v,s in zip(c,scales)], 1)
    assert scaled['point'] == r['point']
    same = statistics_for([1, 2, 3], [1, 2, 3], 1)
    assert same['point'] == same['lower95'] == same['upper95'] == 1
    return {'pairedVsUnpairedDistinguished': True, 'pairScaleInvariant': True, 'identityRatioExact': True}

def fixture(ns, profile, xid):
    p = ns['packet'](xid=xid)
    if profile == 'short-valid': return p[:244]
    if profile == 'normal-300': return p
    if profile == 'max-576': return p.ljust(576, b'\0')
    if profile == 'bad-last-byte': return p.ljust(575, b'\0') + b'\1'
    if profile == 'early-reject': return b'\2' + p[1:]
    raise ValueError(profile)

def expected(ns, data, repetitions):
    code, meta = ns['Oracle']().parse(data)
    unit = code if code else meta[0] + meta[1] + meta[5]
    return unit * repetitions & MASK, unit * 32 & MASK

def prepare(out):
    assert sha(COMPILER) == COMPILER_SHA
    out.mkdir(parents=True, exist_ok=False)
    tmp = Path(os.environ['TMPDIR']).resolve()
    assert '/Volumes/Mac Work Cache/' in str(tmp)
    binaries = tmp / ('net-refine-' + hashlib.sha256(str(out).encode()).hexdigest()[:12])
    binaries.mkdir()
    spec = importlib.util.spec_from_file_location('frozen_parser_transform', OLD / 'parser_transform.py')
    transform = importlib.util.module_from_spec(spec); spec.loader.exec_module(transform)
    manifest = {'schema': 'rf2.net.native-region-prepared.v1', 'compilerSHA256': COMPILER_SHA,
                'dependencies': dependency_hashes(), 'plan': json.loads((HERE / 'PLAN.json').read_text()),
                'probes': [], 'clockControls': [], 'estimatorControls': estimator_controls()}
    (out / 'CONTROLLER.py').write_bytes(Path(__file__).read_bytes())
    ns = oracle()
    inputs = out / 'inputs'; inputs.mkdir()
    for name in manifest['plan']['profiles']:
        (inputs / (name + '.bin')).write_bytes(fixture(ns, name, 0x12345678))
    commands = []
    def build(entry, binary, mode):
        command = [str(COMPILER), str(entry), str(binary), '--compact'] + (['--opt'] if mode == 'opt' else [])
        p = subprocess.run(command, capture_output=True, timeout=30)
        commands.append({'command': command, 'exit': p.returncode, 'stdout': p.stdout.decode(errors='replace'), 'stderr': p.stderr.decode(errors='replace')})
        write_json(out / 'BUILD.json', commands)
        assert p.returncode == 0, commands[-1]
        subprocess.run(['codesign', '-s', '-', str(binary)], capture_output=True, check=True)
        return sha(binary)
    clock_dir = out / 'clock-source'; clock_dir.mkdir()
    for name in ['clock.flow', 'clock-controls.flow', 'io-result.flow']: shutil.copyfile(HERE/name, clock_dir/name)
    for mode in ['plain', 'opt']:
        binary = binaries / ('clock-' + mode)
        h = build(clock_dir/'clock-controls.flow', binary, mode)
        manifest['clockControls'].append({'mode': mode, 'binary': str(binary), 'binarySHA256': h})
    for family in manifest['plan']['families']:
        baseline = (OLD/'snapshot'/family/'dhcp.flow').read_text()
        assert hashlib.sha256(baseline.encode()).hexdigest() == PARSER_SHA[family]['baseline']
        for variant in ['baseline', 'candidate']:
            parser = baseline if variant == 'baseline' else transform.apply(baseline)
            assert hashlib.sha256(parser.encode()).hexdigest() == PARSER_SHA[family][variant]
            source = out/'source'/family/variant; source.mkdir(parents=True)
            (source/'dhcp.flow').write_text(parser)
            for name in ['clock.flow', 'probe.flow', 'io-result.flow']: shutil.copyfile(HERE/name, source/name)
            for mode in manifest['plan']['modes']:
                binary = binaries / (family+'-'+variant+'-'+mode)
                h = build(source/'probe.flow', binary, mode)
                manifest['probes'].append({'family': family, 'variant': variant, 'mode': mode, 'binary': str(binary),
                    'binarySHA256': h, 'parserSHA256': PARSER_SHA[family][variant], 'entrySHA256': sha(source/'probe.flow')})
    write_json(out/'PREPARED.json', manifest)
    print(json.dumps({'prepared': True, 'probes': len(manifest['probes']), 'comparativeTiming': False}))

def load(prepared):
    m = json.loads((prepared/'PREPARED.json').read_text())
    assert m['dependencies'] == dependency_hashes(), 'Source drift: prepare a new campaign'
    assert m['compilerSHA256'] == sha(COMPILER) == COMPILER_SHA
    for p in m['probes'] + m['clockControls']: assert sha(p['binary']) == p['binarySHA256']
    return m

def decode(stdout, wanted, warm, repeats, process_us):
    assert len(stdout) == 56, 'Exact native output framing'
    checksum, native_us, observed, started, finished, numerator, denominator, warm_checksum = struct.unpack('<QQQQQIIQ', stdout)
    assert checksum == wanted and warm_checksum == warm and observed == repeats
    assert 0 < started <= finished and numerator > 0 and denominator > 0
    delta = finished - started
    assert delta <= MASK // numerator
    assert native_us == delta*numerator//denominator//1000, 'Independent exact timebase conversion'
    assert native_us <= process_us + 2000, 'Native region must fit process envelope'
    return {'nativeUs': native_us, 'processUs': process_us, 'outsideNativeUs': process_us-native_us,
            'checksum': checksum, 'warmChecksum': warm_checksum, 'repetitions': observed,
            'startedTicks': started, 'finishedTicks': finished, 'numerator': numerator, 'denominator': denominator}

def invoke(probe, ns, data, repeats, out, context, fragmented=False):
    wire = struct.pack('<QH', repeats, len(data)) + data
    wanted, warm = expected(ns, data, repeats)
    start = time.monotonic_ns()
    if fragmented:
        p = subprocess.Popen([probe['binary']], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for i in range(0, len(wire), 3):
            p.stdin.write(wire[i:i+3]); p.stdin.flush(); time.sleep(.0001)
        p.stdin.close(); p.stdin = None
        stdout, stderr = p.communicate(timeout=20)
    else:
        p = subprocess.run([probe['binary']], input=wire, capture_output=True, timeout=20)
        stdout, stderr = p.stdout, p.stderr
    process_us = (time.monotonic_ns()-start)/1000
    try:
        assert p.returncode == 0 and stderr == b''
        result = decode(stdout, wanted, warm, repeats, process_us)
    except BaseException:
        (out/'FAILURE-input.bin').write_bytes(wire); (out/'FAILURE-stdout.bin').write_bytes(stdout); (out/'FAILURE-stderr.bin').write_bytes(stderr)
        write_json(out/'FAILURE.json', {'context': context, 'probe': probe, 'returncode': p.returncode})
        raise
    with (out/'SAMPLES.jsonl').open('a') as f:
        f.write(json.dumps({'context': context, 'probeSHA256': probe['binarySHA256'], 'inputSHA256': hashlib.sha256(wire).hexdigest(), **result})+'\n')
    return result

def verify(prepared, out):
    m = load(prepared); out.mkdir(parents=True, exist_ok=False); ns = oracle(); rows = []
    for p in m['clockControls']:
        done = subprocess.run([p['binary']], capture_output=True, timeout=10)
        assert done.returncode == 0 and done.stdout == done.stderr == b''
        rows.append({'clockMode': p['mode'], 'arithmeticControls': 11, 'liveMonotonicControl': True})
    for p in m['probes']:
        for profile in m['plan']['profiles']:
            data = fixture(ns, profile, 0x87654321)
            for fragmented in [False, True]:
                result = invoke(p, ns, data, 3, out, {'phase': 'correctness', 'profile': profile, 'fragmented': fragmented}, fragmented)
                rows.append({'probe': p, 'profile': profile, 'fragmented': fragmented, 'exactOutput': True})
        good = struct.pack('<QH', 1, 576) + fixture(ns, 'max-576', 1)
        for wire in [b'', good[:9], good[:-1], good+b'\0', struct.pack('<QH',0,576)+good[10:], struct.pack('<QH',100000001,576)+good[10:]]:
            done = subprocess.run([p['binary']], input=wire, capture_output=True, timeout=5)
            assert done.returncode == 2 and done.stdout == b''
            rows.append({'probe': p, 'refusedInputSHA256': hashlib.sha256(wire).hexdigest(), 'rejection': True})
    result = {'complete': True, 'allPassed': True, 'comparativeTiming': False, 'clockModes': 2,
              'validParserClockChecks': 80, 'framingRefusals': 48, 'preparedSHA256': sha(prepared/'PREPARED.json'), 'rows': rows}
    write_json(out/'RESULTS.json', result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))

def measure(prepared, out):
    assert os.environ.get('RF2_EXCLUSIVE_TIMING') == '1', 'Root exclusive grant required'
    m = load(prepared); plan = m['plan']; ns = oracle()
    out.mkdir(parents=True, exist_ok=False)
    write_json(out/'STARTED.json', {'preparedSHA256': sha(prepared/'PREPARED.json'), 'UTC': time.time(), 'platform': platform.platform(), 'plan': plan})
    rng = random.Random(plan['orderSeed']); result = {'complete': False, 'preparedSHA256': sha(prepared/'PREPARED.json'), 'rows': [], 'plan': plan}
    try:
        for family in plan['families']:
            for mode in plan['modes']:
                probes = {p['variant']:p for p in m['probes'] if p['family']==family and p['mode']==mode}
                for profile, repeats in plan['profiles'].items():
                    warmups=[]; pairs=[]
                    for i in range(plan['separateWarmupPairs']):
                        data=fixture(ns,profile,rng.randrange(1<<32))
                        for v,p in probes.items():
                            context={'phase':'warmup','family':family,'mode':mode,'profile':profile,'variant':v,'index':i}
                            warmups.append({'variant':v,**invoke(p,ns,data,repeats,out,context)})
                    for i in range(plan['pairs']):
                        data=fixture(ns,profile,rng.randrange(1<<32)); order=list(probes); rng.shuffle(order); observed={}
                        for v in order:
                            context={'phase':'comparison','family':family,'mode':mode,'profile':profile,'variant':v,'pair':i}
                            observed[v]=invoke(probes[v],ns,data,repeats,out,context)
                        pairs.append({'pair':i,'order':order,'inputSHA256':hashlib.sha256(data).hexdigest(),'observed':observed})
                    b=[p['observed']['baseline']['nativeUs'] for p in pairs]; c=[p['observed']['candidate']['nativeUs'] for p in pairs]
                    assert min(b+c)>0
                    stats=statistics_for(b,c,plan['bootstrapSeed']+len(result['rows']),plan['bootstrapSamples'])
                    proc=statistics_for([p['observed']['baseline']['processUs'] for p in pairs],[p['observed']['candidate']['processUs'] for p in pairs],plan['bootstrapSeed']+len(result['rows']))
                    gate=stats['point']<=plan['gate']['candidateBaselinePointMaximum'] and stats['upper95']<=plan['gate']['upperPairedBootstrap95Maximum'] and min(b+c)>=plan['gate']['minimumNativeMicrosecondsEveryMeasuredProcess']
                    row={'family':family,'mode':mode,'profile':profile,'repetitions':repeats,'nativeRatios':stats,'processRatios':proc,'baselineMedianUs':statistics.median(b),'candidateMedianUs':statistics.median(c),'minimumNativeUs':min(b+c),'gatePassed':gate,'warmups':warmups,'pairs':pairs}
                    result['rows'].append(row);write_json(out/'RESULTS.json',result)
                    print(family,mode,profile,round(stats['point'],5),[round(stats['lower95'],5),round(stats['upper95'],5)],'gate',gate,flush=True)
        result['complete']=True
        small=[r for r in result['rows'] if r['profile'] in plan['smallCaseProfiles']]
        result['smallCasePromotionGatePassed']=all(r['gatePassed'] for r in small)
        write_json(out/'RESULTS.json',result)
    except BaseException as e:
        result['failure']=type(e).__name__+': '+str(e);write_json(out/'RESULTS.json',result);raise
    print(json.dumps({'complete':True,'rows':len(result['rows']),'smallCasePromotionGatePassed':result['smallCasePromotionGatePassed']}))

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['prepare','verify','measure']);ap.add_argument('--prepared',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.phase=='prepare': prepare(a.out.resolve())
    elif a.phase=='verify': verify(a.prepared.resolve(),a.out.resolve())
    else: measure(a.prepared.resolve(),a.out.resolve())
