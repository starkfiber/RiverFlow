"""Independent bounded bridge oracle, exact frame-output checks, stream failures."""
from pathlib import Path
import subprocess,struct,random,json,hashlib,sys,threading,time
V=Path('experiments/rf2net/bridge');D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('artifacts/rf2net-bridge');D.mkdir(parents=True,exist_ok=True);compiler=Path('artifacts/rf2decision-sustained/compiler-opt').resolve()
rng=random.Random(161108)
def frame(dst,src,size=60,kind=0x88b5):
 assert size>=14
 return dst.to_bytes(6,'big')+src.to_bytes(6,'big')+struct.pack('!H',kind)+bytes((i*37+size)%256 for i in range(size-14))
A=0x020000000001;B=0x020000000002;C=0x020000000003
class Oracle:
 def __init__(self):self.table={};self.clock=None
 def run(self,port,tick,b):
  if not 60<=len(b)<=1514:return 5<<8
  if port not in (0,1):return 6<<8
  kind=int.from_bytes(b[12:14],'big')
  if kind in (0x8100,0x88a8):return 9<<8
  if kind<0x600:return 10<<8
  src=int.from_bytes(b[6:12],'big');dst=int.from_bytes(b[:6],'big')
  if src==0 or b[6]&1:return 12<<8
  if dst==0:return 11<<8
  if 0x0180c2000000<=dst<=0x0180c200000f:return 8<<8
  if self.clock is not None and tick<self.clock:return 7<<8
  self.clock=tick
  self.table={k:v for k,v in self.table.items() if tick-v[1]<30}
  if src in self.table:index=self.table[src][2]
  elif len(self.table)<8:index=min(set(range(8))-{v[2] for v in self.table.values()})
  else:
   oldest=min(self.table,key=lambda k:(self.table[k][1],self.table[k][2]));index=self.table.pop(oldest)[2]
  self.table[src]=(port,tick,index)
  mask=1<<(1-port)
  if b[0]&1:return (3<<8)|mask
  if dst in self.table:
   if self.table[dst][0]==port:return 4<<8
   return (1<<8)|mask
  return (2<<8)|mask
cases=[]
def add(name,port,tick,b):cases.append((name,port,tick,b))
add('learn-A-unknown-B',0,0,frame(B,A));add('known-A-from-B',1,1,frame(A,B));add('same-port-filter',0,2,frame(A,C));add('move-B-to-port0',0,3,frame(A,B));add('known-B-now-port0',1,4,frame(B,C));add('expire-at-exact30',1,34,frame(B,C));add('clock-reversal-refuse',0,33,frame(A,B));add('clock-unchanged-after-refusal',0,34,frame(C,A))
for n in [0,1,13,14,59,60,61,127,255,256,512,1513,1514]:add('length-'+str(n),0,35,frame(B,A,n) if n>=14 else bytes(n))
for i in range(16):add('reserved-bridge-group-'+str(i),0,0xffffffff,frame(0x0180c2000000+i,A))
add('reserved-did-not-advance-clock',1,36,frame(A,B))
for kind in [0,1,1500,1501,1535,1536,0x800,0x806,0x8100,0x88a8,0x88b5,0xffff]:add('ethertype-'+str(kind),0,36,frame(B,A,kind=kind))
for src in [0,0xffffffffffff,0x010000000001,A]:add('source-'+str(src),1,37,frame(B,src))
for dst in [0,0xffffffffffff,0x01005e000001,0x0180c2000010,A]:add('destination-'+str(dst),0,38,frame(dst,B))
for port in [2,3,255]:add('invalid-port-'+str(port),port,0xffffffff,frame(A,B))
add('invalid-port-preserved-clock',1,38,frame(A,B))
# Fill, tie eviction, updates and source movement exceed the fixed table budget.
for i in range(20):add('table-pressure-'+str(i),i%2,40,frame(A,0x020000001000+i))
for i in range(20):add('table-probe-'+str(i),i%2,41,frame(0x020000001000+i,A))
# Seeded repeatable heterogeneous stream, with invalid frames interleaved.
tick=50
for i in range(2500):
 tick+=rng.randrange(3)
 src=0x020000000000+rng.randrange(1,24);dst=0x020000000000+rng.randrange(1,24);port=rng.randrange(2);n=rng.choice([60,61,64,74,128,512,1514]);kind=0x88b5
 if i%37==0:dst=0xffffffffffff
 if i%41==0:src|=0x010000000000
 if i%43==0:kind=0x8100
 if i%47==0:port=7
 b=frame(dst,src,n,kind)
 add('seeded-'+str(i),port,tick-5 if i%53==0 else tick,b)
base_tick=tick+100;X=0x02000000ab01;Y=0x02000000ab02
add('expiry-learn',0,base_tick,frame(Y,X));add('expiry-still-live29',1,base_tick+29,frame(X,Y));add('expiry-exact30',1,base_tick+30,frame(X,Y))
add('u32-clock-max',0,0xffffffff,frame(B,A));add('clock-wrap-refused',1,0,frame(A,B));add('still-live-at-max',1,0xffffffff,frame(A,B))

def pack(rows):return b''.join(struct.pack('<HBBI',len(b),port,0,tick)+b for name,port,tick,b in rows)
def expected(rows):
 oracle=Oracle();result=b'';answers=[]
 for name,port,tick,b in rows:
  before=(oracle.clock,oracle.table.copy());r=oracle.run(port,tick,b)
  if r>>8 in [5,6,7,8,9,10,11,12]:assert before==(oracle.clock,oracle.table)
  raw=b if r&3 else b'';result+=struct.pack('<HH',r,len(raw))+raw;answers.append({'name':name,'decision':r,'frameSHA256':hashlib.sha256(b).hexdigest()})
 return result,answers
def expected_state(rows):
 oracle=Oracle();out=b''
 for name,port,tick,b in rows:
  result=oracle.run(port,tick,b);raw=b if result&3 else b''
  out+=struct.pack('<HH',result,len(raw))+raw
  slots={v[2]:(k,v[0],v[1]) for k,v in oracle.table.items()}
  for i in range(8):out+=struct.pack('<QQQ',*slots.get(i,(0,0,0)))
  out+=struct.pack('<QQ',oracle.clock or 0,int(oracle.clock is not None))
 return out
probe_source=(V/'main.flow').read_text().replace('  set count=count+1',"""  let state=buffer("bridge_state",208)
  let k=0
  while k<8
   do store64(state+k*24,mac[k])
   do store64(state+k*24+8,ports[k])
   do store64(state+k*24+16,seen[k])
   set k=k+1
  end
  do store64(state+192,clock[0])
  do store64(state+200,clock[1])
  if write_exact(1,state,208)==0
   return 3
  end
  set count=count+1""",1)
(V/'state_probe.flow').write_text(probe_source)
blob=pack(cases);want,answers=expected(cases);(D/'INPUT.bin').write_bytes(blob);(D/'EXPECTED.bin').write_bytes(want)
rows=[]
for mode in ['plain','opt']:
 exe=D/('program-'+mode);args=[str(compiler),str(V/'main.flow'),str(exe),'--compact']+(['--opt'] if mode=='opt' else [])
 p=subprocess.run(args,capture_output=True,text=True,timeout=40);assert p.returncode==0,p.stderr+p.stdout
 subprocess.run(['codesign','-s','-',str(exe)],capture_output=True,check=True)
 p=subprocess.run([str(exe.resolve())],input=blob,capture_output=True,timeout=30)
 (D/('ACTUAL-'+mode+'.bin')).write_bytes(p.stdout)
 assert p.returncode==0 and p.stdout==want,(mode,p.returncode,len(p.stdout),len(want),p.stderr)
 errors=[]
 raw=pack(cases[:1])
 for n in range(len(raw)):
  if n==0:continue
  p=subprocess.run([str(exe.resolve())],input=raw[:n],capture_output=True,timeout=5);assert p.returncode==2 and not p.stdout,(mode,'truncated',n,p.returncode,p.stdout)
  errors.append('truncated-'+str(n))
 for label,broken in [('oversize',struct.pack('<HBBI',1515,0,0,0)),('flags',struct.pack('<HBBI',60,0,1,0))]:
  p=subprocess.run([str(exe.resolve())],input=broken,capture_output=True,timeout=5);assert p.returncode==2 and not p.stdout,(mode,label,p.returncode,p.stdout);errors.append(label)
 # Fragments arrive separately through a live process; output must not wait for EOF.
 split=cases[:8];split_want,_=expected(split);proc=subprocess.Popen([str(exe.resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 out=[]
 def receive():out.append(proc.stdout.read(len(split_want)))
 worker=threading.Thread(target=receive,daemon=True);worker.start()
 for b in pack(split):proc.stdin.write(bytes([b]));proc.stdin.flush()
 worker.join(5);assert not worker.is_alive() and out==[split_want],(mode,'stream did not respond before EOF')
 proc.stdin.close();proc.wait(timeout=5);assert proc.returncode==0
 # Exactly4096 records succeed; a4097th is refused without emitting its result.
 unit=cases[:1]*4096;unit_blob=pack(unit);unit_want,_=expected(unit)
 p=subprocess.run([str(exe.resolve())],input=unit_blob,capture_output=True,timeout=30);assert p.returncode==0 and p.stdout==unit_want
 p=subprocess.run([str(exe.resolve())],input=unit_blob+raw,capture_output=True,timeout=30);assert p.returncode==2 and p.stdout==unit_want
 errors+=['one-byte-stream-before-EOF','4096-record-cap','4097th-record-refusal']
 probe=D/('state-probe-'+mode)
 args=[str(compiler),str(V/'state_probe.flow'),str(probe),'--compact']+(['--opt'] if mode=='opt' else [])
 subprocess.run(args,capture_output=True,check=True,timeout=40);subprocess.run(['codesign','-s','-',str(probe)],capture_output=True,check=True)
 state_want=expected_state(cases);q=subprocess.run([str(probe.resolve())],input=blob,capture_output=True,timeout=30)
 (D/('STATE-ACTUAL-'+mode+'.bin')).write_bytes(q.stdout)
 assert q.returncode==0 and q.stdout==state_want,(mode,'state differs',q.returncode,len(q.stdout),len(state_want))
 # A closed consumer is never reported as successful delivery.
 broken=subprocess.Popen([str(exe.resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 broken.stdout.close();_,stderr=broken.communicate(raw,timeout=5);assert broken.returncode==3,(mode,'closed-output',broken.returncode,stderr)
 errors.append('closed-output-refusal')
 rows.append(dict(mode=mode,passed=True,stateSnapshots=len(cases),closedOutputExit=broken.returncode,frameCases=len(cases),streamBoundaryControls=len(errors),binarySHA256=hashlib.sha256(exe.read_bytes()).hexdigest(),actualSHA256=hashlib.sha256((D/('ACTUAL-'+mode+'.bin')).read_bytes()).hexdigest()))
 print(mode,len(cases),'frames and',len(errors),'stream controls PASS',flush=True)
receipt={'passed':True,'results':rows,'decisions':answers,'scope':'Native Mac ARM64 frame transformation engine over stdin/stdout, no NIC, guest deployment, STP/VLAN, live switch or performance claim','inputsSHA256':hashlib.sha256(blob).hexdigest(),'expectedSHA256':hashlib.sha256(want).hexdigest(),'compilerSHA256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in V.glob('*') if p.is_file()}}
(D/'RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n')
