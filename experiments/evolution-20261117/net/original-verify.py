"""Native RF2 DHCP payload/state acceptance against a separate dictionary oracle.
No sockets, guest or production network. Generated traffic is lab input, not real leases.
"""
from pathlib import Path
import subprocess,struct,json,hashlib,random,threading,sys
V=Path('experiments/rf2net/dhcp');D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('artifacts/rf2net-dhcp-final');D.mkdir(exist_ok=False)
COMPILER=Path('artifacts/rf2decision-sustained/compiler-opt').resolve();SERVER=0x0a4d0002;BASE=0x0a4d0064
cases=[]
def packet(client=1,kind=1,xid=1,requested=None,server=None,ci=0,extra=b'',flags=0):
 p=bytearray(240);p[:4]=bytes([1,1,6,0]);p[4:8]=struct.pack('!I',xid);p[10:12]=struct.pack('!H',flags);p[12:16]=struct.pack('!I',ci);p[28:34]=(0x020000000000+client).to_bytes(6,'big');p[236:240]=bytes.fromhex('63825363')
 p+=bytes([53,1,kind])
 if requested is not None:p+=bytes([50,4])+struct.pack('!I',requested)
 if server is not None:p+=bytes([54,4])+struct.pack('!I',server)
 p+=extra+b'\xff';return bytes(p).ljust(300,b'\0')
def add(name,t,b):cases.append((name,t,b))
# The independent oracle deliberately uses dict entries keyed by address instead of arrays.
class Oracle:
 def __init__(self):self.leases={};self.clock=None
 def parse(self,b):
  if not 241<=len(b)<=576 or b[:4]!=b'\1\1\6\0' or int.from_bytes(b[10:12],'big') not in [0,32768] or any(b[24:28]) or b[236:240]!=bytes.fromhex('63825363'):return 10,None
  mac=int.from_bytes(b[28:34],'big')
  if not mac or b[28]&1:return 10,None
  o={};i=240;end=False
  while i<len(b):
   code=b[i];i+=1
   if end:
    if code:return 10,None
    continue
   if code==0:continue
   if code==255:end=True;continue
   if i==len(b):return 10,None
   n=b[i];i+=1
   if n==0 or i+n>len(b) or code==52:return 10,None
   value=b[i:i+n];i+=n
   if code in [53,50,54,61]:
    if code in o:return 10,None
    if code==53 and n!=1:return 10,None
    if code in [50,54] and (n!=4 or int.from_bytes(value,'big')==0):return 10,None
    if code==61 and value!=b'\1'+b[28:34]:return 10,None
    o[code]=value
  if not end or 53 not in o:return 10,None
  typ=o[53][0];req=int.from_bytes(o.get(50,b'\0'),'big');srv=int.from_bytes(o.get(54,b'\0'),'big');ci=int.from_bytes(b[12:16],'big')
  if typ==1 and (srv or ci):return 10,None
  if typ==3 and ((ci and (req or srv)) or (not ci and not req)):return 10,None
  if typ==4 and (not req or not srv or ci):return 10,None
  if typ==7 and (not ci or not srv or req):return 10,None
  if typ not in [1,3,4,7]:return 11,None
  return 0,(mac,typ,req,srv,ci,int.from_bytes(b[4:8],'big'),int.from_bytes(b[10:12],'big'),61 in o)
 def run(self,t,b):
  code,m=self.parse(b);ip=0
  if code:return code,b'',self.snapshot()
  mac,typ,req,srv,ci,xid,flags,cid=m
  if self.clock is not None and t<self.clock:return 13,b'',self.snapshot()
  if srv and srv!=SERVER:return 0,b'',self.snapshot()
  self.clock=t;self.leases={ip:row for ip,row in self.leases.items() if row[2]>t}
  own=next((ip for ip,row in self.leases.items() if row[1]==mac and row[0]!=3),None)
  if typ==1:
   ip=own if own is not None else next((i for i in range(BASE,BASE+5) if i not in self.leases),None)
   if ip is None:code=12
   else:
    if self.leases.get(ip,(0,))[0]!=2:self.leases[ip]=(1,mac,t+60,xid)
    code=2
  elif typ==3:
   ip=req or ci
   if own!=ip or (self.leases[ip][0]==1 and (not srv or self.leases[ip][3]!=xid)):code=6
   else:self.leases[ip]=(2,mac,t+600,xid);code=5
  elif typ==7:
   if own==ci and self.leases[own][0]==2:del self.leases[own]
   code=0
  elif typ==4:
   if own==req:self.leases[own]=(3,0,t+600,0)
   code=0
  return code,self.reply(b,code,ip or 0,cid) if code in [2,5,6] else b'',self.snapshot()
 def snapshot(self):
  return b''.join(struct.pack('<4Q',*self.leases.get(i,(0,0,0,0))) for i in range(BASE,BASE+5))+struct.pack('<2Q',self.clock or 0,int(self.clock is not None))
 def reply(self,b,code,ip,cid):
  p=bytearray(240);p[:3]=b'\2\1\6';p[4:8]=b[4:8];p[10:12]=b'\x80\0' if code==6 else b[10:12];p[12:16]=bytes(4) if code==6 else b[12:16];p[16:20]=struct.pack('!I',0 if code==6 else ip);p[28:34]=b[28:34];p[236:240]=bytes.fromhex('63825363')
  p+=bytes([53,1,code,54,4])+struct.pack('!I',SERVER)
  if code!=6:p+=bytes([51,4])+struct.pack('!I',600)+bytes([1,4,255,255,255,0,3,4])+struct.pack('!I',SERVER)
  if cid:p+=b'\x3d\7\1'+b[28:34]
  return bytes(p+b'\xff').ljust(300,b'\0')
for c in range(1,6):add('discover-five-'+str(c),0,packet(c,xid=100+c))
add('sixth-client-poolfull',1,packet(6));add('duplicate-discover-same-offer',1,packet(1,xid=101))
for c in range(1,6):add('select-ACK-'+str(c),2,packet(c,3,xid=100+c,requested=BASE+c-1,server=SERVER))
add('renew-owned',10,packet(1,3,xid=901,ci=BASE));add('steal-bound-IP',11,packet(6,3,requested=BASE,server=SERVER));add('INIT-reboot-owned',12,packet(2,3,requested=BASE+1));add('select-other-server-ignore',13,packet(2,3,requested=BASE+1,server=SERVER+1));add('release-wrong-owner',14,packet(6,7,ci=BASE,server=SERVER));add('release-owned',15,packet(1,7,ci=BASE,server=SERVER));add('reuse-released',16,packet(6,xid=6));add('offer-xid-mismatch',17,packet(6,3,xid=7,requested=BASE,server=SERVER));add('offer-xid-match',18,packet(6,3,xid=6,requested=BASE,server=SERVER));add('decline-owned',19,packet(6,4,requested=BASE,server=SERVER));add('quarantine-no-reuse',20,packet(7));add('clock-reversal-preserves',19,packet(2));add('quarantine-exact-expiry',619,packet(7));add('INIT-no-owned-lease-NAK',620,packet(8,3,requested=BASE+4));add('request-offer-without-server-NAK',620,packet(7,3,requested=BASE));add('release-offer-no-effect',620,packet(7,7,ci=BASE,server=SERVER));add('valid-long-elapsed-seconds',620,packet(7)[:8]+b'\xff\xff'+packet(7)[10:])
# Every invalid payload boundary must preserve all lease state, including clock.
base=packet()
for n in [0,1,13,28,235,239,240,241,242,243,244,245,249,250,299,300,575,576]:add('payload-length-'+str(n),621,base[:n] if n<=300 else base+bytes(n-300))
for at,val in [(0,2),(1,2),(2,0),(2,16),(3,1),(10,1),(11,1),(24,1),(236,0),(28,1)]:
 b=bytearray(base);b[at]=val;add('header-corrupt-'+str(at)+'-'+str(val),622,bytes(b))
for label,opt in [('duplicateType',b'\x35\1\1'),('shortIP',b'\x32\3abc'),('zeroIP',b'\x32\4'+bytes(4)),('duplicateIP',b'\x32\4abcd\x32\4abcd'),('zeroServer',b'\x36\4'+bytes(4)),('shortCID',b'\x3d\1\1'),('wrongCID',b'\x3d\7\1'+bytes(6)),('overload',b'\x34\1\1'),('oversizeOption',b'\x37\xffx')]:add(label,623,packet(extra=opt))
add('matchingCID',623,packet(7,extra=b'\x3d\7\1'+(0x020000000007).to_bytes(6,'big')));add('unknown-bounded-option',623,packet(7,extra=b'\xe0\3abc'))
for kind in [0,2,5,6,8,255]:add('unsupported-kind-'+str(kind),624,packet(7,kind))
add('missing-END',624,base[:243]+bytes(57));add('nonzero-after-END',624,base[:-1]+b'\1');add('maximum-clock',0xffffffff,packet(7));add('wrapped-clock-denied',0,packet(7))
# Fresh process corpus interleaves identities, good and malformed requests, logical expiry.
rng=random.Random(171126);random_cases=[]
for i in range(1500):
 c=rng.randint(1,9);kind=rng.choice([1,3,4,7]);t=i*7;ip=BASE+rng.randrange(7);xid=rng.randrange(100)
 b=packet(c,kind,xid=xid,requested=ip if kind in [3,4] else None,server=SERVER if kind in [3,4,7] else None,ci=ip if kind==7 else 0)
 if i%17==0:b=b[:-1]+b'\1'
 random_cases.append(('seeded-'+str(i),t,b))
for i in range(500):
 b=bytearray(packet(client=1+i%9));at=rng.randrange(len(b));b[at]^=rng.randrange(1,256)
 random_cases.append(('mutated-payload-'+str(i),11000+i,bytes(b)))
def expected(rows):
 o=Oracle();out=b'';records=[]
 for name,t,b in rows:
  before=o.snapshot();code,reply,snap=o.run(t,b)
  if code in [10,11,13]:assert before==snap
  states=[struct.unpack_from('<4Q',snap,i*32) for i in range(5)]
  owners=[x[1] for x in states if x[0] in [1,2]];assert len(owners)==len(set(owners))
  out+=struct.pack('<HH',code,len(reply))+reply+snap;records.append({'name':name,'code':code,'stateSHA256':hashlib.sha256(snap).hexdigest()})
 return out,records
def packed(rows):return b''.join(struct.pack('<HI',len(b),t)+b for _,t,b in rows)
results=[]
for mode in ['plain','opt']:
 exe=D/('dhcp-'+mode);args=[str(COMPILER),str(V/'main.flow'),str(exe),'--compact']+(['--opt'] if mode=='opt' else [])
 x=subprocess.run(args,capture_output=True,text=True,timeout=40);assert x.returncode==0,x.stdout+x.stderr
 subprocess.run(['codesign','-s','-',str(exe)],check=True,capture_output=True)
 for label,corpus in [('explicit',cases),('seeded',random_cases)]:
  want,decisions=expected(corpus);(D/(label+'-input.bin')).write_bytes(packed(corpus));x=subprocess.run([str(exe.resolve())],input=packed(corpus),capture_output=True,timeout=20)
  (D/(mode+'-'+label+'-actual.bin')).write_bytes(x.stdout);(D/(label+'-expected.bin')).write_bytes(want)
  if x.returncode!=0 or x.stdout!=want:
   at=0
   for name,t,b in corpus:
    a=struct.unpack_from('<HH',want,at);step=4+a[1]+176
    if x.stdout[at:at+step]!=want[at:at+step]:print('FIRST MISMATCH',mode,label,name,'expected',a,'actual',x.stdout[at:at+4].hex(),'offset',at);break
    at+=step
   raise AssertionError((mode,label,x.returncode,len(x.stdout),len(want)))
  (D/(label+'-decisions.json')).write_text(json.dumps(decisions,indent=2)+'\n')
 # All strict prefixes of one record are rejected without output.
 raw=packed(cases[:1]);stream=0
 for n in range(1,len(raw)):
  x=subprocess.run([str(exe.resolve())],input=raw[:n],capture_output=True,timeout=5);assert x.returncode==2 and not x.stdout,(mode,n,x.returncode);stream+=1
 for blob in [struct.pack('<HI',577,0),struct.pack('<HI',65535,0)]:
  x=subprocess.run([str(exe.resolve())],input=blob,capture_output=True,timeout=5);assert x.returncode==2 and not x.stdout;stream+=1
 x=subprocess.run([str(exe.resolve())],input=b'',capture_output=True,timeout=5);assert x.returncode==0 and not x.stdout;stream+=1
 # Refuse delivery to a closed output; report EPIPE rather than claim success.
 p=subprocess.Popen([str(exe.resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);p.stdout.close();p.communicate(raw,timeout=5);assert p.returncode==3;stream+=1
 # Fragmented live pipe must produce each result before EOF, without short-read loss.
 unit=cases[:12];unit_blob=packed(unit);unit_want,_=expected(unit)
 p=subprocess.Popen([str(exe.resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);received=[]
 worker=threading.Thread(target=lambda:received.append(p.stdout.read(len(unit_want))),daemon=True);worker.start()
 for pos in range(0,len(unit_blob),7):p.stdin.write(unit_blob[pos:pos+7]);p.stdin.flush()
 worker.join(5);assert not worker.is_alive() and received==[unit_want]
 p.stdin.close();p.wait(timeout=5);assert p.returncode==0;stream+=1
 cap=cases[:1]*4096;cap_want,_=expected(cap)
 x=subprocess.run([str(exe.resolve())],input=packed(cap),capture_output=True,timeout=20);assert x.returncode==0 and x.stdout==cap_want;stream+=1
 x=subprocess.run([str(exe.resolve())],input=packed(cap)+raw,capture_output=True,timeout=20);assert x.returncode==2 and x.stdout==cap_want;stream+=1
 results.append({'mode':mode,'passed':True,'payloadStateCases':len(cases)+len(random_cases),'streamControls':stream,'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest()});print(mode,results[-1],flush=True)
(D/'RESULTS.json').write_text(json.dumps({'passed':True,'results':results,'scope':'Native Mac ARM64 RF2 BOOTP payload codec and bounded in-memory lease engine only. No UDP socket, VM102, DHCP client, failover, network throughput or physical hardware qualification.','compilerSHA256':hashlib.sha256(COMPILER.read_bytes()).hexdigest(),'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in V.glob('*') if p.is_file()}},indent=2)+'\n')
