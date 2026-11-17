"""Native durable lease/reservation tests. No interfaces, live VMs or packets."""
from pathlib import Path
import subprocess,json,hashlib,struct,tempfile,select,os,resource,signal,shutil,sys
V=Path('experiments/rf2net/dhcp-durable');D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('artifacts/rf2net-dhcp-durable-final');D.mkdir(exist_ok=False);C=Path('artifacts/rf2decision-sustained/compiler-opt').resolve()
SERVER=0x0a4d0002;BASE=0x0a4d0064;MASK=2**64-1

def mac(c):return 0x020000000000+c
def pkt(c,kind=1,xid=1,ip=None,srv=None,ci=0):
 b=bytearray(240);b[:3]=b'\1\1\6';b[4:8]=struct.pack('!I',xid);b[12:16]=struct.pack('!I',ci);b[28:34]=mac(c).to_bytes(6,'big');b[236:240]=bytes.fromhex('63825363');b+=bytes([53,1,kind])
 if ip is not None:b+=b'\x32\4'+struct.pack('!I',ip)
 if srv is not None:b+=b'\x36\4'+struct.pack('!I',srv)
 return bytes(b+b'\xff').ljust(300,b'\0')
def wire(b,t=100):return struct.pack('<HI',len(b),t)+b
def checksum(b):
 h=14695981039346656037
 for c in b:h=((h^c)*1099511628211)&MASK
 return h
def repair(b):
 b=bytearray(b);struct.pack_into('<Q',b,240,checksum(b[:240]));return bytes(b)
def records(path):
 b=path.read_bytes();assert len(b)%256==0 and b
 out=[]
 for at in range(0,len(b),256):
  r=b[at:at+256];assert r[:8]==b'RF2DH01!' and r[248:]==b'RF2END1!' and struct.unpack_from('<Q',r,240)[0]==checksum(r[:240]);assert struct.unpack_from('<Q',r,8)[0]==len(out)+1
  out.append({'generation':len(out)+1,'clock':struct.unpack_from('<QQ',r,16),'reserves':struct.unpack_from('<5Q',r,32),'slots':[struct.unpack_from('<4Q',r,72+i*32) for i in range(5)]})
 return out

def compile_at(src,exe,mode):
 x=subprocess.run([str(C),str(src),str(exe),'--compact']+(['--opt'] if mode=='opt' else []),capture_output=True,text=True,timeout=40);assert x.returncode==0,x.stdout+x.stderr;subprocess.run(['codesign','-s','-',str(exe)],capture_output=True,check=True)
def run(exe,command,path,data=b'',want=0,preexec=None):
 x=subprocess.run([str(exe.resolve()),command,str(path)],input=data,capture_output=True,timeout=8,preexec_fn=preexec);assert x.returncode==want,(command,path.name,want,x.returncode,x.stderr,x.stdout[:30]);return x
allrows=[]
for mode in ['plain','opt']:
 exe=D/('server-'+mode);compile_at(V/'main.flow',exe,mode);rows=[]
 def remember(label):rows.append({'label':label,'passed':True})
 def init(path,res=(0,0,0,0,0)):run(exe,'init',path,struct.pack('<5Q',*res));assert path.stat().st_mode&0o777==0o600;records(path)
 def request(path,c,kind=1,xid=1,ip=None,srv=None,ci=0,t=100,want=2,yi=None):
  b=pkt(c,kind,xid,ip,srv,ci);x=run(exe,'serve',path,wire(b,t));code,n=struct.unpack_from('<HH',x.stdout);assert code==want and len(x.stdout)==4+n,(c,kind,want,code)
  if code in [2,5,6]:
   assert n==300 and x.stdout[4:7]==b'\2\1\6' and x.stdout[8:12]==struct.pack('!I',xid)
   assert x.stdout[32:38]==mac(c).to_bytes(6,'big')
   if yi is not None:assert x.stdout[20:24]==struct.pack('!I',yi),(c,yi,x.stdout[20:24])
  else:assert n==0
  records(path);return x
 with tempfile.TemporaryDirectory(prefix='rf2lease-') as tmp:
  root=Path(tmp);db=root/'leases';res=(mac(5),0,0,0,mac(1));init(db,res);remember('explicit-private-init-reservations')
  run(exe,'init',db,bytes(40),want=4);remember('existing-init-refused')
  for order,c in enumerate([2,3,4,1,5]):request(db,c,xid=100+c,yi=BASE+[None,4,1,2,3,0][c]);remember('restart-offer-client-'+str(c))
  for c,slot in [(2,1),(3,2),(4,3),(1,4),(5,0)]:request(db,c,3,xid=100+c,ip=BASE+slot,srv=SERVER,want=5,yi=BASE+slot);remember('restart-ACK-client-'+str(c))
  assert records(db)[-1]['reserves']==res
  before=db.read_bytes();request(db,1,3,xid=101,ip=BASE+4,srv=SERVER,want=5,yi=BASE+4);assert db.read_bytes()==before;remember('duplicate-ACK-no-extra-journal-record')
  request(db,6,want=12);remember('full-pool-refuses-sixth')
  request(db,6,7,ci=BASE+1,srv=SERVER,want=0);assert records(db)[-1]['slots'][1][1]==mac(2);remember('wrong-owner-release-preserved')
  request(db,1,7,ci=BASE+4,srv=SERVER,want=0);request(db,6,want=12);remember('reserved-free-address-not-dynamically-allocated')
  request(db,1,3,ip=BASE+4,want=5,yi=BASE+4);assert records(db)[-1]['slots'][4][1]==mac(1);remember('known-reservation-INIT-REBOOT')
  request(db,5,4,ip=BASE,srv=SERVER,want=0);request(db,5,want=12);remember('declined-reservation-quarantined-no-fallback')
  request(db,6,t=700,yi=BASE+1);remember('expired-dynamic-lease-reused-reservations-retained')
  request(db,5,t=700,yi=BASE);remember('reserved-quarantine-exact-expiry')
  before=db.read_bytes();request(db,5,t=699,want=13);assert db.read_bytes()==before;remember('absolute-clock-regression-fails-without-write')
  before=db.read_bytes();run(exe,'serve',db,wire(b'x',701));assert db.read_bytes()==before;remember('malformed-payload-no-write')
  missing=root/'missing';run(exe,'serve',missing,b'',want=4);assert not missing.exists();remember('missing-store-never-auto-initialized')
  badconf=root/'bad-config'
  for config in [(mac(1),mac(1),0,0,0),(1<<48,0,0,0,0),(0x010000000001,0,0,0,0)]:run(exe,'init',badconf,struct.pack('<5Q',*config),want=2);assert not badconf.exists()
  remember('invalid-duplicate-reservations-refused-before-create')
  # Filesystem admission failures must not damage the original store.
  link=root/'symlink';link.symlink_to(db);run(exe,'serve',link,b'',want=4);assert db.read_bytes()==before;remember('symlink-refused')
  hard=root/'hard';os.link(db,hard);run(exe,'serve',db,b'',want=4);hard.unlink();remember('hardlink-refused')
  fifo=root/'fifo';os.mkfifo(fifo,0o600);run(exe,'serve',fifo,b'',want=4);remember('FIFO-refused-without-blocking')
  db.chmod(0o644);run(exe,'serve',db,b'',want=4);db.chmod(0o600);remember('insecure-mode-refused')
  # Lock held while serving, not just around loading.
  holder=subprocess.Popen([str(exe.resolve()),'serve',str(db)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  try:
   import time;time.sleep(.1);assert holder.poll() is None;run(exe,'serve',db,b'',want=4);remember('concurrent-writer-refused')
  finally:holder.kill();holder.wait(timeout=5)
  run(exe,'serve',db);remember('lock-released-after-process-death')
  # An ACK was read before a real SIGKILL; reopening must preserve that lease.
  crash=root/'crash';init(crash)
  live=subprocess.Popen([str(exe.resolve()),'serve',str(crash)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  try:
   live.stdin.write(wire(pkt(1,xid=901)));live.stdin.flush();assert select.select([live.stdout],[],[],5)[0];answer=live.stdout.read(304);assert len(answer)==304 and answer[0]==2
   live.stdin.write(wire(pkt(1,3,xid=901,ip=BASE,srv=SERVER)));live.stdin.flush();assert select.select([live.stdout],[],[],5)[0];answer=live.stdout.read(304);assert len(answer)==304 and answer[0]==5
  finally:live.kill();live.wait(timeout=5)
  assert records(crash)[-1]['slots'][0][0]==2;request(crash,1,3,xid=902,ci=BASE,t=101,want=5,yi=BASE);remember('real-process-kill-after-ACK-reopens-bound-lease')
  # Lost output is not a lost durable lease.
  lost=root/'lost';init(lost);p=subprocess.Popen([str(exe.resolve()),'serve',str(lost)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);p.stdout.close();p.communicate(wire(pkt(2)),timeout=5);assert p.returncode==3
  assert records(lost)[-1]['slots'][0][1]==mac(2);request(lost,2,3,ip=BASE,srv=SERVER,want=5,yi=BASE);remember('output-failure-keeps-committed-offer-for-retry')
  # Real child-local filesystem limit forces an append short write/EFBIG.
  full=root/'limited';init(full);original=full.read_bytes()
  def limit():signal.signal(signal.SIGXFSZ,signal.SIG_IGN);resource.setrlimit(resource.RLIMIT_FSIZE,(len(original)+128,len(original)+128))
  x=run(exe,'serve',full,wire(pkt(1)),want=6,preexec=limit);assert not x.stdout and full.read_bytes()==original;run(exe,'serve',full);remember('real-file-size-failure-rolls-back-before-reply')
  # All partial final record sizes fail closed, without rewriting or replying.
  original=crash.read_bytes();bad=root/'corrupt'
  for n in range(1,256):
   blob=original[:256]+original[256:256+n];bad.write_bytes(blob);bad.chmod(0o600);x=run(exe,'serve',bad,wire(pkt(7)),want=5);assert not x.stdout and bad.read_bytes()==blob
  remember('255-partial-final-record-prefixes-refused')
  for at in [0,8,16,24,32,72,80,88,96,232,240,248,255]:
   blob=bytearray(original);blob[at]^=1;bad.write_bytes(blob);bad.chmod(0o600);x=run(exe,'serve',bad,wire(pkt(7)),want=5);assert not x.stdout and bad.read_bytes()==blob
  remember('corrupt-header-state-checksum-marker-refused')
  # Structurally valid checksums cannot excuse invalid schema semantics.
  first=original[:256]
  for at,value in [(16,1),(24,1),(32,1<<48),(40,mac(5)),(72,4),(80,mac(1)),(232,1)]:
   b=bytearray(first);struct.pack_into('<Q',b,at,value)
   if at==40:struct.pack_into('<Q',b,32,value)
   b=repair(b);bad.write_bytes(b);bad.chmod(0o600);x=run(exe,'serve',bad,want=5);assert not x.stdout
  remember('checksum-valid-invalid-semantic-record-refused')
  b=bytearray(original[256:512]);struct.pack_into('<Q',b,32,mac(9));b=repair(b);bad.write_bytes(first+b);bad.chmod(0o600);run(exe,'serve',bad,want=5);remember('reservation-change-within-journal-refused')
  # Capacity exhaustion is refusal, never silent overwrite of acknowledged state.
  units=[]
  for gen in range(1,4097):
   b=bytearray(first);struct.pack_into('<Q',b,8,gen);units.append(repair(b))
  cap=root/'capacity';cap.write_bytes(b''.join(units));cap.chmod(0o600);run(exe,'serve',cap);x=run(exe,'serve',cap,wire(pkt(1)),want=2);assert not x.stdout;remember('4096-record-cap-no-rewrite')
  b=bytearray(first);struct.pack_into('<Q',b,8,4097);cap.write_bytes(cap.read_bytes()+repair(b));run(exe,'serve',cap,want=5);remember('4097th-record-refused-on-load')
  # Source-hook fault variants are explicit local test executables, not shipping options.
  variants=[('fsync-once',"return syscall6(95,fd,0,0,0,0,0)",'''let counter=buffer("sync_fault",8)
 if load64(counter)==0
  do store64(counter,1)
  return 0-5
 end
 return syscall6(95,fd,0,0,0,0,0)'''),('partial-write',None,None),('uncertain-rollback',None,None)]
  for name,key,rep in variants:
   vd=D/(mode+'-'+name);vd.mkdir();s=(V/'store.flow').read_text()
   if name=='fsync-once':s=s.replace(key,rep,1)
   else:
    start=s.index('fn lease_write(');end=s.index('\nfn lease_sync',start)
    s=s[:start]+'''fn lease_write(fd,p,n)
 if fd!=1
  do write(fd,p,128)
  return 0
 end
 return 1
end
'''+s[end:]
    if name=='uncertain-rollback':s=s.replace('return syscall6(201,fd,n,0,0,0,0)','return 0-5',1)
   (vd/'store.flow').write_text(s);(vd/'dhcp.flow').write_bytes((V/'dhcp.flow').read_bytes());(vd/'main.flow').write_bytes((V/'main.flow').read_bytes());mut=vd/'program';compile_at(vd/'main.flow',mut,mode)
   target=root/name;init(target);previous=target.read_bytes();x=run(mut,'serve',target,wire(pkt(1)),want=6);assert not x.stdout
   if name=='uncertain-rollback':assert target.read_bytes()!=previous;run(exe,'serve',target,want=5)
   else:assert target.read_bytes()==previous;run(exe,'serve',target)
   remember('hook-'+name+'-no-reply-safe-restart-or-refusal')
 allrows.append({'mode':mode,'passed':True,'namedControls':len(rows),'partialTailCases':255,'cases':rows,'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest()});print(mode,len(rows),'named durable/reservation controls +255 partial tails passed',flush=True)
(D/'RESULTS.json').write_text(json.dumps({'passed':True,'results':allrows,'scope':'Native Mac RF2 journal/reservation stream component; real process restarts, child-local file limit, explicit fsync/write fault hooks. No power-cut, UDP, VM102, HA or physical durability qualification. Input clock is caller-supplied trusted absolute UTC seconds, not autonomous time authentication.','compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in V.glob('*') if p.is_file()}},indent=2)+'\n')
