"""Generate signatures from staged SDK sources; no inferred APIs."""
from pathlib import Path
import re,sys
folder=Path(sys.argv[1]);out=Path(sys.argv[2]);lines=['# Exact SDK signatures','', 'Read API.md for contracts; these signatures are extracted from the supplied source.','']
for p in sorted(folder.iterdir()):
 if p.suffix not in('.flow','.rf2'):continue
 lines+=['## '+p.name,'','```flow']
 lines += [line for line in p.read_text().splitlines()if re.match(r'^(fn |record |result |array |collection |text |vector |resource )',line)]
 lines+=['```','']
out.write_text('\n'.join(lines))
