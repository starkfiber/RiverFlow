"""Build the combined opt-in SDK candidate, without replacing any stable package."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def create(destination):
    spec=importlib.util.spec_from_file_location('evolution_sdk',HERE/'sdk/stage_sdk.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    destination=module.stage(destination.resolve())
    report=HERE/'report/report.flow';(destination/'report.flow').write_bytes(report.read_bytes())
    provenance=json.loads((destination/'PROVENANCE.json').read_text())
    provenance['edition']='0.50C-measured-candidate'
    provenance['transformation']='Opt-in measured JSON spans with scalar alias/density fallback, plus bounded typed JSON/HTML reports. No compiler or stable runtime replacement.'
    for item in provenance['files']:
        if item['path']=='text.flow':
            item['packageSHA256']=sha(destination/'text.flow')
            item['transformation']+='; preserve scalar writer under writer_json_scalar and add identical-export span writer'
            item['additionalInputs'].append({'path':'experiments/evolution-20261117/sdk/json_spans.flow','SHA256':sha(HERE/'sdk/json_spans.flow')})
    provenance['files'].append({'path':'report.flow','source':'experiments/evolution-20261117/report/report.flow','sourceSHA256':sha(report),'packageSHA256':sha(report),'transformation':'Exact reviewed source; no hidden IO or compiler effects','additionalInputs':[]})
    (destination/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (destination/'rf2-sdk.manifest').write_text('rf2-sdk-v1\n'+''.join(f'{sha(destination/x["path"])} {x["path"]}\n'for x in provenance['files']))
    (destination/'SDK-CANDIDATE.json').unlink()
    return destination
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path);a=parser.parse_args();print(create(a.destination))
