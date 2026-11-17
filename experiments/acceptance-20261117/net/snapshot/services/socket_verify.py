"""Actual local UDP DHCP persistence/restart and DNS sockets; no VM or LAN exposure."""
from pathlib import Path
import subprocess,socket,select,struct,tempfile,json,hashlib,ast,sys
R=Path.cwd();D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('artifacts/rf2net-services-sockets');D.mkdir(exist_ok=False);C=Path('artifacts/rf2decision-sustained/compiler-opt').resolve();BASE=0x0a4d0064;SERVER=0x0a4d0002
# Reuse only pure independent oracle/fixture functions; do not import executing verifiers.
def definitions(path,names,env):
 for n in ast.parse(Path(path).read_text()).body:
  if isinstance(n,ast.FunctionDef) and n.name in names:exec(compile(ast.Module(body=[n],type_ignores=[]),str(path),'exec'),env)
env={'struct':struct,'MASK':2**64-1,'subprocess':subprocess}
definitions('experiments/rf2net/dhcp-durable/verify.py',['mac','pkt','records','checksum'],env)
dnsenv={'struct':struct};definitions('experiments/rf2net/dns/verify.py',['name','query','soa','oracle'],dnsenv)
results=[]
def build(src,exe,mode):
 x=subprocess.run([str(C),str(src),str(exe),'--compact']+(['--opt'] if mode=='opt' else []),capture_output=True,text=True,timeout=40);assert x.returncode==0,x.stdout+x.stderr;subprocess.run(['codesign','-s','-',str(exe)],capture_output=True,check=True)
def start(exe,args):
 p=subprocess.Popen([str(exe.resolve())]+args,stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert select.select([p.stdout],[],[],5)[0];h=p.stdout.read(2);assert len(h)==2,(p.poll(),p.stderr.read());port=int.from_bytes(h,'big');assert port>1023;return p,port
def end(p,port):
 p.wait(timeout=5);assert p.returncode==0 and not p.stderr.read();s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',port));s.close()
for mode in ['plain','opt']:
 dhcp=D/('dhcp-'+mode);dns=D/('dns-'+mode);build('experiments/rf2net/dhcp-durable/loopback.flow',dhcp,mode);build('experiments/rf2net/dns/loopback.flow',dns,mode)
 with tempfile.TemporaryDirectory(prefix='rf2services-') as tmp:
  db=Path(tmp)/'leases';res=(env['mac'](5),0,0,0,env['mac'](1));x=subprocess.run([str(dhcp.resolve()),'init',str(db)],input=struct.pack('<5Q',*res),capture_output=True,timeout=5);assert x.returncode==0,x.returncode
  bind={1:BASE+4,2:BASE+1,3:BASE+2,4:BASE+3,5:BASE}
  for phase in [0,1]:
   p,port=start(dhcp,['serve',str(db)]);sockets=[];count=0
   try:
    for _ in range(6):
     s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',0));s.settimeout(1);sockets.append(s)
    def send(c,b):
     global count
     sockets[c-1].sendto(b,('127.0.0.1',port));count+=1
    def receive(c,kind,xid,ip):
     b,peer=sockets[c-1].recvfrom(1000);assert peer==('127.0.0.1',port) and len(b)==300 and b[242]==kind and int.from_bytes(b[4:8],'big')==xid and int.from_bytes(b[16:20],'big')==ip
    for c in range(1,6):send(c,env['pkt'](c,xid=100+c))
    for c in range(1,6):receive(c,2,100+c,bind[c])
    for c in range(1,6):send(c,env['pkt'](c,3,xid=100+c,ip=bind[c],srv=SERVER))
    for c in range(1,6):receive(c,5,100+c,bind[c])
    for c in range(1,6):send(c,env['pkt'](c,3,xid=200+c,ci=bind[c]))
    for c in range(1,6):receive(c,5,200+c,bind[c])
    send(6,env['pkt'](6,3,xid=99,ip=BASE,srv=SERVER));receive(6,6,99,0)
    bad=[b'',b'x',env['pkt'](2)[:239],env['pkt'](2)[:241],env['pkt'](2)+bytes(277),env['pkt'](2)+bytes(800)]
    for at,val in [(0,2),(2,0),(3,1),(10,1),(236,0),(28,1)]:
     b=bytearray(env['pkt'](2));b[at]=val;bad.append(bytes(b))
    for b in bad+[env['pkt'](2,3,ip=bind[2],srv=SERVER+1)]:
     before=db.read_bytes();send(2,b);sockets[1].settimeout(.06)
     try:sockets[1].recvfrom(1000);raise AssertionError('bad request answered')
     except socket.timeout:pass
     finally:sockets[1].settimeout(1)
     assert db.read_bytes()==before,'invalid/other-server input must not change persistent state'
    for c in [1,2,5]:send(c,env['pkt'](c,3,xid=300+c,ci=bind[c]));receive(c,5,300+c,bind[c])
    assert count==32;end(p,port)
    state=env['records'](db)[-1];assert state['reserves']==res
    for c,ip in bind.items():assert state['slots'][ip-BASE][0]==2 and state['slots'][ip-BASE][1]==env['mac'](c)
    results.append({'mode':mode,'service':'durable-DHCP','phase':phase,'passed':True,'UDPdatagrams':32,'ordinaryClientSockets':5,'negativeClientSockets':1,'boundLeases':5,'reservationsSurvived':True,'journalGeneration':state['generation'],'clockBasis':'kernel UTC seconds, checked against persisted clock; not authenticated NTP','socketCleanup':True})
   finally:
    for s in sockets:s.close()
    if p.poll() is None:p.kill();p.wait(timeout=5)
  # New DNS process, same client-count, independent request/response oracle.
  p,port=start(dns,[]);sockets=[]
  try:
   for _ in range(5):
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',0));s.settimeout(.08);sockets.append(s)
   qs=[]
   for s in ['gateway.rf2.test','health.rf2.test','rf2.test','missing.rf2.test','blocked.rf2.test','example.test']:
    for typ in [1,28,6,2]:qs.append(dnsenv['query'](s,typ,edns=512))
   qs += [dnsenv['query']('GATEWAY.RF2.TEST'),dnsenv['query'](edns=4096,version=1),b'',b'x',dnsenv['query'](flags=0x8000),dnsenv['query']()[:12],bytes(513),dnsenv['query'](edns=512,opt=b'\0')]
   assert len(qs)==32
   # Batch sends overlap across five real client sockets; correlate expected order per socket.
   for i,b in enumerate(qs):sockets[i%5].sendto(b,('127.0.0.1',port))
   for i,b in enumerate(qs):
    want=dnsenv['oracle'](b)
    if want:
     actual,peer=sockets[i%5].recvfrom(1000);assert actual==want and peer==('127.0.0.1',port),(i,b.hex(),actual.hex(),want.hex())
   end(p,port)
   for s in sockets:
    try:s.recvfrom(1000);raise AssertionError('unexpected response to dropped query')
    except socket.timeout:pass
   results.append({'mode':mode,'service':'local-zone-DNS','passed':True,'UDPdatagrams':32,'clientSockets':5,'scope':'Local authoritative zone, positive/negative/refused and EDNS0/BADVERS; no forwarding or recursive resolver','socketCleanup':True})
  finally:
   for s in sockets:s.close()
   if p.poll() is None:p.kill();p.wait(timeout=5)
 print(mode,'durable DHCP32+32 after restart and DNS32 real loopback datagrams passed',flush=True)
(D/'RESULTS.json').write_text(json.dumps({'passed':True,'results':results,'scope':'Actual Mac loopback sockets and native file persistence; generated BOOTP/DNS clients, not OS DHCP clients or guest VM102 integration','sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for v in ['dhcp-durable','dns','services'] for p in (Path('experiments/rf2net')/v).glob('*') if p.is_file() and p.suffix in ['.flow','.py']},'binaries':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.iterdir() if p.is_file()}},indent=2)+'\n')
