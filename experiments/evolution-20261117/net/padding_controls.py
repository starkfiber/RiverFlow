"""Every post-END byte position at every admitted length, independently checked."""
from pathlib import Path
import struct,hashlib,subprocess,json
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[2]/'artifacts/evolution-20261117/net'
src=(HERE/'original-verify.py').read_text();ns=dict(struct=struct,hashlib=hashlib)
exec('SERVER=0x0a4d0002;BASE=0x0a4d0064\ncases=[]\n'+src[src.index('def packet('):src.index('for c in range(1,6):')],ns)
rows=[]
for n in range(244,577):
 b=ns['packet']()[:244].ljust(n,b'\0');rows.append((f'valid-{n}',n,b))
 for pos in range(244,n):
  p=bytearray(b);p[pos]=1+(pos%255);rows.append((f'bad-{n}-{pos}',n,bytes(p)))
checks=[]
for variant in ['baseline','candidate']:
 for mode in ['plain','opt']:
  exe=OUT/variant/'acceptance'/('dhcp-'+mode)
  for start in range(0,len(rows),4000):
   batch=rows[start:start+4000];o=ns['Oracle']();want=bytearray();blob=bytearray()
   for name,t,b in batch:
    code,reply,snap=o.run(t,b);want+=struct.pack('<HH',code,len(reply))+reply+snap;blob+=struct.pack('<HI',len(b),t)+b
   p=subprocess.run([str(exe)],input=bytes(blob),capture_output=True,timeout=20)
   assert p.returncode==0 and p.stdout==want,(variant,mode,start,p.returncode)
  checks.append(dict(variant=variant,mode=mode,cases=len(rows),passed=True))
(OUT/'PADDING-CONTROLS.json').write_text(json.dumps(dict(checks=checks,meaning='Every zero padding length244..576 and every individual nonzero padding byte; no mutation of network or production.'),indent=2)+'\n')
print(checks)
