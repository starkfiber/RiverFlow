"""Developer-only function-change evidence. Does not load or reuse machine code."""
from pathlib import Path
import re,json,sys
IDENT=re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z');HEX=re.compile(r'[a-f0-9]{64}\Z')
def read_map(path):
 raw=Path(path).read_bytes();assert len(raw)<=4194304,'map size bound';lines=raw.decode('ascii').splitlines();assert lines[0]=='RF2_FUNCTION_MAP_V1' and lines[-1]=='END','incomplete or unsupported map';header=lines[1].split();assert len(header)==3 and header[0]in('0','1')and header[1]in('0','1')and HEX.fullmatch(header[2]),'invalid context';functions={};current=None;end=0
 for line in lines[2:-1]:
  fields=line.split();assert fields,'empty record'
  if fields[0]=='F':
   assert len(fields)==5 and IDENT.fullmatch(fields[1])and HEX.fullmatch(fields[4]),'invalid function';name=fields[1];start,size=map(int,fields[2:4]);assert name not in functions and 0<=end<=start and start%4==size%4==0 and 0<size<=1048576 and start+size<=1048576,'function range';end=start+size;current={'offset':start,'size':size,'tokens':fields[4],'calls':set(),'relocations':[]};functions[name]=current;assert len(functions)<=256
  elif fields[0]=='C':
   assert current is not None and len(fields)==2 and IDENT.fullmatch(fields[1]),'invalid call';current['calls'].add(fields[1])
  elif fields[0]=='R':
   assert current is not None and len(fields)==4,'invalid relocation';offset,kind,target=map(int,fields[1:]);assert offset%4==0 and 0<=offset<current['size'] and 1<=kind<=3 and 0<=target<65536,'relocation bounds';current['relocations'].append((offset,kind,target))
  else:raise ValueError('unknown map record')
 assert 'main'in functions,'missing entry';assert all(c in functions for f in functions.values()for c in f['calls']),'unknown direct callee';return header,functions

def compare(old,new):
 oh,a=read_map(old);nh,b=read_map(new);changed={x for x in a.keys()|b.keys()if x not in a or x not in b or a[x]['tokens']!=b[x]['tokens']};affected=set(changed)
 if oh!=nh:affected|=a.keys()|b.keys()
 else:
  while True:
   next_set=affected|{name for collection in (a,b)for name,f in collection.items()if f['calls']&affected}
   if next_set==affected:break
   affected=next_set
 return {'schema':'rf2.function.change.evidence.v1','changedFunctions':sorted(changed),'requiresRevalidation':sorted(affected),'unchangedCandidates':sorted(b.keys()-affected),'globalContextChanged':oh!=nh,'machineCodeReused':False,'limits':'Diagnostic change propagation only. No object/semantic cache admission. Positional relocation targets are not stable linker identities; complete object/type/ABI replay remains required. Compiler identity must be retained separately.'}
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('Usage: function-impact.py old.functions new.functions')
 print(json.dumps(compare(sys.argv[1],sys.argv[2]),indent=2))
