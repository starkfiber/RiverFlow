"""Offline explicit binding controls. Does not negotiate PPPoE or access a NIC."""
from pathlib import Path
import subprocess,struct,random,json,hashlib,sys
ns={};s=Path('experiments/rf2net/frames_verify.py').read_text();exec(s[:s.index('for tag in')],ns);packet=ns['packet'];frame=ns['frame'];rng=random.Random(161111)
D=Path(sys.argv[1]);exe=D/'program';base=frame(packet(),500,True);binding=base[:12]+struct.pack('!H',7);cases=[]
def add(name,b,c=binding,allow=False):cases.append((name,c+b,0,b'ALLOW\n' if allow else b'DROP\n'))
add('matching',base,allow=True)
for i in range(12):
 b=bytearray(base);b[i]^=1;add('mac-mismatch-'+str(i),bytes(b))
 c=bytearray(binding);c[i]^=1;add('explicit-rebinding-'+str(i),bytes(b),bytes(c),True)
for sid in [0,1,7,8,65534,65535]+[rng.randrange(1,65535) for _ in range(40)]:
 b=bytearray(base);b[20:22]=struct.pack('!H',sid);c=base[:12]+struct.pack('!H',sid);add('session-match-'+str(sid),bytes(b),c,sid not in [0,65535]);add('stale-session-'+str(sid),base,c,sid==7)
for n in range(60):add('truncated-'+str(n),base[:n],allow=n==54)
for tag in [None,0,499,500,501,500|0xa000]:
 for ppp in [False,True]:add('encapsulation-'+str(tag)+'-'+str(ppp),frame(packet(),tag,ppp),allow=tag is not None and tag&4095==500 and ppp)
for n in range(130):add('payload-'+str(n),frame(packet(bytes((j*17)%256 for j in range(n))),500,True),allow=True)
for n in range(80):add('random-'+str(n),rng.randbytes(rng.randrange(0,150)))
for n in range(14):cases.append(('truncated-config-'+str(n),binding[:n],2,b''))
add('frame-cap2048',bytes(2048));add('wrong-IP-checksum',base[:36]+bytes([base[36]^1])+base[37:])
rows=[]
for name,data,code,out in cases:
 p=subprocess.run([str(exe.resolve())],input=data,capture_output=True,timeout=5);assert (p.returncode,p.stdout)==(code,out),(name,p.returncode,p.stdout,code,out)
 rows.append(dict(name=name,inputSHA256=hashlib.sha256(data).hexdigest(),exit=p.returncode,output=p.stdout.decode()))
# General parser accepts the changed-MAC frame, binding refuses it: concrete narrowed policy.
b=bytearray(base);b[6]^=1;old=Path('artifacts/rf2decision-vector/regression/opt/net/program').resolve();p=subprocess.run([str(old)],input=b,capture_output=True,timeout=5);assert p.returncode==0 and p.stdout==b'ALLOW\n'
r=dict(passed=True,count=len(rows),results=rows,generalParserCounterexample='old frame classifier allows changed source MAC; explicit bound adapter refuses unless configuration changes too',scope='static configured-byte MAC/session check for VLAN500 PPPoE frames; no authentication, replay protection, discovery, connection state, NAT or forwarding',binarySHA256=hashlib.sha256(exe.read_bytes()).hexdigest(),sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('experiments/rf2net/binding.flow'),Path('experiments/rf2net/bound_main.flow'),Path('experiments/rf2net/packet.flow'),Path(__file__)]})
(D/'BINDING-RESULTS.json').write_text(json.dumps(r,indent=2)+'\n');print(len(rows),'binding controls passed')
