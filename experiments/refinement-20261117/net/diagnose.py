"""Reanalyze a preserved campaign without native execution or replacing its gates."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, statistics

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('net_native_controller', HERE/'controller.py')
controller = importlib.util.module_from_spec(spec); spec.loader.exec_module(controller)

def main(source, out):
    old = json.loads(source.read_text()); assert old['completed']
    out.mkdir(parents=True, exist_ok=False)
    result = {'schema':'rf2.net.historical-estimator-diagnostic.v1', 'inputSHA256':controller.sha(source),
              'inputPath':str(source), 'nativeExecution':False, 'changesHistoricalDecision':False,
              'limits':['No native-region clock was recorded previously; launch versus scheduling/CPU causes cannot be separated retrospectively.',
                        'Recomputed paired-median estimates are exploratory, not a replacement of the historical frozen decision.'], 'rows':[]}
    for row in old['rows']:
        b=[p['ms']['baseline'] for p in row['pairs']]
        c=[p['ms']['candidate'] for p in row['pairs']]
        ratio=controller.statistics_for(b,c,171127)
        pairs=[cv/bv for bv,cv in zip(b,c)]
        result['rows'].append({'family':row['family'],'mode':row['mode'],'profile':row['profile'],
            'historicalRatioOfMedians':row['candidateBaselineRatio'], 'historical95':row['pairedBootstrap95'],
            'prospectivePairedMedianDiagnostic':ratio,
            'processBaselineRangeMs':[min(b),max(b)], 'processCandidateRangeMs':[min(c),max(c)],
            'pairedRatioRange':[min(pairs),max(pairs)],
            'baselineRelativeMAD':statistics.median(abs(x-statistics.median(b)) for x in b)/statistics.median(b),
            'candidateRelativeMAD':statistics.median(abs(x-statistics.median(c)) for x in c)/statistics.median(c)})
    (out/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'rows':len(result['rows']),'nativeExecution':False,'changesHistoricalDecision':False}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();main(a.input.resolve(),a.out.resolve())
