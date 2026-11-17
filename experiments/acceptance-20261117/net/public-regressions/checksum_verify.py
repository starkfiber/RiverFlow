"""Independent UDP pseudoheader checksum fixtures; offline native execution."""
import json,struct,subprocess,hashlib,sys
from pathlib import Path
ns={};s=Path('experiments/rf2net/frames_verify.py').read_text();exec(s[:s.index('for tag in')],ns);packet=ns['packet'];frame=ns['frame']
def seal(b):
 b=bytearray(b);pseudo=b[12:20]+bytes([0,17])+struct.pack('!H',len(b)-20);data=pseudo+b[20:];data+=b'\0'*(len(data)%2);total=sum(struct.unpack('!%dH'%(len(data)//2),data))
 while total>>16:total=(total&65535)+(total>>16)
 b[26:28]=struct.pack('!H',(~total&65535) or 65535);return bytes(b)
exe=Path(sys.argv[1]);rows=[]
for n in range(129):
 ip=seal(packet(bytes((i*17)%256 for i in range(n))))
 for tag,ppp in [(None,False),(500,False),(500,True)]:
  for good in [True,False]:
   b=bytearray(ip)
   if not good:b[21]^=1
   data=frame(bytes(b),tag,ppp);q=subprocess.run([str(exe.resolve())],input=data,capture_output=True,timeout=3);rows.append(dict(length=n,tag=tag,ppp=ppp,valid=good,passed=q.returncode==0 and q.stdout==(b'ALLOW\n' if good else b'DROP\n'),inputSHA256=hashlib.sha256(data).hexdigest()))
r=dict(count=len(rows),allPassed=all(x['passed'] for x in rows),binarySHA256=hashlib.sha256(exe.read_bytes()).hexdigest(),sources={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['experiments/rf2net/packet.flow','experiments/rf2net/ethernet.flow','experiments/rf2net/checksum_verify.py']},rows=rows);(exe.parent/'CHECKSUM-RESULTS.json').write_text(json.dumps(r,indent=2)+'\n');print(r['count'],r['allPassed']);assert r['allPassed']
