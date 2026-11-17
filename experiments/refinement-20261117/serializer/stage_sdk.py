#!/usr/bin/env python3
"""Create a fresh source-bound SDK candidate; the original SDK is never edited."""
from pathlib import Path
import argparse, hashlib, json, shutil
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
EXPECTED='5d0ef4fd5cd34d40c3be21b5b334e607227fe80fd5c036bf2abefc144e209b5b'
PROTECTED=('sdk/v1','native/compiler','dist','bin','plugin','.codex-plugin','site/downloads')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe_destination(destination):
    destination=Path(destination)
    if destination.is_symlink():raise ValueError('Use a fresh destination, not a symlink')
    destination=destination.resolve()
    for name in PROTECTED:
        protected=(ROOT/name).resolve()
        if destination==protected or protected in destination.parents:
            raise ValueError('Experimental output cannot enter protected source/release tree: '+name)
    if destination.exists():raise ValueError('Use a new destination; no evidence is overwritten')
    return destination
def stage(destination):
    destination=safe_destination(destination)
    source=ROOT/'sdk/v1'
    if sha(source/'text.flow')!=EXPECTED:raise ValueError('SDK text baseline identity changed')
    shutil.copytree(source,destination)
    original=(source/'text.flow').read_text()
    original=original.replace('fn writer_json(out:Writer,p,n)','fn writer_json_scalar(out:Writer,p,n)',1)
    candidate=(HERE/'json_spans.flow').read_text().replace('module json_spans\n','',1).replace('fn writer_json_spans(out:Writer,p,n)','fn writer_json(out:Writer,p,n)',1).replace('return writer_json(out,p,n)','return writer_json_scalar(out,p,n)')
    (destination/'text.flow').write_text(original+'\n'+candidate)
    manifest=(source/'rf2-sdk.manifest').read_text().replace(EXPECTED+' text.flow',sha(destination/'text.flow')+' text.flow')
    (destination/'rf2-sdk.manifest').write_text(manifest)
    (destination/'SDK-CANDIDATE.json').write_text(json.dumps(dict(schema='rf2.json-span-sdk.v1',productionTouched=False,baselineTextSHA256=EXPECTED,candidateTextSHA256=sha(destination/'text.flow'),patchSourceSHA256=sha(HERE/'json_spans.flow'),behavior='Same R3 small/alias paths; disjoint large dense fallback and span escapes use checked direct bytes, preserving legacy atomic/partial writes.'),indent=2)+'\n')
    return destination
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args();print(stage(a.destination))
