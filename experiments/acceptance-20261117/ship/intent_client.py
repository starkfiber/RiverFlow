"""Research peer SDK; stdlib reference crypto, durable nonce leases and bounded reconnect.
Not a production cryptographic library or native RF2 SDK. Boot provisioning is external.
"""
import struct,json,os,stat,fcntl,tempfile,hashlib
from pathlib import Path
REQ=b'RF2AE01!';REP=b'RF2AR01!';INNER=b'RF2IC01!';REPLY=b'RF2IR01!'
def block(key,nonce,counter):
 s=list(struct.unpack('<4I',b'expand 32-byte k'))+list(struct.unpack('<8I',key))+[counter]+list(struct.unpack('<3I',nonce));x=s.copy()
 def q(a,b,c,d):
  for left,right,shift in [(a,b,16),(c,d,12),(a,b,8),(c,d,7)]:
   x[left]=(x[left]+x[right])&0xffffffff
   target=d if left==a else b;v=x[target]^x[left];x[target]=((v<<shift)|(v>>(32-shift)))&0xffffffff
 for _ in range(10):
  for p in [(0,4,8,12),(1,5,9,13),(2,6,10,14),(3,7,11,15),(0,5,10,15),(1,6,11,12),(2,7,8,13),(3,4,9,14)]:q(*p)
 return struct.pack('<16I',*[(a+b)&0xffffffff for a,b in zip(x,s)])
def crypt(key,nonce,data):
 out=bytearray()
 for at in range(0,len(data),64):
  stream=block(key,nonce,1+at//64);out.extend(b^stream[i] for i,b in enumerate(data[at:at+64]))
 return bytes(out)
def tag(key,nonce,aad,cipher):
 k=block(key,nonce,0);r=int.from_bytes(k[:16],'little')&0x0ffffffc0ffffffc0ffffffc0fffffff;s=int.from_bytes(k[16:32],'little');msg=aad+bytes((-len(aad))%16)+cipher+bytes((-len(cipher))%16)+struct.pack('<QQ',len(aad),len(cipher));a=0
 for i in range(0,len(msg),16):a=((a+int.from_bytes(msg[i:i+16],'little')+(1<<128))*r)%((1<<130)-5)
 return ((a+s)&((1<<128)-1)).to_bytes(16,'little')
def seal(key,nonce,aad,plain):
 c=crypt(key,nonce,plain);return c+tag(key,nonce,aad,c)
def opened(key,nonce,aad,sealed):
 import hmac
 if len(sealed)<16 or not hmac.compare_digest(tag(key,nonce,aad,sealed[:-16]),sealed[-16:]):raise ValueError('authentication')
 return crypt(key,nonce,sealed[:-16])
class CredentialStore:
 def __init__(self,path):self.path=Path(path)
 def _check_parent(self):
  p=self.path.parent;l=p.lstat()
  if stat.S_ISLNK(l.st_mode) or l.st_uid!=os.getuid() or l.st_mode&0o077:raise ValueError('private credential directory required')
 def _save(self,v):
  self._check_parent();fd,name=tempfile.mkstemp(prefix='.credential-',dir=self.path.parent);os.fchmod(fd,0o600)
  try:
   with os.fdopen(fd,'w') as f:json.dump(v,f);f.flush();os.fsync(f.fileno())
   os.replace(name,self.path);d=os.open(self.path.parent,os.O_RDONLY)
   try:os.fsync(d)
   finally:os.close(d)
  finally:
   if os.path.exists(name):os.unlink(name)
 def _read(self):
  self._check_parent();fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
  with os.fdopen(fd) as f:
   st=os.fstat(f.fileno())
   if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode&0o077 or st.st_size>16384:raise ValueError('private credential file required')
   return json.load(f)
 def install(self,c2s,s2c,boot):
  self._check_parent();fd=os.open(str(self.path)+'.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
  try:
   st=os.fstat(fd)
   if st.st_uid!=os.getuid() or st.st_mode&0o077 or not stat.S_ISREG(st.st_mode):raise ValueError('private lock required')
   fcntl.flock(fd,fcntl.LOCK_EX);return self._install(c2s,s2c,boot)
  finally:os.close(fd)
 def _install(self,c2s,s2c,boot):
  if len(c2s)!=32 or len(s2c)!=32 or len(boot)!=16 or c2s==s2c or not any(c2s) or not any(s2c) or not any(boot):raise ValueError('credentials')
  self._check_parent();old=self._read() if self.path.exists() else {'usedKeys':[],'usedBoots':[]}
  keys=[hashlib.sha256(k).hexdigest() for k in (c2s,s2c)];bid=boot.hex()
  if any(k in old['usedKeys'] for k in keys) or bid in old['usedBoots'] or len(old['usedBoots'])>=32:raise ValueError('credential reuse/history capacity')
  self._save(dict(c2s=c2s.hex(),s2c=s2c.hex(),boot=bid,seq=0,usedKeys=old['usedKeys']+keys,usedBoots=old['usedBoots']+[bid]))
 def reserve(self):
  self._check_parent();fd=os.open(str(self.path)+'.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
  try:
   st=os.fstat(fd)
   if st.st_uid!=os.getuid() or st.st_mode&0o077 or not stat.S_ISREG(st.st_mode):raise ValueError('private lock required')
   fcntl.flock(fd,fcntl.LOCK_EX);v=self._read()
   if type(v['seq']) is not int or not 0<=v['seq']<2**64-1:raise ValueError('sequence exhaustion')
   v['seq']+=1;self._save(v);return bytes.fromhex(v['c2s']),bytes.fromhex(v['s2c']),bytes.fromhex(v['boot']),v['seq']
  finally:os.close(fd)
class UnknownOutcome(Exception):pass
class Client:
 def __init__(self,store,exchange,mode=0):self.store=store;self.exchange=exchange;self.mode=mode;self.epoch=None;self.boot=None
 def _send(self,op,mid=0,retention=0,value=b'',hello=False):
  c,s,b,seq=self.store.reserve()
  if not hello and b!=self.boot:raise ConnectionError('boot changed')
  epoch=0 if hello else self.epoch
  head=REQ+b+struct.pack('<QQ',epoch,seq);body=INNER+struct.pack('<8Q',op,epoch,mid,0,retention,len(value),int.from_bytes(value,'little'),self.mode if hello else 0)
  wire=head+seal(c,struct.pack('<IQ',epoch,seq),head,body);reply=self.exchange(wire)
  if len(reply)!=128 or reply[:8]!=REP or reply[8:24]!=b or reply[24:40]!=struct.pack('<QQ',epoch,seq):raise ValueError('reply correlation')
  body=opened(s,struct.pack('<IQ',epoch,seq),reply[:40],reply[40:]);fields=struct.unpack('<8Q',body[8:])
  if body[:8]!=REPLY or fields[1]!=mid or (not hello and fields[0]!=epoch):raise ValueError('reply body')
  self.boot=b;return fields
 def connect(self):
  result=self._send(0,hello=True)
  if result[2]!=13 or not 0<result[0]<2**32:raise ConnectionError('handshake refused')
  self.epoch=result[0];return result
 def call(self,op,mid=0,retention=0,value=b''):
  if op not in (1,2,3,4) or len(value)>8:raise ValueError('operation/value')
  safe_reconnect=op==4 or(op==1 and self.mode==0)
  for attempt in range(3):
   try:
    if self.epoch is None:self.connect()
    result=self._send(op,mid,retention,value)
    if result[2]==2 and safe_reconnect:self.epoch=None;continue
    return result
   except TimeoutError:
    if not safe_reconnect:raise UnknownOutcome('application reconciliation required')
    if attempt==0:continue  # Safe observations/latest semantics only; fresh nonce.
    self.epoch=None
   except ConnectionError:
    if not safe_reconnect:raise UnknownOutcome('boot/session changed; reconcile first')
    self.epoch=None
  raise ConnectionError('bounded reconnect exhausted')
