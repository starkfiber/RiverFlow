"""Produce the complete opt-in R3 SDK, including the unchanged report source."""
from pathlib import Path
import argparse,hashlib,json
from stage_sdk import stage,ROOT,HERE
REPORT_SHA='8f272ebf7604989be3844267c0adc283295acdae34839079ba609a9f80c37ba8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def complete(destination):
    report=ROOT/'experiments/evolution-20261117/report/report.flow'
    if sha(report)!=REPORT_SHA:raise ValueError('Report source drift: review before composition')
    destination=stage(destination.resolve());(destination/'report.flow').write_bytes(report.read_bytes())
    provenance=json.loads((destination/'PROVENANCE.json').read_text());provenance['edition']='0.50D-small-fields-candidate'
    provenance['transformation']='Opt-in direct scalar JSON field path through256bytes; retained large span/alias/density paths; unchanged typed report composition. Default SDK and releases untouched.'
    for item in provenance['files']:
        if item['path']=='text.flow':
            item['packageSHA256']=sha(destination/'text.flow');item['transformation']+='; direct scalar small-field body and retained large span fallback'
            item['additionalInputs'].append({'path':'experiments/acceptance-20261117/sdk/json_spans.flow','SHA256':sha(HERE/'json_spans.flow')})
    provenance['files'].append({'path':'report.flow','source':'experiments/evolution-20261117/report/report.flow','sourceSHA256':REPORT_SHA,'packageSHA256':REPORT_SHA,'transformation':'Exact previously qualified source; no hidden IO','additionalInputs':[]})
    (destination/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (destination/'rf2-sdk.manifest').write_text('rf2-sdk-v1\n'+''.join(f'{sha(destination/x["path"])} {x["path"]}\n'for x in provenance['files']))
    (destination/'SDK-CANDIDATE.json').unlink()
    return destination
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args();print(complete(a.destination))
