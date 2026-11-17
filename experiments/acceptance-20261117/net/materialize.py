"""Materialize source variants from one reviewed baseline; no compile or execution."""
from pathlib import Path
import argparse,hashlib,json,shutil
from parser_transform import apply
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    sources=json.loads((H/'SOURCE-MANIFEST.json').read_text())['inputSources']
    for name,want in sources.items():
        relative=name.split('/experiments/rf2net/',1)[1];assert sha(H/'snapshot'/relative)==want,'Baseline identity changed: '+relative
    if not args.check:
        for variant in ['baseline','candidate']:
            if(H/variant).exists():raise FileExistsError('Existing source variant; use --check or preserve it before a deliberate new materialization')
        for variant in ['baseline','candidate']:shutil.copytree(H/'snapshot',H/variant)
        for family in ['dhcp','dhcp-durable']:
            p=H/'candidate'/family/'dhcp.flow';p.write_text(apply(p.read_text()))
    for variant in ['baseline','candidate']:
        for p in (H/'snapshot').rglob('*'):
            if not p.is_file():continue
            relative=p.relative_to(H/'snapshot');want=p.read_bytes()
            if variant=='candidate'and str(relative)in ['dhcp/dhcp.flow','dhcp-durable/dhcp.flow']:want=apply(p.read_text()).encode()
            assert(H/variant/relative).read_bytes()==want,'Variant drift: '+str(relative)
    print('Reviewed baseline and candidate source identities verified; no native image executed')
if __name__=='__main__':main()
