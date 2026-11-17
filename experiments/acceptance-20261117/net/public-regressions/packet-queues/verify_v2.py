import hashlib,hmac,json,random,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def event(op,s=0,peer=1,ch=1,session=1,g=0,id=1,ret=10,mode=1,size=4,ticket=0,data=b'test'):
 return (op,s,peer,ch,session,g,id,ret,mode,size,ticket,0),data[:32].ljust(32,b'\0')
def packed(e):return struct.pack('<12Q',*e[0])+e[1]
class Model:
 def __init__(self):self.g=1;self.now=0;self.turn=0;self.ticket=0;self.ps=[[0]*16 for _ in range(4)];self.data=[bytearray(64) for _ in range(4)]
 def pending(self,s):self.ps[s][7:9]=[0,0];self.data[s][:32]=bytes(32)
 def dispatch(self,s):self.ps[s][9:14]=[0]*5;self.data[s][32:]=bytes(32)
 def apply(self,e):
  (op,s,peer,ch,session,g,id,ret,mode,size,ticket,_),data=e;r=99
  if op==0:
   if s>=4 or not peer or not ch or not session or ret<=self.now or ret>10**9 or mode>1:r=1
   elif self.ps[s][12]==2:r=6
   elif any(i!=s and p[0] and p[1:3]==[peer,ch] for i,p in enumerate(self.ps)):r=3
   elif self.g>=2**32-1:r=9
   else:self.g+=1;self.ps[s]=[1,peer,ch,session,ret,mode]+[0]*10;self.data[s]=bytearray(64);r=0
  if op==1:
   if s>=4:r=1
   else:
    self.ps[s][0]=0;self.pending(s)
    if self.ps[s][12]!=2:self.dispatch(s)
    if self.g>=2**32-1:r=9
    else:self.g+=1;r=0
  if op==2:
   if s>=4:r=1
   else:
    p=self.ps[s]
    if not p[0] or p[1:4]!=[peer,ch,session]:r=3
    elif g!=self.g:r=2
    elif self.now>=p[4] or not 1<=ret<=1000:r=7
    elif not 1<=size<=32:r=8
    elif not id or id<=p[6]:r=4
    elif p[7] and p[5]==0:r=5
    else:self.data[s][:32]=data[:size]+bytes(32-size);p[6:9]=[id,size,min(self.now+ret,p[4])];r=0
  if op==3:
   r=0
   for i in range(4):
    k=(self.turn+i)%4;p=self.ps[k]
    if p[0] and p[7] and not p[12]:
     if self.ticket>=2**32-1:break
     self.ticket+=1;p[9:14]=[p[7],p[8],self.ticket,1,self.g];self.data[k][32:]=self.data[k][:32];self.pending(k);self.turn=(k+1)%4;r=k+1;break
  if op==4:
   if s>=4:r=1
   else:
    p=self.ps[s]
    if p[12]!=1 or p[11]!=ticket:r=4
    elif not p[0] or p[13]!=self.g or self.now>=p[10] or self.now>=p[4]:self.dispatch(s);r=2
    else:p[12]=2;r=0
  if op==5:
   if s>=4:r=1
   elif self.ps[s][12]!=2 or self.ps[s][11]!=ticket:r=4
   else:self.dispatch(s);r=0
  if op==6:
   if ticket<self.now or ticket>10**9:r=1
   else:
    self.now=ticket;r=0
    for i,p in enumerate(self.ps):
     if p[7] and (self.now>=p[8] or self.now>=p[4]):self.pending(i)
     if p[12]==1 and (self.now>=p[10] or self.now>=p[4]):self.dispatch(i)
  return struct.pack('<4Q',r,self.g,self.now,self.turn)+(struct.pack('<16Q',*self.ps[s])+bytes(self.data[s][32:]) if s<4 else bytes(160))
class AuthIngress:
 # Trusted local research adapter. HMAC authenticity only, not encryption or native crypto.
 def __init__(self):self.keys={1:b'public-test-fixture-key-not-a-secret'};self.revoked=set();self.identities={1:(1,1)}
 def sign(self,e):return hmac.digest(self.keys[e[0][4]],packed(e),'sha256')
 def admit(self,e,tag):
  session=e[0][4];key=self.keys.get(session)
  if session in self.revoked or key is None or not hmac.compare_digest(hmac.digest(key,packed(e),'sha256'),tag):raise ValueError('auth refusal')
  if e[0][0]!=2:raise ValueError('management is private')
  if e[0][2:4]!=self.identities[session]:raise ValueError('session identity mismatch')
  return e

def trial(seed):
 rng=random.Random(seed);m=Model();es=[];expected=[];names=[]
 def add(e,name=None,result=None):
  a=m.apply(e);es.append(e);expected.append(a)
  if result is not None:assert struct.unpack_from('<Q',a)[0]==result,name
  if name:names.append(name)
  return struct.unpack_from('<Q',a)[0]
 def bind(s,peer):add(event(0,s,peer=peer,session=peer,ret=100000),result=0)
 for s in range(4):bind(s,s+1)
 auth=AuthIngress();e=event(2,g=m.g)
 tag=auth.sign(e);assert auth.admit(e,tag)==e
 for offset in [0,16,32,40,48,56,72,96,127]:
  raw=bytearray(packed(e));raw[offset]^=1;mut=(struct.unpack('<12Q',raw[:96]),bytes(raw[96:]));before=len(es)
  try:auth.admit(mut,tag);raise AssertionError('forgery accepted')
  except ValueError:pass
  assert len(es)==before
 add(auth.admit(e,tag),'authenticated submit',0)
 add(e,'duplicate authenticated request refused',4)
 # Copy-in: later controller payload changes cannot mutate queue bytes.
 add(event(3),'dispatch',1);token=m.ps[0][11]
 add(event(1),'revoke dispatch before NIC handoff',0)
 add(event(4,ticket=token),'revoked dispatch commit refuses',4)
 bind(0,1);add(event(2,g=m.g),'fresh submit',0);add(event(3),'dispatch again',1);token=m.ps[0][11]
 add(event(4,ticket=token),'handoff commits',0);add(event(1),'revoke after handoff',0)
 add(event(0,ret=100000),'rebind cannot reuse in-flight buffer',6)
 add(event(5,ticket=token+1),'wrong completion cannot free owner',4)
 add(event(5,ticket=token),'matching completion frees revoked owner',0)
 bind(0,1);add(event(2,g=m.g,ret=2),'short lifetime',0);add(event(3));token=m.ps[0][11]
 add(event(6,ticket=2),'expiry clears uncommitted dispatch',0);add(event(4,ticket=token),'expired commit refuses',4)
 add(event(6,ticket=1),'clock reversal refuses',1)
 # Flood sender0 while sender1 retains its own waiting bytes.
 add(event(2,1,peer=2,session=2,g=m.g,id=1,data=b'peer-two'),result=0)
 for i in range(2,102):add(event(2,g=m.g,id=i,data=bytes([i%256])*32,size=32))
 assert m.ps[1][7]==4 and bytes(m.data[1][:4])==b'peer'
 names.append('sender overload preserves other queued bytes')
 auth.revoked.add(1)
 try:auth.admit(e,tag);raise AssertionError('revoked auth accepted')
 except ValueError:pass
 names.append('adapter session revocation denies ingress')
 auth.revoked.clear()
 for foreign in [event(2,peer=2,g=m.g),event(2,ch=2,g=m.g),event(0,g=m.g)]:
  try:auth.admit(foreign,auth.sign(foreign));raise AssertionError('wrong identity/management accepted')
  except ValueError:pass
 names.append('valid MAC cannot change session identity or invoke management')
 for _ in range(1500):
  s=rng.randrange(6);p=m.ps[s] if s<4 else [0]*16;op=rng.randrange(8)
  add(event(op,s,peer=p[1],ch=p[2],session=p[3],g=m.g if rng.random()<.8 else max(0,m.g-1),id=rng.randrange(150),ret=rng.randrange(1,1000) if op!=0 else m.now+10000,mode=rng.randrange(2),size=rng.randrange(35),ticket=(m.ps[s][11] if s<4 and rng.random()<.7 else m.now+1) if op!=6 else m.now+rng.randrange(4),data=rng.randbytes(32)))
 return es,expected,names
if __name__=='__main__':
 out=ROOT/'artifacts/rf2net-packet-verification-v2';out.mkdir(exist_ok=False)
 results=[]
 for path in ['artifacts/rf2net-packet-opt/program','artifacts/rf2net-packet-plain/program']:
  total=0
  for seed in range(20):
   es,expected,names=trial(seed);r=subprocess.run([str(ROOT/path)],input=b''.join(map(packed,es)),capture_output=True,timeout=15)
   assert r.returncode==0,(path,seed,r.stderr);assert len(r.stdout)==192*len(expected)
   for i,want in enumerate(expected):assert r.stdout[i*192:(i+1)*192]==want,(path,seed,i,es[i])
   total+=len(expected)
  results.append(dict(path=path,seeds=20,event_comparisons=total,named_controls=names,auth_tamper_checks_per_seed=9))
 (out/'result.json').write_text(json.dumps(results,indent=2))
 files=[Path(__file__),Path(__file__).with_name('main.flow'),Path(__file__).with_name('packets.flow'),out/'result.json']+[ROOT/r['path'] for r in results]
 (out/'evidence-index.json').write_text(json.dumps({str(f.resolve()):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},indent=2));print(json.dumps(results,indent=2))
