import random,struct,subprocess,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
class Oracle:
 def __init__(self):self.g=1;self.halt=0;self.turn=0;self.value=0;self.slots=[[0]*8 for _ in range(4)]
 def advance(self):
  if self.g>=4294967295:self.halt=1;self.slots=[[0]*8 for _ in range(4)];return False
  self.g+=1;return True
 def event(self,e):
  op,s,peer,ch,g,id,mode,v=e;r=99
  if op==0:
   if s>=4 or peer==0 or ch==0 or mode>1:r=1
   elif self.halt:r=2
   elif any(i!=s and p[6] and p[0]==peer and p[1]==ch for i,p in enumerate(self.slots)):r=3
   elif not self.advance():r=2
   else:self.slots[s]=[peer,ch,0,0,mode,0,1,0];r=0
  if op==1:
   if s>=4:r=1
   else:
    ok=self.advance();self.slots[s]=[0]*8;r=0 if ok else 2
  if op==2:
   if s>=4:r=1
   elif self.halt or g!=self.g:r=2
   else:
    p=self.slots[s]
    if not p[6] or (p[0],p[1])!=(peer,ch):r=3
    elif id==0 or id<=p[5]:r=4
    elif p[2] and p[4]==0:r=5
    else:p[2]=id;p[3]=v;p[5]=id;r=0
  if op==3:
   r=0
   if not self.halt:
    for i in range(4):
     k=(self.turn+i)%4;p=self.slots[k]
     if p[6] and p[2]:self.value=p[3];p[2]=p[3]=0;self.turn=(k+1)%4;r=k+1;break
    if not r:self.value=0
  p=self.slots[s] if s<4 else [0]*8
  return (r,self.g,self.value,p[2],p[3],p[5],p[6],self.halt)
def event(op,s=0,peer=1,ch=1,g=0,id=1,mode=1,v=123):return (op,s,peer,ch,g,id,mode,v)
def campaign(seed):
 rng=random.Random(seed);o=Oracle();es=[];answers=[]
 def add(e):es.append(e);answers.append(o.event(e));return answers[-1]
 # Independent sender/channel bindings and overload isolation.
 for s in range(4):assert add(event(0,s,peer=s+1,ch=1))[0]==0
 g=o.g
 for id in range(1,101):assert add(event(2,0,g=g,id=id))[0]==0
 assert add(event(2,1,peer=2,g=g,v=999))[0]==0
 assert add(event(3))[0]==1
 assert add(event(3))[0]==2
 # Read/validate -> revoke -> enqueue: stale token refuses.
 token=o.g;add(event(1,0));assert add(event(2,0,g=token,id=200))[0]==2
 # Preserve refusal must not consume the refused ID.
 add(event(0,0,mode=0));g=o.g
 assert add(event(2,g=g,id=1))[0]==0
 assert add(event(2,g=g,id=2))[0]==5
 add(event(3));assert add(event(2,g=g,id=2))[0]==0
 # Duplicate sender/channel binding refuses rather than making extra quotas.
 assert add(event(0,2,peer=1,ch=1))[0]==3
 for _ in range(2000):
  s=rng.randrange(6);op=rng.randrange(5);p=o.slots[s] if s<4 else [0]*8
  add(event(op,s,peer=p[0] if rng.random()<.8 else rng.randrange(5),ch=p[1] if rng.random()<.8 else rng.randrange(3),g=o.g if rng.random()<.7 else max(0,o.g-1),id=rng.randrange(1,400),mode=rng.randrange(3),v=rng.getrandbits(64)))
 return es,answers
if __name__=='__main__':
 out=ROOT/'artifacts/rf2net-owned-queues-verification';out.mkdir(exist_ok=False)
 bins=[ROOT/'artifacts/rf2net-owned-queues-opt-b/program',ROOT/'artifacts/rf2net-owned-queues-plain/program']
 summary=[]
 for binary in bins:
  checks=0
  for seed in range(20):
   es,expected=campaign(seed);data=b''.join(struct.pack('<8Q',*e) for e in es)
   r=subprocess.run([str(binary)],input=data,capture_output=True,timeout=15)
   assert r.returncode==0,(binary,seed,r.returncode,r.stderr)
   actual=list(struct.iter_unpack('<8Q',r.stdout));assert len(actual)==len(expected)
   for i,(a,b) in enumerate(zip(actual,expected)):assert a==b,(binary,seed,i,es[i],a,b)
   checks+=len(expected)
  for n in [1,63,65]:
   r=subprocess.run([str(binary)],input=b'\0'*n,capture_output=True,timeout=5);assert r.returncode==2
  summary.append(dict(binary=str(binary),events=checks,seeds=20,truncated_stream_controls=3))
 (out/'result.json').write_text(json.dumps(summary,indent=2))
 files=[Path(__file__),Path(__file__).with_name('queues.flow'),Path(__file__).with_name('main.flow'),*bins,out/'result.json']
 (out/'evidence-index.json').write_text(json.dumps({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},indent=2));print(json.dumps(summary,indent=2))
