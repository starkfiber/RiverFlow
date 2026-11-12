"""Explicit derivation of the existing native JSON parser for the contract sidecar."""
from pathlib import Path
import re,sys
R=Path(__file__).resolve().parents[1];text=(R/'native/rf2.rf2').read_text();base=text[text.index('fn slen('):text.index('fn unsigned(')]
for name in sorted(re.findall(r'^fn (\w+)\(',base,re.M),key=len,reverse=True):base=re.sub(r'\b'+name+r'(?=\s*\()', 'j_'+name,base)
rpc=text[text.index('fn rpc_start('):text.index('fn tool_error(')]
for name in ['rpc_start','rpc_error','token','say','output','decimal']:rpc=re.sub(r'\b'+name+r'(?=\s*\()', 'j_'+name,rpc)
line=text[text.index('fn line()'):text.index('fn rpc_start(')]
for name in ['line','state','fail','say','output']:line=re.sub(r'\b'+name+r'(?=\s*\()', 'j_'+name,line)
result='module transport\n# Derived from native/rf2.rf2 by tools/sync-contract-json.py.\n'+base+rpc+line
p=R/'examples/evidence-contract/lib/json_transport.rf2'
if '--check'in sys.argv:
 assert p.read_text()==result,'Contract transport source is stale; run sync-contract-json.py'
else:p.write_text(result)
