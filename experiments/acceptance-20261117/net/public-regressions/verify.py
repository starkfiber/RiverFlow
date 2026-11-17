"""Offline packet controls only. Does not open a network interface."""
import subprocess,struct,random,json,hashlib
from pathlib import Path
exe=Path('artifacts/rf2net-first-build/program')
def checksum(b):
 s=sum(struct.unpack('!10H',b));s=(s&65535)+(s>>16);s=(s&65535)+(s>>16);return 65535-s
def packet(payload=b'',proto=17,source=b'\x0a\x01\x02\x03',dest=b'\xc0\x00\x02\x35',port=53,flags=0,ttl=64):
 udp=struct.pack('!4H',12345,port,8+len(payload),0)+payload
 h=bytearray(struct.pack('!BBHHHBBH4s4s',69,0,20+len(udp),1,flags,ttl,proto,0,source,dest));h[10:12]=struct.pack('!H',checksum(h));return bytes(h)+udp
cases=[('allowed',packet(),True),('DF',packet(flags=16384),True),('fragment',packet(flags=8192),False),('offset',packet(flags=1),False),('reserved',packet(flags=32768),False),('TTL',packet(ttl=0),False),('TCP',packet(proto=6),False),('wrong port',packet(port=80),False),('source',packet(source=b'\x0b\x01\x02\x03'),False),('destination',packet(dest=b'\xc0\x00\x02\x36'),False)]
for n in range(28):cases.append(('truncated'+str(n),packet()[:n],False))
rng=random.Random(501)
for n in range(100):
 b=packet(rng.randbytes(n));cases.append(('payload'+str(n),b,True));bad=bytearray(b);bad[10]^=1;cases.append(('checksum'+str(n),bytes(bad),False))
cases.extend([('trailing',packet()+b'x',False),('oversize',packet(b'x'*2020),False),('options',bytes([70])+packet()[1:],False)])
results=[]
for name,b,allow in cases:
 q=subprocess.run([str(exe.resolve())],input=b,capture_output=True,timeout=3);passed=q.returncode==0 and q.stdout==(b'ALLOW\n' if allow else b'DROP\n');results.append(dict(name=name,passed=passed,inputSHA256=hashlib.sha256(b).hexdigest(),exit=q.returncode,output=q.stdout.decode()))
r=dict(scope='Offline supplied IPv4 datagrams, no interface or forwarding',count=len(results),allPassed=all(x['passed'] for x in results),executableSHA256=hashlib.sha256(exe.read_bytes()).hexdigest(),sourceSHA256=hashlib.sha256(Path('experiments/rf2net/main.flow').read_bytes()).hexdigest(),results=results)
Path('artifacts/rf2net-first-build/RESULTS.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='results'}));assert r['allPassed']
