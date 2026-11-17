"""Local frame fixtures. No sockets, capture or network writes."""
import sys,subprocess,struct,json,hashlib,random
from pathlib import Path
# Load packet construction definitions only; do not rerun/overwrite old receipts.
s=Path('experiments/rf2net/verify.py').read_text();ns={};exec(s[:s.index('cases=')],ns);packet=ns['packet']
exe=Path(sys.argv[1]) if len(sys.argv)>1 else Path('artifacts/rf2net-frames/program');cases=[]
def frame(ip,tag=None,ppp=False,pad=True):
 h=b'\x02\x00\x00\x00\x00\x01'+b'\x02\x00\x00\x00\x00\x02';kind=0x8864 if ppp else 0x0800
 h+=struct.pack('!HHH',0x8100,tag,kind) if tag is not None else struct.pack('!H',kind)
 if ppp:h+=struct.pack('!BBHHH',0x11,0,7,len(ip)+2,0x21)
 b=h+ip;return b.ljust(60,b'\0') if pad else b
for tag in [None,500,500|0xa000]:
 for ppp in [False,True]:
  for n in [0,1,17,18,19,100,1464]:
   b=frame(packet(b'x'*n),tag,ppp);cases.append((f'valid {tag} {ppp} {n}',b,True))
  b=frame(packet(),tag,ppp)
  for n in range(42 if not ppp else 50):cases.append((f'truncated {tag} {ppp} {n}',b[:n],False))
  cases.append(('excess padding',b+b'\0',False))
for tag in [0,1,499,501,4095]:cases.append(('wrong VLAN',frame(packet(),tag,True),False))
base=frame(packet(),500,True)
for off,val in [(18,0x12),(19,9),(20,0),(22,0),(23,1),(24,0),(25,0x57)]:
 b=bytearray(base);b[off]=val
 if bytes(b)!=base:cases.append((f'bad PPP {off}',bytes(b),False))
for sid in [0,65535]:
 b=bytearray(base);b[20:22]=struct.pack('!H',sid);cases.append(('reserved session',bytes(b),False))
rng=random.Random(500)
for n in range(200):cases.append(('random short',rng.randbytes(rng.randrange(0,28)),False))
results=[]
for name,b,allow in cases:
 q=subprocess.run([str(exe.resolve())],input=b,capture_output=True,timeout=3);ok=q.returncode==0 and q.stdout==(b'ALLOW\n' if allow else b'DROP\n');results.append(dict(name=name,passed=ok,exit=q.returncode,inputSHA256=hashlib.sha256(b).hexdigest(),output=q.stdout.decode()))
r=dict(count=len(results),allPassed=all(x['passed'] for x in results),sourceSHA256=hashlib.sha256(Path('experiments/rf2net/ethernet.flow').read_bytes()).hexdigest(),binarySHA256=hashlib.sha256(exe.read_bytes()).hexdigest(),scope='Offline single Ethernet frame without FCS, optional one VLAN500 and PPPoE session encapsulation; fixed lab policy',results=results)
(exe.parent/'RESULTS.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='results'}));assert r['allPassed'],[x for x in results if not x['passed']]
