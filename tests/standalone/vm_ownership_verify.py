"""Native typed VM lifetimes, bounded guest images and in-VMM timer cancellation.
No guest is allowed to change timer/system registers. External timeout is only a failing-test guard.
"""
from pathlib import Path
import os,subprocess,struct,hashlib,json,time,random,platform
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_VM_DIR',R/'output/ownership-0.20-final'));D=R/'artifacts/ownership-0.20'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
C=B/'rf2c-self';E=B/'rf2-vm-runner';MAGIC=int.from_bytes(b'RF2G020\0','little');rows=[];rng=random.Random(201113)
def image(name,ops,entry=0,isa=1,flags=0,reserved=0):
 p=D/(name+'.rf2g');p.write_bytes(struct.pack('<6Q',MAGIC,len(ops)*4,entry,isa,flags,reserved)+struct.pack('<'+'I'*len(ops),*ops));return p
def run(p,ms=10,a=19,b=23,cancel=0):
 start=time.monotonic_ns();q=subprocess.run([E,p,str(ms),str(a),str(b),str(cancel)],capture_output=True,timeout=5);wall=time.monotonic_ns()-start
 assert len(q.stdout)==80,(q.returncode,q.stdout,q.stderr)
 values=dict(zip(['reason','value','data','elapsedTicks','budgetTicks','ticksPerSecond','status','reserved','loadedBytes','entry'],struct.unpack('<10Q',q.stdout)))
 row={'image':p.name,'ms':ms,'a':a,'b':b,'cancel':cancel,'processExit':q.returncode,'wallNs':wall,**values};rows.append(row);return row
add=image('add',[0x8b010000,0xf9000040,0xd4000002]);loop=image('loop',[0x14000000]);noploop=image('nop-loop',[0xd503201f,0x17ffffff]);repeat=image('repeated-add',[0x8b010000]*7+[0xf9000040,0xd4000002]);entry=image('entry',[0xd503201f,0x8b010000,0xf9000040,0xd4000002],4)
for i in range(24):
 a,b=rng.randrange(2**32),rng.randrange(2**32)
 for p,factor in [(add,1),(repeat,7),(entry,1)]:
  x=run(p,100,a,b);assert x['processExit']==0 and x['status']==0 and x['reason']==1 and x['data']==a+factor*b and x['value']==x['data'],x
# Actual hardware timer returns from the loop; do not count timeout termination as cancellation.
for ms in [1,2,5,10,20,50]:
 for p in [loop,noploop]:
  for _ in range(3):
   x=run(p,ms);assert x['processExit']==0 and x['reason']==2 and x['status']==0 and x['data']==0,x
   # Generous lower tolerance admits API setup; no hard upper real-time guarantee.
   assert x['elapsedTicks']>=x['budgetTicks']*0.5,x
for p in [loop,add]:
 for _ in range(6):
  x=run(p,100,cancel=1);assert x['processExit']==0 and x['reason']==0 and x['data']==0 and x['status']==0,x
bad=[]
def refuse(p):
 x=run(p);assert x['processExit']==1 and x['status']!=0 and x['reason']==0 and x['loadedBytes']==0,x;bad.append({'file':p.name,'status':x['status']})
for name,ops in [('timer-disable',[0xd51be31f]),('svc',[0xd4000001]),('eret',[0xd69f03e0]),('other-store',[0xf9000000]),('branch-out',[0x14000001]),('branch-before',[0x17ffffff]),('unknown',[0xffffffff]),('zero',[]),('oversize',[0xd503201f]*1025)]:refuse(image(name,ops))
for p in [image('entry-oob',[0xd4000002],4),image('entry-align',[0xd4000002],1),image('wrong-isa',[0xd4000002],isa=2),image('flags',[0xd4000002],flags=1),image('reserved',[0xd4000002],reserved=1)]:refuse(p)
raw=add.read_bytes()
for i in [0,1,7,8,15,24,47,48,49,59]:
 p=D/f'truncated-{i}.rf2g';p.write_bytes(raw[:i]);refuse(p)
for name,data in [('magic',b'INVALID!'+raw[8:]),('trailing',raw+b'\0'),('huge',raw+b'\0'*5000)]:
 p=D/(name+'.rf2g');p.write_bytes(data);refuse(p)
link=D/'linked.rf2g';link.symlink_to(add);refuse(link)
fifo=D/'fifo';os.mkfifo(fifo);refuse(fifo);refuse(D/'missing');refuse(D)
# Every branch encoding in a small independent reference window must agree with admission.
branch_cases=0
for pc in range(4):
 for delta in range(-6,7):
  ops=[0xd503201f]*4;ops[pc]=0x14000000|(delta&0x3ffffff)
  p=image(f'branch-{pc}-{delta}',ops)
  x=run(p,1,cancel=1);valid=0<=pc+delta<4
  assert (x['status']==0)==valid,(pc,delta,x);branch_cases+=1
H='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\nresource Machine(IO,vm)\nresource CPU(IO,vcpu)\n'
main='''fn main(argc,argv)
 let answer=9
 let observed_error=0
 handle work()
 ok value
  set answer=value
 err cause
  set answer=1
  set observed_error=cause
 end
 handle again()
 ok recreated
 err failed
  return 99
 end
 let out=buffer("lifetime_observation",8)
 do store64(out,observed_error)
 do write(1,out,8)
 return answer
end
fn again():IO
 own m=Machine()
 return ok(0)
end
'''
def compile_case(name,body,valid=True,extra='',expected=0,error_value=None):
 p=D/(name+'.rf2');p.write_text(H+'fn work():IO\n'+body+'\nend\n'+extra+main)
 observations=[]
 for opt in [[],['--opt']]:
  e=D/(name+('-opt' if opt else '-plain'));q=subprocess.run([C,p,e,*opt],capture_output=True,timeout=15)
  if not valid:
   assert q.returncode==1 and not e.exists(),(name,opt,q.returncode,q.stderr);observations.append(q.stderr.decode().strip());continue
  assert q.returncode==0,(name,opt,q.stderr)
  subprocess.run(['/usr/bin/codesign','-s','-','--entitlements',R/'examples/hypervisor/entitlements.plist',e],check=True,capture_output=True)
  q=subprocess.run([e],capture_output=True,timeout=5);assert q.returncode==expected,(name,opt,q.returncode,q.stderr);cause=struct.unpack('<Q',q.stdout)[0];assert error_value is None or cause==error_value,(name,cause,error_value)
  if name=='cleanup-error':assert cause>=65536,(name,cause)
  observations.append({'exit':q.returncode,'error':cause})
 return {'name':name,'admitted':valid,'observations':observations}
cases=[]
base=' own m=Machine()\n own c=CPU(m)\n'
for name,body in [('ordinary-return',base+' return ok(0)'),('primary-error',base+' return err(42)'),('partial-acquisition',' own m=Machine()\n own second=Machine()\n return ok(0)')]:cases.append(compile_case(name,body,expected=0 if name=='ordinary-return' else 1,error_value=42 if name=='primary-error' else None))
# Test cleanup errors, then reacquire before process exit. Raw calls deliberately violate ownership.
cases.append(compile_case('cleanup-error',' own m=Machine()\n do platform_call("Hypervisor","hv_vm_destroy")\n return ok(0)',expected=1))
cases.append(compile_case('cleanup-preserves-primary',' own m=Machine()\n do platform_call("Hypervisor","hv_vm_destroy")\n return err(42)',expected=1,error_value=42))
for name,body in [('copy',base+' let alias=m\n return ok(0)'),('return-owner',base+' return ok(m)'),('raw-owner',base+' do platform_call("Hypervisor","hv_vcpu_run",c)\n return ok(0)'),('wrong-parent',' own c=CPU(1)\n return ok(0)'),('wrong-operation',base+' handle vm_unmap_owned(c,65536,16384)\n ok a\n err e\n end\n return ok(0)'),('parent-before-child',base+' handle release(m)\n ok a\n err e\n end\n return ok(0)'),('use-after-release',base+' handle release(c)\n ok a\n err e\n end\n handle vcpu_run_owned(c)\n ok b\n err f\n end\n return ok(0)'),('let-owner',' let m=Machine()\n return ok(0)'),('escaped-owner',' own m=Machine()\n if 1\n  own c=CPU(m)\n end\n return ok(0)')]:cases.append(compile_case(name,body,False))
# 0.19 compiler refuses typed VM source; original 0.19 raw VMM still runs with new compiler (separate regression).
old=R/'output/foundation-0.19-regression/rf2c-self';q=subprocess.run([old,R/'examples/vm-runner/main.rf2',D/'old-refusal'],capture_output=True);assert q.returncode==1 and not(D/'old-refusal').exists()
report={'passed':True,'edition':'0.20-dev','host':platform.platform(),'seed':201113,'actualGuestRuns':120,'guestObservations':rows,'rejectedImages':bad,'branchAdmissionCases':branch_cases,'ownershipCases':cases,'old019RefusesNewSource':True,'sourceSHA256':hashlib.sha256((R/'examples/vm-runner/main.rf2').read_bytes()).hexdigest(),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'runnerSHA256':hashlib.sha256(E.read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limits':['One Apple Silicon physical Mac; Apple owns virtualization','Cancellation is a virtual-timer exit for the validated instruction subset; no arbitrary ARM64 or Linux guest guarantee','No hard real-time upper bound: host scheduling may delay return','Raw trusted platform calls can defeat ownership, and mapping buffers are still manually managed','No new Core/MCP execution authority, speed, energy or token claim']}
report['actualGuestRuns']=sum(x['status']==0 for x in rows);(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'report':str(D/'report.json'),'actualGuestRuns':report['actualGuestRuns'],'rejectedImages':len(bad),'ownershipCases':len(cases)}))
