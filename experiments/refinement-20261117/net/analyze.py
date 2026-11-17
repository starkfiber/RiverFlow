"""Summarize existing once-only evidence; never launch native probes or rerun timing."""
from pathlib import Path
import argparse
import hashlib
import json
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main(evidence, out):
    timing_path = evidence / 'timing-1/RESULTS.json'
    prepared_path = evidence / 'prepared-2/PREPARED.json'
    timing = json.loads(timing_path.read_text())
    prepared = json.loads(prepared_path.read_text())
    verify = json.loads((evidence / 'verify-2/RESULTS.json').read_text())
    logic = json.loads((evidence / 'logic-controls-1/RESULTS.json').read_text())
    assert timing['complete'] and verify['complete'] and verify['allPassed'] and logic['allPassed']
    assert timing['preparedSHA256'] == verify['preparedSHA256'] == sha(prepared_path)
    assert timing['plan'] == prepared['plan'] == json.loads((HERE / 'PLAN.json').read_text())
    for relative, expected_hash in prepared['dependencies'].items():
        assert sha(ROOT / relative) == expected_hash, relative
    plan = timing['plan']; rows = []; measured = 0; warm = 0
    keys = set()
    for row in timing['rows']:
        key = (row['family'], row['mode'], row['profile'])
        assert key not in keys; keys.add(key)
        assert len(row['pairs']) == plan['pairs'] and len(row['warmups']) == 2 * plan['separateWarmupPairs']
        base = []; candidate = []
        for index, pair in enumerate(row['pairs']):
            assert pair['pair'] == index and sorted(pair['order']) == ['baseline', 'candidate']
            observed = pair['observed']
            assert observed['baseline']['checksum'] == observed['candidate']['checksum']
            assert observed['baseline']['warmChecksum'] == observed['candidate']['warmChecksum']
            for variant in ('baseline', 'candidate'):
                value = observed[variant]
                assert value['repetitions'] == plan['profiles'][row['profile']]
                assert 0 < value['startedTicks'] <= value['finishedTicks']
                assert value['numerator'] > 0 and value['denominator'] > 0
                assert value['nativeUs'] == (value['finishedTicks'] - value['startedTicks']) * value['numerator'] // value['denominator'] // 1000
            base.append(observed['baseline']['nativeUs']); candidate.append(observed['candidate']['nativeUs'])
        ratios = [c / b for b, c in zip(base, candidate)]
        assert row['nativeRatios']['point'] == statistics.median(ratios)
        assert row['baselineMedianUs'] == statistics.median(base)
        assert row['candidateMedianUs'] == statistics.median(candidate)
        assert row['minimumNativeUs'] == min(base + candidate)
        gates = {'point': row['nativeRatios']['point'] <= plan['gate']['candidateBaselinePointMaximum'],
                 'upper95': row['nativeRatios']['upper95'] <= plan['gate']['upperPairedBootstrap95Maximum'],
                 'minimumDuration': min(base + candidate) >= plan['gate']['minimumNativeMicrosecondsEveryMeasuredProcess']}
        assert row['gatePassed'] == all(gates.values())
        rows.append({k: row[k] for k in ('family', 'mode', 'profile', 'repetitions', 'nativeRatios', 'processRatios', 'baselineMedianUs', 'candidateMedianUs', 'minimumNativeUs', 'gatePassed')})
        rows[-1]['gateComponents'] = gates
        measured += 2 * len(row['pairs']); warm += len(row['warmups'])
    assert len(rows) == len(plan['families']) * len(plan['modes']) * len(plan['profiles']) == 20
    small = [r for r in rows if r['profile'] in plan['smallCaseProfiles']]
    optimized_small = [r for r in small if r['mode'] == 'opt']
    assert timing['smallCasePromotionGatePassed'] == all(r['gatePassed'] for r in small)
    sample_lines = sum(1 for _ in (evidence / 'timing-1/SAMPLES.jsonl').open())
    assert sample_lines == measured + warm == 1320
    receipt_files = ['prepared-2/PREPARED.json', 'verify-2/RESULTS.json', 'logic-controls-1/RESULTS.json',
                     'historical-estimator-1/RESULTS.json', 'timing-1/RESULTS.json', 'timing-1/SAMPLES.jsonl', 'timing-1/STARTED.json']
    result = {'schema': 'rf2.net.native-region-analysis.v1', 'complete': True, 'nativeExecution': False,
              'comparativeCampaignsAddedByAnalysis': 0, 'productParserChanged': False,
              'preparedSHA256': sha(prepared_path), 'measuredProcesses': measured, 'separateWarmupProcesses': warm,
              'rows': rows, 'smallGates': {'passed': sum(r['gatePassed'] for r in small), 'total': len(small)},
              'optimizedSmallGates': {'passed': sum(r['gatePassed'] for r in optimized_small), 'total': len(optimized_small)},
              'allModeSmallPromotion': timing['smallCasePromotionGatePassed'],
              'decision': 'Optimized-only native small-case qualification; no default/stable/live promotion. Plain durable early-reject remains inconclusive.',
              'limits': ['Native elapsed is monotonic wall time, not CPU cycles or exclusive hardware time.',
                         'A shared Mac with user applications is not a dedicated benchmark host.',
                         'Original optimized normal-300 includes a 47850us native sample, below the fixed 50000us duration floor; preserve its nonqualifying row.',
                         'Bootstrap intervals are preserved from the frozen controller, not recomputed or selected by this analysis.',
                         'Historical launch-inclusive measurements and decisions remain unchanged; estimator diagnostic is separate.'],
              'evidenceSHA256': {name: sha(evidence / name) for name in receipt_files},
              'analysisSourceSHA256': sha(Path(__file__))}
    out.mkdir(parents=True, exist_ok=False)
    (out / 'ANALYSIS.json').write_text(json.dumps(result, indent=2) + '\n')
    lines = ['family\tmode\tprofile\tpaired_median_C_over_B\tlower95\tupper95\tminimum_native_us\tgate_passed']
    for row in rows:
        stats = row['nativeRatios']
        lines.append('\t'.join(map(str, [row['family'], row['mode'], row['profile'], stats['point'], stats['lower95'], stats['upper95'], row['minimumNativeUs'], row['gatePassed']])))
    (out / 'ROWS.tsv').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: result[k] for k in ('complete', 'nativeExecution', 'measuredProcesses', 'smallGates', 'optimizedSmallGates', 'allModeSmallPromotion')}))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--evidence', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); main(args.evidence.resolve(), args.out.resolve())
