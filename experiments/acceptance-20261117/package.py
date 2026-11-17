"""Build a reviewed development source SDK; never replace stable/release files."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
HERE=Path(__file__).resolve().parent
CLI_SHA="7d4e4c2cef46bfccf78ed6d8cb0f1db9456f7ec87ac651723c1228e0ef52b1a9"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def create(destination):
    source=HERE/'ai/text-report-cli.flow'
    if sha(source)!=CLI_SHA:raise ValueError('CLI source drift; review and qualify before changing this pin')
    sys.path.insert(0,str(HERE/'sdk'))
    from stage_complete import complete
    destination=complete(destination.resolve())
    (destination/'text-report-cli.flow').write_bytes(source.read_bytes())
    p=json.loads((destination/'PROVENANCE.json').read_text())
    p['edition']='0.50D-reviewed-development'
    p['transformation']+='; explicit synchronous typed text-report CLI callback library'
    p['limits']=['Not a stable release','R3 small-input performance qualified; retained dense large-input loss','Callback is trusted Systems code; effects and reentrancy are not sandboxed','AI usefulness must be checked against complete task tests, never source size']
    p['files'].append({'path':'text-report-cli.flow','source':'experiments/acceptance-20261117/ai/text-report-cli.flow','sourceSHA256':CLI_SHA,'packageSHA256':CLI_SHA,'transformation':'Exact reviewed callback library','additionalInputs':[]})
    (destination/'PROVENANCE.json').write_text(json.dumps(p,indent=2)+'\n')
    (destination/'rf2-sdk.manifest').write_text('rf2-sdk-v1\n'+''.join(f'{sha(destination/x["path"])} {x["path"]}\n'for x in p['files']))
    return destination
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args();print(create(a.destination))
