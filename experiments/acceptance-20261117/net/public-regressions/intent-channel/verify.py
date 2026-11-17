"""Native RF2 bounded ownership model checks. No sockets or VM operations."""
from pathlib import Path
import struct,subprocess,json,hashlib,random
R=Path(__file__).resolve().parents[3];V=Path(__file__).parent;D=R/'artifacts/rf2net-intent-channel';D.mkdir(exist_ok=True)
compiler=R/'artifacts/rf2decision-sustained/compiler-opt';source=V/'admission.flow'
class Oracle:
 def __init__(self):self.epoch=self.seen=self.id=self.size=self.value=self.deadline=self.clock=self.mode=self.cap=0
 def event(self,r):
  op,e,i,t,ttl,n,val,mode=r;code=8
  if op==0:
   code=1
   if self.epoch<e<=0xffffffff and 0<ttl<=1000 and mode in (0,1) and self.clock<=t<=1000000000:
    self.epoch=e;self.seen=self.id=self.size=self.value=self.deadline=0;self.clock=t;self.mode=mode;self.cap=ttl;code=13
  elif self.epoch==0 or e!=self.epoch:code=2
  elif not self.clock<=t<=1000000000:code=9
  else:
   self.clock=t;expired=bool(self.id and t>=self.deadline)
   if expired:self.id=self.size=self.value=self.deadline=0
   if op==1:
    if not self.seen<i<=0xffffffff:code=3
    elif not 0<n<=8:code=4
    elif not 0<ttl<=self.cap:code=5
    elif self.id and self.mode==1:code=6
    else:self.id=self.seen=i;self.size=n;self.value=val&((1<<(8*n))-1);self.deadline=t+ttl;code=0
   elif op in (2,3):
    code=7
    if self.id and self.id==i:self.id=self.size=self.value=self.deadline=0;code=12 if op==2 else 11
   elif op==4:code=10 if expired else 0
  return (code,self.id,self.size,self.value,self.seen,self.deadline)
def evt(op,e=1,i=0,t=0,ttl=50,n=3,val=0x112233,mode=0):return (op,e,i,t,ttl,n,val,mode)
scenarios=[('latest',[evt(0,ttl=100),evt(1,i=1,t=1,val=0xffffff112233),evt(1,i=2,t=2,ttl=40,n=2,val=0xaabb),evt(2,i=1,t=3),evt(1,i=2,t=4),evt(3,i=2,t=5),evt(2,i=2,t=6)]),('reliable',[evt(0,ttl=100,mode=1),evt(1,i=1,t=1),evt(1,i=2,t=2),evt(2,i=1,t=3),evt(1,i=2,t=4,ttl=3),evt(4,t=7),evt(2,i=2,t=8)]),('epoch',[evt(0,ttl=100),evt(1,i=1,t=1),evt(0,e=2,t=2,ttl=100),evt(1,e=2,i=1,t=3),evt(2,e=1,i=1,t=999),evt(2,e=2,i=1,t=4)]),('invalid',[evt(1,i=1),evt(0,ttl=0),evt(0,ttl=100),evt(1,i=1,t=1,n=9),evt(1,i=1,t=2,ttl=101),evt(1,i=1,t=3,n=8,val=(1<<64)-1),evt(1,i=2,t=2),evt(0,e=1,t=4),evt(3,i=1,t=4)])]
for seed in range(32):
 rng=random.Random(seed);records=[evt(0,ttl=100,mode=seed%2)];time=0
 for _ in range(200):
  time+=rng.randrange(5);records.append(evt(rng.choice([1,1,1,2,3,4,8]),e=rng.choice([1,1,1,0,2]),i=rng.randrange(1,60),t=time,ttl=rng.choice([0,1,20,100,101]),n=rng.randrange(11),val=rng.getrandbits(64)))
 scenarios.append(('seed-'+str(seed),records))
rows=[]
for label,opt in [('plain',False),('opt',True)]:
 b=D/('admission-'+label);cmd=[str(compiler),str(source),str(b),'--compact']+(['--opt'] if opt else[])
 build=subprocess.run(cmd,capture_output=True,text=True);(D/('build-'+label+'.log')).write_text(build.stdout+build.stderr);assert build.returncode==0
 subprocess.run(['codesign','-s','-',str(b)],check=True,capture_output=True)
 for name,records in scenarios:
  oracle=Oracle();wanted=[oracle.event(r) for r in records];blob=b''.join(struct.pack('<8Q',*r) for r in records)
  x=subprocess.run([str(b)],input=blob,capture_output=True,timeout=5);assert x.returncode==0 and len(x.stdout)==48*len(records),(label,name,x.returncode,len(x.stdout))
  got=list(struct.iter_unpack('<6Q',x.stdout));assert got==wanted,(label,name,next((i,a,c) for i,(a,c) in enumerate(zip(got,wanted)) if a!=c))
  for state in got:
   assert state[2]<=8 and (state[1]!=0 or state[2:4]==(0,0)),'owner invariant'
  rows.append({'build':label,'scenario':name,'records':len(records),'passed':True,'inputSHA256':hashlib.sha256(blob).hexdigest(),'outputSHA256':hashlib.sha256(x.stdout).hexdigest()})
 # Exact stream cap and truncation are separately executed, not generated claims.
 cap=[evt(0,ttl=100)]+[evt(4,t=i) for i in range(511)];raw=b''.join(struct.pack('<8Q',*r) for r in cap)
 for name,data,code,outputlen in [('exact512',raw,0,512*48),('record513',raw+struct.pack('<8Q',*evt(4,t=512)),2,512*48),('truncated',raw[:17],2,0)]:
  x=subprocess.run([str(b)],input=data,capture_output=True,timeout=5);assert (x.returncode,len(x.stdout))==(code,outputlen),(label,name,x.returncode,len(x.stdout))
  rows.append({'build':label,'scenario':name,'passed':True,'exit':x.returncode,'outputBytes':len(x.stdout)})
# Independent named invariants from explicit scenarios, outside reference equality.
o=Oracle();states=[o.event(r) for r in scenarios[0][1]];assert states[1][3]==0x112233 and states[2][1:4]==(2,2,0xaabb) and states[3][1]==2 and states[-1][1:4]==(0,0,0)
o=Oracle();states=[o.event(r) for r in scenarios[1][1]];assert states[2][0]==6 and states[2][1]==1 and states[5][0]==10 and states[5][1:4]==(0,0,0)
report={'passed':True,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'compilerSHA256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'scenariosPerBuild':len(scenarios),'eventChecksPerBuild':sum(len(r) for _,r in scenarios),'streamControlsPerBuild':3,'rows':rows,'scope':'Actual AppleSilicon nativeRF2 stdin/stdout single-slot state model; no network, cryptography, authentication, multi-process crash safety or measured speed advantage'}
(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print('Native RF2 checks:',report['eventChecksPerBuild'],'events per build; two builds; six stream controls')
