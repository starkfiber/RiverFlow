"""Actual shared-key image and owned-mapping failure checks. Disposable local keys only."""
from pathlib import Path
import os,subprocess,hashlib,hmac,struct,random,tempfile,json,time,platform
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_AUTH_VM_DIR',R/'output/mappings-0.21-qualified'));C=B/'rf2c-self';E=B/'rf2-guest';D=R/'artifacts/mappings-0.21'/('verify-'+str(time.time_ns()));D.mkdir(parents=True);rows=[];rng=random.Random(211113)
def image(code,key,entry=0,maxms=100,fields=None):
 words=[int.from_bytes(b'RF2A021\0','little'),len(code),entry,1,0,0,65536,81920,16384,965,7,maxms,0,0]
 if fields:
  for i,v in fields.items():words[i]=v
 msg=struct.pack('<14Q',*words)+hashlib.sha256(key).digest()[:16]+code;return msg+hmac.digest(key,msg,'sha256')
def call(path,key,ms=10,a=19,b=23,cancel=0):
 q=subprocess.run([E,path,key,str(ms),str(a),str(b),str(cancel)],capture_output=True,timeout=5);assert len(q.stdout)==80,(q.returncode,q.stderr,q.stdout);v=struct.unpack('<10Q',q.stdout);r={'exit':q.returncode,'reason':v[0],'value':v[1],'data':v[2],'runTicks':v[3],'budgetTicks':v[4],'frequency':v[5],'status':v[6],'loadedBytes':v[8]};rows.append(r);return r
add=struct.pack('<3I',0x8b010000,0xf9000040,0xd4000022);loop=struct.pack('<I',0x14000000)
with tempfile.TemporaryDirectory(prefix='rf2-guest-test-')as td:
 d=Path(td);key=d/'key';key2=d/'key2';k=os.urandom(32);k2=os.urandom(32);key.write_bytes(k);key2.write_bytes(k2);key.chmod(0o600);key2.chmod(0o600);good=d/'good';good.write_bytes(image(add,k));spin=d/'loop';spin.write_bytes(image(loop,k))
 for _ in range(18):
  a,b=rng.randrange(2**32),rng.randrange(2**32);x=call(good,key,a=a,b=b);assert x['exit']==0 and x['reason']==1 and x['value']==x['data']==a+b,x
 for ms in [1,5,20]:
  for _ in range(3):
   x=call(spin,key,ms);assert x['exit']==0 and x['reason']==2 and x['runTicks']>=x['budgetTicks']/2,x
 for _ in range(4):
  x=call(spin,key,cancel=1);assert x['exit']==0 and x['reason']==0 and x['data']==0,x
 x=call(good,key2);assert x['exit']==1 and x['status']!=0 and x['reason']==0
 # Every byte of the MAC, selected code bytes and every header word are independently corrupted.
 base=image(add,k);refusals=0
 for pos in [*range(len(base)-32,len(base)),0,8,16,24,32,40,48,56,64,72,80,88,96,104,112,128,132,136]:
  raw=bytearray(base);raw[pos]^=1;f=d/'corrupt';f.write_bytes(raw);x=call(f,key);assert x['exit']==1 and x['status']!=0 and x['reason']==0,x;refusals+=1
 # Correct MAC does not bypass boot policy or ISA validation.
 for fields in [{6:131072},{7:98304},{8:32768},{9:0},{10:0},{11:0},{11:1001},{12:1},{13:1},{2:1},{3:2},{4:1}]:
  f=d/'valid-mac-wrong-policy';f.write_bytes(image(add,k,fields=fields));x=call(f,key);assert x['exit']==1 and x['reason']==0;refusals+=1
 f=d/'forbidden';f.write_bytes(image(struct.pack('<I',0xd51be31f),k));assert call(f,key)['status']==1007;refusals+=1
 f=d/'hvc-zero';f.write_bytes(image(struct.pack('<I',0xd4000002),k));assert call(f,key)['status']==1007;refusals+=1
 f=d/'time-limit';f.write_bytes(image(add,k,maxms=1));assert call(f,key,2)['status']==1016;refusals+=1
 for raw in [base[:127],base[:-1],base+b'x',base+b'\0'*5000]:
  f=d/'length';f.write_bytes(raw);assert call(f,key)['exit']==1;refusals+=1
 link=d/'link';link.symlink_to(good);assert call(link,key)['exit']==1;refusals+=1
 fifo=d/'fifo';os.mkfifo(fifo);assert call(fifo,key)['exit']==1;refusals+=1
 for n in [0,31,33]:
  badkey=d/'badkey';badkey.write_bytes(os.urandom(n));badkey.chmod(0o600);assert call(good,badkey)['exit']==1;refusals+=1
 key.chmod(0o644);assert call(good,key)['exit']==1;key.chmod(0o600);refusals+=1
 keylink=d/'keylink';keylink.symlink_to(key);assert call(good,keylink)['exit']==1;refusals+=1
 keyfifo=d/'keyfifo';os.mkfifo(keyfifo,0o600);assert call(good,keyfifo)['exit']==1;refusals+=1
 # Native signer and independent Python verification; existing output must survive unchanged.
 nativekey=d/'native-key';assert subprocess.run([E,'keygen',nativekey],capture_output=True).returncode==0;assert len(nativekey.read_bytes())==32 and nativekey.stat().st_mode&0o777==0o600
 signed=d/'native-signed';assert subprocess.run([E,'seal',R/'examples/vm-runner/add.rf2g',nativekey,signed],capture_output=True).returncode==0
 blob=signed.read_bytes();assert hmac.compare_digest(blob[-32:],hmac.digest(nativekey.read_bytes(),blob[:-32],'sha256'));assert call(signed,nativekey)['value']==42
 assert subprocess.run([E,'seal',R/'examples/vm-runner/add.rf2g',nativekey,signed],capture_output=True).returncode==1 and signed.read_bytes()==blob
 # Replay is deliberately allowed; do not claim anti-rollback from authentication.
 assert call(good,key)['exit']==0 and call(good,key)['exit']==0
H='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\nresource Machine(IO,vm)\nresource CPU(IO,vcpu)\nresource Pages(IO,mapping)\n'
main='''fn main(argc,argv)
 let tag=0
 let value=0
 handle work()
 ok answer
  set value=answer
 err cause
  set tag=1
  set value=cause
 end
 handle again()
 ok yes
 err no
  return 99
 end
 let out=buffer("observation",16)
 do store64(out,tag)
 do store64(out+8,value)
 do write(1,out,16)
 return 0
end
fn again():IO
 own vm=Machine()
 own pages=Pages(vm,65536,16384,3)
 return ok(0)
end
'''
cases=[]
def case(name,body,expected=(0,0),admit=True):
 source=D/(name+'.rf2');source.write_text(H+'fn work():IO\n'+body+'\nend\n'+main);observed=[]
 for opts in [[],['--opt']]:
  exe=D/(name+('-opt'if opts else'-plain'));p=subprocess.run([C,source,exe,*opts],capture_output=True,timeout=15)
  if not admit:assert p.returncode==1 and not exe.exists(),(name,p.stderr);observed.append(p.stderr.decode().strip());continue
  assert p.returncode==0,(name,p.stderr);subprocess.run(['/usr/bin/codesign','-s','-','--entitlements',R/'examples/hypervisor/entitlements.plist',exe],check=True,capture_output=True);q=subprocess.run([exe],capture_output=True,timeout=5);assert q.returncode==0,(name,q.returncode,q.stderr);v=struct.unpack('<2Q',q.stdout)
  if expected=='nonzero':assert v[0]==1 and v[1]!=0,(name,v)
  else:assert v==expected,(name,v,expected)
  observed.append(list(v))
 cases.append({'name':name,'admitted':admit,'observed':observed})
base=' own vm=Machine()\n own p=Pages(vm,65536,16384,3)\n'
case('ordinary-cleanup',base+' return ok(0)')
case('primary-error',base+' return err(42)',(1,42))
for name,arg in [('alignment','vm,65537,16384,3'),('size-zero','vm,65536,0,3'),('size-large','vm,65536,1064960,3'),('permissions','vm,65536,16384,7')]:case(name,' own vm=Machine()\n own p=Pages('+arg+')\n return ok(0)',(1,22))
case('map-overlap',base+' own second=Pages(vm,65536,16384,3)\n return ok(0)','nonzero')
case('copy',base+' let alias=p\n return ok(0)',admit=False)
case('raw-escape',base+' do syscall6(73,p,16384,0,0,0,0)\n return ok(0)',admit=False)
case('parent-release',base+' handle release(vm)\n ok x\n err e\n end\n return ok(0)',admit=False)
case('live-cpu-release',base+' own cpu=CPU(vm)\n handle release(p)\n ok x\n err e\n end\n return ok(0)',admit=False)
case('live-cpu-write',base+' own cpu=CPU(vm)\n handle mapping_store32(p,0,42)\n ok x\n err e\n end\n return ok(0)',admit=False)
# A skipped release must not fool runtime parent/CPU guards.
conditional=base+' own cpu=CPU(vm)\n if 0\n  handle release(cpu)\n  ok x\n  err e\n  end\n end\n'
case('conditional-release-guard',conditional+' handle release(p)\n ok y\n err e2\n  return err(e2)\n end\n return ok(0)',(1,16))
case('conditional-write-guard',conditional+' handle mapping_store32(p,0,42)\n ok y\n err e2\n  return err(e2)\n end\n return ok(0)',(1,16))
case('late-mapping',conditional+' own other=Pages(vm,81920,16384,3)\n return ok(0)',(1,16))
case('compat-unmap-guard',base+' handle vm_unmap_owned(vm,65536,16384)\n ok x\n err e\n  return err(e)\n end\n return ok(0)',(1,9))
case('read-range',base+' handle mapping_read64(p,16384)\n ok x\n  return ok(x)\n err e\n  return err(e)\n end\n return err(99)',(1,22))
case('write-range',base+' handle mapping_store32(p,16384,42)\n ok x\n err e\n  return err(e)\n end\n return ok(0)',(1,22))
case('write-value',base+' handle mapping_store32(p,0,4294967296)\n ok x\n err e\n  return err(e)\n end\n return ok(0)',(1,22))
case('last-word',base+' handle mapping_store32(p,16380,42)\n ok x\n err e\n  return err(e)\n end\n handle mapping_read64(p,16376)\n ok y\n  return ok(y)\n err e2\n  return err(e2)\n end\n return err(99)',(0,42<<32))
# Raw interference is outside ownership; primary error must still survive failed unmap cleanup.
case('raw-destroy-primary',base+' do platform_call("Hypervisor","hv_vm_destroy")\n return err(42)',(1,42))
case('raw-unmap-idempotent',base+' do platform_call("Hypervisor","hv_vm_unmap",65536,16384)\n return ok(0)',(0,0))
case('raw-destroy-cleanup',base+' do platform_call("Hypervisor","hv_vm_destroy")\n return ok(0)','nonzero')
report={'passed':True,'edition':'0.21-dev','host':platform.platform(),'seed':211113,'imageObservations':rows,'authenticatedGuestRuns':sum(x['exit']==0 for x in rows),'imageRefusals':refusals,'mappingCases':cases,'nativeSignerPythonHmacVerified':True,'replayAllowedVerified':True,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'runnerSHA256':hashlib.sha256(E.read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256((R/'examples/evidence-contract/guest.rf2').read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limits':['Shared-key HMAC, not public signatures, measured boot attestation or anti-rollback','Fixed bounded boot ABI and admitted ARM64 instructions; no ELF/Linux/devices','Raw syscalls/API interference, fatal traps/signals remain outside ownership; failed guest unmap intentionally retains host memory until process reclamation','Single local Mac; no universal speed, AI-token, energy or hardware novelty claim']};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'report':str(D/'report.json'),'guestRuns':report['authenticatedGuestRuns'],'imageRefusals':refusals,'mappingCases':len(cases)}))
