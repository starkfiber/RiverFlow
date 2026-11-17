"""Five real UDP sockets, generated BOOTP payloads, native RF2 loopback server.
Not operating-system DHCP clients: no interface leasing, broadcast, guest or WAN.
"""
from pathlib import Path
import subprocess,socket,struct,json,hashlib,select,random,sys
V=Path('experiments/rf2net/dhcp');D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('artifacts/rf2net-dhcp-socket-final');D.mkdir(exist_ok=False);C=Path('artifacts/rf2decision-sustained/compiler-opt').resolve();SERVER=0x0a4d0002;BASE=0x0a4d0064

def req(c,typ=1,xid=1,ip=None,srv=None,ci=0):
 b=bytearray(240);b[:3]=b'\1\1\6';b[4:8]=struct.pack('!I',xid);b[12:16]=struct.pack('!I',ci);b[28:34]=(0x020000000000+c).to_bytes(6,'big');b[236:240]=bytes.fromhex('63825363');b+=bytes([53,1,typ])
 if ip is not None:b+=bytes([50,4])+struct.pack('!I',ip)
 if srv is not None:b+=bytes([54,4])+struct.pack('!I',srv)
 return bytes(b+b'\xff').ljust(300,b'\0')
def check(b,c,typ,xid,ip):
 assert len(b)==300 and b[:3]==b'\2\1\6' and int.from_bytes(b[4:8],'big')==xid
 assert b[28:34]==(0x020000000000+c).to_bytes(6,'big') and int.from_bytes(b[16:20],'big')==ip
 assert b[20:24]==bytes(4),'must not advertise an unconfigured boot server'
 o={};i=240
 while b[i]!=255:
  k,n=b[i:i+2];assert k not in o;o[k]=b[i+2:i+2+n];i+=2+n
 assert o[53]==bytes([typ]) and o[54]==struct.pack('!I',SERVER)
 assert 6 not in o,'must not advertise DNS until resolver is configured'
 if typ in [2,5]:assert o[51]==struct.pack('!I',600)

results=[]
for mode in ['plain','opt']:
 exe=D/('udp-server-'+mode);x=subprocess.run([str(C),str(V/'loopback.flow'),str(exe),'--compact']+(['--opt'] if mode=='opt' else []),capture_output=True,text=True,timeout=40);assert x.returncode==0,x.stdout+x.stderr
 subprocess.run(['codesign','-s','-',str(exe)],check=True,capture_output=True)
 p=subprocess.Popen([str(exe.resolve())],stdout=subprocess.PIPE,stderr=subprocess.PIPE);clients=[];count=0;port=None
 try:
  assert select.select([p.stdout],[],[],5)[0];raw=p.stdout.read(2);assert len(raw)==2,(p.poll(),p.stderr.read());port=int.from_bytes(raw,'big');assert port>1023
  for _ in range(6):
   s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',0));s.settimeout(1);clients.append(s)
  def send(c,b):
   global count
   clients[c-1].sendto(b,('127.0.0.1',port));count+=1
  def receive(c,kind,xid,ip):
   b,peer=clients[c-1].recvfrom(1000);assert peer==('127.0.0.1',port);check(b,c,kind,xid,ip)
  # All five requests are sent before collecting replies: real overlapping socket clients.
  for c in range(1,6):send(c,req(c,xid=100+c))
  for c in range(1,6):receive(c,2,100+c,BASE+c-1)
  for c in range(1,6):send(c,req(c,3,xid=100+c,ip=BASE+c-1,srv=SERVER))
  for c in range(1,6):receive(c,5,100+c,BASE+c-1)
  # An unknown owner cannot claim another client's address.
  send(6,req(6,3,xid=99,ip=BASE,srv=SERVER));receive(6,6,99,0)
  for c in range(1,6):send(c,req(c,3,xid=200+c,ci=BASE+c-1))
  for c in range(1,6):receive(c,5,200+c,BASE+c-1)
  def silent(c,b):
   send(c,b);clients[c-1].settimeout(.06)
   try:clients[c-1].recvfrom(1000);raise AssertionError('unexpected UDP response')
   except socket.timeout:pass
   finally:clients[c-1].settimeout(1)
  silent(6,req(6)) # pool exhaustion
  silent(1,req(1,7,ci=BASE,srv=SERVER))
  send(6,req(6,xid=306));receive(6,2,306,BASE)
  send(6,req(6,3,xid=306,ip=BASE,srv=SERVER));receive(6,5,306,BASE)
  # Eleven invalid datagrams, including truncation and receive-buffer overflow.
  bad=[b'',b'x',req(2)[:239],req(2)[:241],req(2)+bytes(277),req(2)+bytes(800)]
  for at,value in [(0,2),(2,0),(3,1),(10,1),(236,0)]:
   b=bytearray(req(2));b[at]=value;bad.append(bytes(b))
  for b in bad:silent(2,b)
  send(5,req(5,3,xid=405,ci=BASE+4));receive(5,5,405,BASE+4)
  assert count==32,count;p.wait(timeout=5);assert p.returncode==0 and not p.stderr.read()
  # Rebind without SO_REUSEADDR proves the listening descriptor is released.
  release=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);release.bind(('127.0.0.1',port));release.close()
  # An idle new server fails boundedly and closes its descriptor.
  idle=subprocess.Popen([str(exe.resolve())],stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert len(idle.stdout.read(2))==2;idle.wait(timeout=5);assert idle.returncode==4
  results.append({'mode':mode,'passed':True,'datagrams':count,'clientSockets':6,'ordinaryClients':5,'generatedLeasesBound':5,'invalidDatagrams':len(bad),'idleTimeoutExit':4,'normalExit':0,'socketRebindPassed':True,'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest()});print(mode,'32 actual UDP datagrams; five ordinary client sockets and one negative-control client passed',flush=True)
 finally:
  for s in clients:s.close()
  if p.poll() is None:p.terminate();p.wait(timeout=5)
# Verify the bounded time conversion divider against host integer arithmetic.
(D/'clock.flow').write_bytes((V/'clock.flow').read_bytes())
probe=D/'division.flow';probe.write_text('profile RF2_SYSTEM_A64_V1\nuse "clock.flow"\nfn main(argc,argv)\n let p=buffer("v",16)\n let i=0\n while i<1024\n  if read(0,p,16)!=16\n   return 2\n  end\n  let q=dhcp_div(load64(p),load64(p+8))\n  do store64(p,q)\n  if write(1,p,8)!=8\n   return 3\n  end\n  set i=i+1\n end\n return 0\nend\n')
rng=random.Random(171117);vals=[(rng.randrange(2**64),rng.randrange(1,2**32)) for _ in range(1024)];vals[:8]=[(0,1),(2**64-1,1),(2**64-1,2**32-1),(2**64-1,1000000000),(1,2),(2**32,1),(2**63,3),(2**64-1,3)]
for mode in ['plain','opt']:
 exe=D/('division-'+mode);x=subprocess.run([str(C),str(probe),str(exe),'--compact']+(['--opt'] if mode=='opt' else []),capture_output=True,text=True,timeout=40);assert x.returncode==0,x.stdout+x.stderr;subprocess.run(['codesign','-s','-',str(exe)],check=True,capture_output=True)
 x=subprocess.run([str(exe.resolve())],input=b''.join(struct.pack('<QQ',*v) for v in vals),capture_output=True,timeout=10);assert x.returncode==0 and x.stdout==b''.join(struct.pack('<Q',a//b) for a,b in vals)
# Exercise timebase conversion, invalid ratios and intermediate-overflow refusal.
clockprobe=D/'seconds.flow'
clockprobe.write_text('profile RF2_SYSTEM_A64_V1\nuse "clock.flow"\nfn main(argc,argv)\n let p=buffer("v",24)\n let i=0\n while i<1024\n  let at=0\n  while at<24\n   let n=read(0,p+at,24-at)\n   if any(n==0,n>>63)\n    return 2\n   end\n   set at=at+n\n  end\n  let answer=dhcp_seconds(load64(p),load64(p+8),load64(p+16))\n  do store64(p,answer)\n  if write(1,p,8)!=8\n   return 3\n  end\n  set i=i+1\n end\n return 0\nend\n')
timevals=[(rng.randrange(2**64),rng.randrange(1,2**32),rng.randrange(1,2**32)) for _ in range(1024)]
timevals[:8]=[(1,0,1),(1,1,0),(1,2**32,1),(1,1,2**32),(2**64-1,1,1),(2**64-1,2,1),(2**64-1,2**32-1,2**32-1),(3,1000000001,2)]
want=[]
for delta,numer,denom in timevals:
 if not 0<numer<2**32 or not 0<denom<2**32:answer=2**64-1
 else:
  ns=delta*numer//denom;answer=ns//1000000000 if ns<2**64 else 2**64-1
 want.append(answer)
for mode in ['plain','opt']:
 exe=D/('seconds-'+mode);x=subprocess.run([str(C),str(clockprobe),str(exe),'--compact']+(['--opt'] if mode=='opt' else []),capture_output=True,text=True,timeout=40);assert x.returncode==0,x.stdout+x.stderr;subprocess.run(['codesign','-s','-',str(exe)],check=True,capture_output=True)
 x=subprocess.run([str(exe.resolve())],input=b''.join(struct.pack('<QQQ',*v) for v in timevals),capture_output=True,timeout=10);assert x.returncode==0 and x.stdout==b''.join(struct.pack('<Q',a) for a in want)
(D/'SOCKET-RESULTS.json').write_text(json.dumps({'passed':True,'results':results,'dividerCasesPerMode':1024,'timeConversionCasesPerMode':1024,'scope':'Actual Darwin loopback UDP only with generated BOOTP payloads, not OS DHCP clients, NIC broadcast, VM102 or production DHCP/HA','sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in V.glob('*') if p.is_file()}},indent=2)+'\n')
