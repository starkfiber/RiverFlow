"""Independent bounded heap-collection ownership, alias and failure controls.

Native local developer controller. Faults, when injected, patch owned test binaries
and model a failing syscall; they are not observations of actual kernel OOM.
"""
from pathlib import Path
import hashlib,json,os,struct,subprocess,time,re
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
D=R/'artifacts/sprint-033'/('heap-redteam-'+str(time.time_ns()));D.mkdir(parents=True)
ROWS=[];SERIAL=0;HANDLE_SERIAL=0;MASK=(1<<64)-1
H='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ncollection Numbers(IO,128)\n'

def wrap(body,extra='',limit=128):
 return H.replace('Numbers(IO,128)',f'Numbers(IO,{limit})')+extra+'fn work():IO\n'+body+'\nend\nfn main(argc,argv)\n handle work()\n ok v\n  return v\n err e\n  return 200\n end\n return 201\nend\n'

def handle(call,binding='value',body='',error='return err(cause)'):
 global HANDLE_SERIAL
 HANDLE_SERIAL+=1;ok_name=binding+'_'+str(HANDLE_SERIAL);err_name='cause_'+str(HANDLE_SERIAL)
 body=re.sub(r'\b'+re.escape(binding)+r'\b',ok_name,body);error=re.sub(r'\bcause\b',err_name,error)
 return ' handle '+call+'\n ok '+ok_name+'\n'+''.join('  '+l+'\n'for l in body.splitlines())+' err '+err_name+'\n  '+error+'\n end\n'

def build(name,source,opt,expected=True,mapping=False):
 global SERIAL
 SERIAL+=1;out=D/(f'{SERIAL:03}-'+name+('-opt'if opt else'-default'));p=out.with_suffix('.rf2');p.write_text(source)
 q=subprocess.run([C,p,out,'--compact',*(['--opt']if opt else[]),*(['--functions']if mapping else[])],capture_output=True,timeout=30,env={'PATH':'/nonexistent'})
 if expected:
  assert q.returncode==0,(name,q.returncode,q.stderr.decode(errors='replace'))
  subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True)
 else:assert q.returncode!=0 and not out.exists(),(name,q.returncode,q.stderr)
 return out,q

def execute(name,source,opt,exit=0,stderr=None):
 out,_=build(name,source,opt);q=subprocess.run([out],capture_output=True,timeout=10,env={'PATH':'/nonexistent'})
 assert q.returncode==exit and not q.stdout,(name,opt,q.returncode,q.stdout,q.stderr)
 if stderr is not None:assert q.stderr==stderr,(name,opt,q.stderr)
 ROWS.append(dict(case=name,optimized=opt,outcome='executed',exit=q.returncode,sourceSHA256=hashlib.sha256(source.encode()).hexdigest(),binarySHA256=hashlib.sha256(out.read_bytes()).hexdigest()))
 return out

def refused(name,source,opt):
 _,q=build(name,source,opt,False);ROWS.append(dict(case=name,optimized=opt,outcome='refused',sourceSHA256=hashlib.sha256(source.encode()).hexdigest(),stderr=q.stderr.decode(errors='replace')[:500]))

def patch_fault(source,out,number,index,expected):
 data=source.read_bytes();needle=struct.pack('<II',0xd2800000|(number<<5)|16,3556773889)
 sites=[i for i in range(len(data)-7)if data[i:i+8]==needle];assert len(sites)==expected,(number,len(sites),expected)
 at=sites[index];words=struct.pack('<II',0xd2800000|(12<<5),0xeb1f03ff)
 out.write_bytes(data[:at]+words+data[at+8:]);out.chmod(0o700);subprocess.run(['/usr/bin/codesign','-s','-','--force',out],capture_output=True,check=True)
 return dict(syscall=number,site=index,offset=at,original=data[at:at+8].hex(),replacement=words.hex(),sourceSHA256=hashlib.sha256(data).hexdigest(),patchedSHA256=hashlib.sha256(out.read_bytes()).hexdigest(),kind='controlled failing syscall model, not real OOM')

def patch_pointer_probe(source,out):
 data=source.read_bytes();pos=32;base=None
 for _ in range(struct.unpack_from('<I',data,16)[0]):
  cmd,size=struct.unpack_from('<II',data,pos)
  if cmd==0x80000028:base=struct.unpack_from('<Q',data,pos+8)[0]
  pos+=size
 assert base is not None,'LC_MAIN entry absent'
 rows=Path(str(source)+'.functions').read_text().splitlines();fields=next(x.split()for x in rows if x.startswith('F heap_test_pointer '));offset=base+int(fields[2]);assert int(fields[3])>=8
 # Test-only descriptor pointer extraction; no such RF2 capability is exposed.
 replacement=struct.pack('<II',0xf9400400,0xd65f03c0)
 asm=D/'pointer-probe.s';obj=D/'pointer-probe.o';asm.write_text('.text\n.globl _probe\n_probe:\n ldr x0,[x0,#8]\n ret\n')
 subprocess.run(['/usr/bin/clang','-target','arm64-apple-macos14','-c',asm,'-o',obj],capture_output=True,check=True)
 raw=obj.read_bytes();pos=32;actual=None
 for _ in range(struct.unpack_from('<I',raw,16)[0]):
  cmd,size=struct.unpack_from('<II',raw,pos)
  if cmd==0x19:
   section=pos+72
   for _ in range(struct.unpack_from('<I',raw,pos+64)[0]):
    if raw[section:section+16].split(b'\0')[0]==b'__text':
     count=struct.unpack_from('<Q',raw,section+40)[0];start=struct.unpack_from('<I',raw,section+48)[0];actual=raw[start:start+count]
    section+=80
  pos+=size
 assert actual==replacement,(actual,replacement)
 out.write_bytes(data[:offset]+replacement+data[offset+8:]);out.chmod(0o700);subprocess.run(['/usr/bin/codesign','-s','-','--force',out],capture_output=True,check=True)
 return dict(kind='test-only descriptor pointer probe',offset=offset,original=data[offset:offset+8].hex(),replacement=replacement.hex(),independentAssemblerMatches=True,sourceSHA256=hashlib.sha256(data).hexdigest(),patchedSHA256=hashlib.sha256(out.read_bytes()).hexdigest())

def function_ranges(source):
 data=source.read_bytes();pos=32;base=None
 for _ in range(struct.unpack_from('<I',data,16)[0]):
  cmd,size=struct.unpack_from('<II',data,pos)
  if cmd==0x80000028:base=struct.unpack_from('<Q',data,pos+8)[0]
  pos+=size
 assert base is not None
 result={}
 for line in Path(str(source)+'.functions').read_text().splitlines():
  fields=line.split()
  if fields and fields[0]=='F':result[fields[1]]=(base+int(fields[2]),int(fields[3]))
 return data,result

def inject_scoped_fault(source,out,function,number,once,thunk_name='fault_once'):
 data,ranges=function_ranges(source);start,size=ranges[function]
 sites=[i for i in range(start,start+size-3)if data[i:i+4]==struct.pack('<I',3556773889)]
 expected={'__rf2heap_grow':2,'__rf2heap_drop':1,'__rf2heap_pending':1}[function];assert len(sites)==expected,(function,sites)
 index=0 if function!='__rf2heap_grow'or number==197 else 1;offset=sites[index]
 assert data[offset+4:offset+12]==struct.pack('<II',0x54000043,0xcb0003e0),'review generic Darwin errno conversion before injection'
 if once:
  assert struct.unpack_from('<I',data,start)[0]==2847898621,'BL injection requires real frame preserving LR'
  target=ranges[thunk_name][0];delta=target-offset;assert delta%4==0 and -(1<<27)<=delta<(1<<27)
  replacement=struct.pack('<III',0x94000000|((delta//4)&0x3ffffff),0xd503201f,0xd503201f)
 else:replacement=struct.pack('<III',0x92800000|(11<<5),0xd503201f,0xd503201f)
 # Replace SVC/BCC/NEG as a whole with a canonical syscall-result model.
 # The thunk returns -errno/normal result, so conversion must not run twice.
 out.write_bytes(data[:offset]+replacement+data[offset+12:]);out.chmod(0o700);subprocess.run(['/usr/bin/codesign','-s','-','--force',out],capture_output=True,check=True)
 return dict(kind='one-shot canonical syscall-result injection'if once else'permanent canonical syscall-result injection',function=function,number=number,site=index,offset=offset,original=data[offset:offset+12].hex(),replacement=replacement.hex(),sourceSHA256=hashlib.sha256(data).hexdigest(),patchedSHA256=hashlib.sha256(out.read_bytes()).hexdigest(),limits='Injected owned-test syscall wrapper result, not actual OOM; BL used only in framed runtime functions')

def fault_thunk(number,name='fault_once'):
 counter=name+'_counter'
 return 'fn '+name+'(a,b,c,d,e,f)\n let counter=buffer("'+counter+'",8)\n if load64(counter)==0\n  do store64(counter,1)\n  return -12\n end\n return syscall6('+str(number)+',a,b,c,d,e,f)\nend\n'

def run_fault(name,source,opt,function,number,once):
 original,_=build(name,source,opt,mapping=True);control=subprocess.run([original],capture_output=True,timeout=10,env={'PATH':'/nonexistent'});assert control.returncode==(0 if name.endswith('preserves-primary') else 1),(name,'control',control.returncode,control.stderr);patched=original.with_name(original.name+'-fault')
 receipt=inject_scoped_fault(original,patched,function,number,once)
 q=subprocess.run([patched],capture_output=True,timeout=10,env={'PATH':'/nonexistent'});assert q.returncode==0 and not q.stdout,(name,opt,q.returncode,q.stdout,q.stderr)
 ROWS.append(dict(case=name,optimized=opt,outcome='executed injected own binary',fault=receipt))

def main():
 for opt in [False,True]:
  execute('empty',wrap(' own a=Numbers()\n return ok(a.length|a.capacity|(a.limit!=128))'),opt)
  growth=' own a=Numbers()\n let i=0\n while i<128\n'+handle('collection_push(a,18446744073709551615-i*17)','n','if n!=i+1\n return ok(1)\nend')+'  set i=i+1\n end\n set i=0\n while i<128\n'+handle('collection_get(a,i)','v','if v!=18446744073709551615-i*17\n return ok(2)\nend')+'  set i=i+1\n end\n return ok((a.length!=128)|(a.capacity<128)|(a.capacity>a.limit))'
  execute('multiple-growth-u64-oracle',wrap(growth),opt)
  moved=' own a=Numbers()\n'+handle('collection_push(a,18446744073709551615)','n')+' own b=move(a)\n'+handle('collection_get(b,0)','v','return ok((v!=18446744073709551615)|(b.length!=1))')+' return ok(3)'
  execute('move-populated-owner',wrap(moved),opt)
  execute('move-empty-owner',wrap(' own a=Numbers()\n own b=move(a)\n return ok(b.length|b.capacity)'),opt)
  reserve=' own a=Numbers()\n'+handle('collection_reserve(a,33)','cap','if (cap<33)|(a.length!=0)|(a.capacity!=cap)\n return ok(1)\nend')+handle('collection_push(a,73)','n')+handle('collection_reserve(a,1)','cap2','if cap2<33\n return ok(2)\nend')+handle('collection_get(a,0)','v','return ok((v!=73)|(a.length!=1))')+' return ok(3)'
  execute('reserve-preserves-data-no-shrink',wrap(reserve),opt)
  for call,err in [('collection_reserve(a,18446744073709551615)',22),('collection_get(a,18446744073709551615)',34),('collection_set(a,18446744073709551615,99)',34)]:
   body=' own a=Numbers()\n'+handle('collection_push(a,57)','n')+handle(call,'bad','return ok(1)',f'if cause!={err}\n   return ok(2)\n  end')+handle('collection_get(a,0)','v','return ok((v!=57)|(a.length!=1))')+' return ok(3)'
   execute('bad-request-'+str(err)+'-'+call.split('(')[0],wrap(body),opt)
  full=' own a=Numbers()\n let i=0\n while i<4\n'+handle('collection_push(a,i+10)','n')+'  set i=i+1\n end\n'+handle('collection_push(a,99)','bad','return ok(1)','if cause!=22\n   return ok(2)\n  end')+' return ok((a.length!=4)|(a.capacity>4))'
  execute('maximum-push-does-not-commit',wrap(full,limit=4),opt)
  clear=' own a=Numbers()\n'+handle('collection_push(a,71)','n')+' let cap=a.capacity\n'+handle('collection_clear(a)','v','if a.length!=0\n return ok(1)\nend')+handle('collection_get(a,0)','bad','return ok(2)','if cause!=34\n   return ok(3)\n  end')+' return ok(a.capacity!=cap)'
  execute('clear-preserves-capacity-not-old-length',wrap(clear),opt)
  # Mutable helpers receive a borrow of the descriptor, not a copy of ownership.
  helper='fn append(a:Numbers):IO\n'+handle('collection_push(a,19)','n','return ok(n)')+' return ok(2)\nend\n'
  execute('borrow-helper-mutation',wrap(' own a=Numbers()\n'+handle('append(a)','n','if n!=1\n return ok(1)\nend')+handle('collection_get(a,0)','v','return ok((v!=19)|(a.length!=1))')+' return ok(2)',helper),opt)
  # All scalar arguments may call a mutable helper on the same descriptor.
  reentrant='fn mutate(a:Numbers)\n'+handle('collection_reserve(a,128)','capacity')+handle('collection_clear(a)','cleared')+handle('collection_push(a,51)','n')+' return 73\nend\n'
  # The helper must return scalar, so handle failures terminate the test explicitly.
  reentrant=re.sub(r'return err\(cause_\d+\)','return 199',reentrant)
  rhs=' own a=Numbers()\n'+handle('collection_push(a,11)','first')+handle('collection_push(a,mutate(a))','after','if after!=2\n return ok(1)\nend')+handle('collection_get(a,0)','v0','if v0!=51\n return ok(2)\nend')+handle('collection_get(a,1)','v1','return ok((v1!=73)|(a.length!=2))')+' return ok(3)'
  execute('reentrant-push-reloads-grown-cleared-descriptor',wrap(rhs,reentrant),opt)
  rhsset=' own a=Numbers()\n'+handle('collection_push(a,11)','first')+handle('collection_set(a,0,mutate(a))','assigned')+handle('collection_get(a,0)','value','return ok((value!=73)|(a.length!=1))')+' return ok(3)'
  execute('reentrant-set-reloads-grown-descriptor',wrap(rhsset,reentrant),opt)
  aliases='fn aliases(a:Numbers,b:Numbers):IO\n'+handle('collection_push(a,17)','n')+handle('collection_push(b,19)','m','return ok(m)')+' return ok(199)\nend\n'
  aliasbody=' own a=Numbers()\n'+handle('aliases(a,a)','count','if count!=2\n return ok(1)\nend')+handle('collection_get(a,1)','value','return ok((value!=19)|(a.length!=2))')+' return ok(2)'
  execute('two-sequential-borrows-may-alias',wrap(aliasbody,aliases),opt)
  released=' own a=Numbers()\n'+handle('collection_push(a,73)','n')+handle('release(a)','released')+handle('collection_push(a,99)','bad','return ok(1)','if cause!=9\n   return ok(2)\n  end')+handle('release(a)','bad2','return ok(3)','if cause!=9\n   return ok(4)\n  end')+' return ok(0)'
  execute('successful-release-disarms-all-operations',wrap(released),opt)
  # A property compiled before release in the loop must still check runtime liveness.
  loop=' own a=Numbers()\n let i=0\n while i<2\n  let before=a.limit\n'+handle('release(a)','r')+'  set i=i+1\n end\n return ok(0)'
  execute('released-loop-property-controlled-trap',wrap(loop),opt,exit=2,stderr=b'RF2 bounds\n')
  # Instrument only our typed helper to observe mapping retirement with a same-protection mprotect query.
  probe_helper='fn heap_test_pointer(a:Numbers)\n return 0\nend\n'
  probe_body=' own a=Numbers()\n'+handle('collection_reserve(a,1)','initial')+' let old=heap_test_pointer(a)\n if old==0\n  return ok(201)\n end\n let before=a.capacity\n'+handle('collection_push(a,57)','n')+handle('collection_reserve(a,before+1)','grown')+' let current=heap_test_pointer(a)\n if current==old\n  return ok(1)\n end\n let probe=buffer("mincore_probe",8)\n if syscall6(74,old,1,3,0,0,0)!=-12\n  return ok(2)\n end\n if syscall6(74,current,1,3,0,0,0)!=0\n  return ok(3)\n end\n'+handle('collection_get(a,0)','value','if value!=57\n return ok(4)\nend')+handle('release(a)','released')+' return ok(syscall6(74,current,1,3,0,0,0)!=-12)'
  probe_source=wrap(probe_body,probe_helper)
  original,_=build('mapping-retirement-probe',probe_source,opt,mapping=True)
  q=subprocess.run([original],capture_output=True,timeout=10,env={'PATH':'/nonexistent'});assert q.returncode==201,(q.returncode,q.stderr)
  patched=original.with_name(original.name+'-instrumented');receipt=patch_pointer_probe(original,patched)
  q=subprocess.run([patched],capture_output=True,timeout=10,env={'PATH':'/nonexistent'});assert q.returncode==0 and not q.stdout,(q.returncode,q.stdout,q.stderr)
  ROWS.append(dict(case='actual-relocation-and-retirement-mprotect',optimized=opt,outcome='executed instrumented own binary',instrumentation=receipt))
  # Observe owner cleanup while the process remains alive, not only at exit.
  cleanup_extra='record Observation(pointer:u64)\n'+probe_helper
  cleanup_work='fn cleaned(observation:Observation):IO\n own a=Numbers()\n'+handle('collection_push(a,91)','n')+' set observation.pointer=heap_test_pointer(a)\n own b=move(a)\n return ok(0)\nend\n'
  cleanup_main='fn work():IO\n return ok(0)\nend\nfn main(argc,argv)\n let observation=Observation(0)\n'+handle('cleaned(observation)','done','if observation.pointer==0\n return 201\nend','return 202')+' return syscall6(74,observation.pointer,1,3,0,0,0)!=-12\nend\n'
  cleanup_source=H+cleanup_extra+cleanup_work+cleanup_main
  original,_=build('actual-automatic-cleanup-after-move',cleanup_source,opt,mapping=True)
  control=subprocess.run([original],capture_output=True,timeout=10);assert control.returncode==201,control.stderr
  patched=original.with_name(original.name+'-instrumented');receipt=patch_pointer_probe(original,patched)
  q=subprocess.run([patched],capture_output=True,timeout=10,env={'PATH':'/nonexistent'});assert q.returncode==0 and not q.stdout,(q.returncode,q.stderr)
  ROWS.append(dict(case='actual-automatic-cleanup-after-move',optimized=opt,outcome='in-process retired mapping after callee return',instrumentation=receipt))
  # Growth failure must not publish metadata or discard existing data.
  initial=' own a=Numbers()\n'+handle('collection_reserve(a,1)','unexpected','return ok(1)','if cause!=12\n   return ok(2)\n  end')+' if (a.length!=0)|(a.capacity!=0)\n  return ok(3)\n end\n'+handle('collection_push(a,91)','n')+handle('collection_get(a,0)','v','return ok((v!=91)|(a.length!=1))')+' return ok(4)'
  run_fault('injected-initial-mmap-state-and-retry',wrap(initial,fault_thunk(197)),opt,'__rf2heap_grow',197,True)
  retire=' own a=Numbers()\n'+handle('collection_push(a,71)','n')+' let cap=a.capacity\n'+handle('collection_reserve(a,cap+1)','unexpected','return ok(1)','if cause!=12\n   return ok(2)\n  end')+' if (a.length!=1)|(a.capacity!=cap)\n  return ok(3)\n end\n'+handle('collection_get(a,0)','old','if old!=71\n return ok(4)\nend')+handle('collection_reserve(a,cap+1)','grown','if grown<=cap\n return ok(5)\nend')+handle('collection_get(a,0)','value','return ok((value!=71)|(a.length!=1))')+' return ok(6)'
  run_fault('injected-old-retire-preserves-active-pending-retry',wrap(retire,fault_thunk(73)),opt,'__rf2heap_grow',73,True)
  release=' own a=Numbers()\n'+handle('collection_push(a,71)','n')+' let cap=a.capacity\n'+handle('release(a)','unexpected','return ok(1)','if cause!=12\n   return ok(2)\n  end')+handle('collection_get(a,0)','value','if (value!=71)|(a.length!=1)|(a.capacity!=cap)\n return ok(3)\nend')+handle('release(a)','released')+handle('collection_get(a,0)','unexpected2','return ok(4)','if cause!=9\n   return ok(5)\n  end')+' return ok(0)'
  run_fault('injected-release-failure-ownership-and-retry',wrap(release,fault_thunk(73)),opt,'__rf2heap_drop',73,True)
  pending=' own a=Numbers()\n'+handle('collection_push(a,71)','n')+' let cap=a.capacity\n'+handle('collection_reserve(a,cap+1)','unexpected','return ok(1)','if cause!=12\n   return ok(2)\n  end')+handle('collection_reserve(a,cap+1)','unexpected2','return ok(3)','if cause!=12\n   return ok(4)\n  end')+' if (a.capacity!=cap)|(a.length!=1)\n  return ok(5)\n end\n'+handle('collection_get(a,0)','v','if v!=71\n return ok(6)\nend')+handle('collection_reserve(a,cap+1)','grown','if grown<=cap\n return ok(7)\nend')+handle('collection_get(a,0)','last','return ok((last!=71)|(a.length!=1))')+' return ok(8)'
  pending_src=wrap(pending,fault_thunk(73,'fault_retire_once')+fault_thunk(73,'fault_pending_once'))
  original,_=build('injected-pending-retirement-retry',pending_src,opt,mapping=True)
  control=subprocess.run([original],capture_output=True,timeout=10);assert control.returncode==1
  first=original.with_name(original.name+'-retire-fault');r1=inject_scoped_fault(original,first,'__rf2heap_grow',73,True,'fault_retire_once')
  Path(str(first)+'.functions').write_bytes(Path(str(original)+'.functions').read_bytes())
  final=original.with_name(original.name+'-both-faults');r2=inject_scoped_fault(first,final,'__rf2heap_pending',73,True,'fault_pending_once')
  q=subprocess.run([final],capture_output=True,timeout=10,env={'PATH':'/nonexistent'});assert q.returncode==0 and not q.stdout,(q.returncode,q.stderr)
  ROWS.append(dict(case='injected-pending-cleanup-failure-and-retry',optimized=opt,outcome='active data retained across two errors',faults=[r1,r2]))
  for primary in [False,True]:
   src=H+'fn work():IO\n own a=Numbers()\n'+handle('collection_push(a,71)','n')+(' return err(77)\n'if primary else' return ok(0)\n')+'end\nfn main(argc,argv)\n handle work()\n ok value\n  return 1\n err cause\n  return cause!='+str(77 if primary else 65548)+'\n end\n return 2\nend\n'
   run_fault('injected-cleanup-'+('preserves-primary'if primary else'reports-secondary'),src,opt,'__rf2heap_drop',73,False)
  for name,extra,body in [
   ('private-helper-forgery','fn __rf2heap_op(d,op,a,b,limit)\n return 0\nend\n',' own a=Numbers()\n return ok(0)'),
   ('private-helper-call','',' own a=Numbers()\n do __rf2heap_op(0,0,0,0,0)\n return ok(0)'),
   ('private-type-forgery','record __rf2heap_IO(x:u64)\n',' own a=Numbers()\n return ok(0)')]:refused(name,wrap(body,extra),opt)
  # Every invalid source must refuse before executable creation.
  for name,body in [
   ('owner-copy',' own a=Numbers()\n let b=a\n return ok(0)'),
   ('owner-rebind',' own a=Numbers()\n set a=a\n return ok(0)'),
   ('move-twice',' own a=Numbers()\n own b=move(a)\n own c=move(a)\n return ok(0)'),
   ('source-property-after-move',' own a=Numbers()\n own b=move(a)\n return ok(a.length)'),
   ('source-operation-after-move',' own a=Numbers()\n own b=move(a)\n'+handle('collection_push(a,1)','n')+' return ok(0)'),
   ('raw-owner-pointer',' own a=Numbers()\n do write(1,a,8)\n return ok(0)'),
   ('owner-result-escape',' own a=Numbers()\n return ok(a)'),
   ('owner-pointer-property',' own a=Numbers()\n return ok(a.pointer)'),
   ('move-in-branch',' own a=Numbers()\n if 1\n own b=move(a)\n end\n return ok(0)'),
   ('move-in-loop',' own a=Numbers()\n while 0\n own b=move(a)\n end\n return ok(0)')]:refused(name,wrap(body),opt)
  for operation in ['release(a)','move(a)']:
   if operation.startswith('release'):body=handle(operation,'v','return ok(0)')+' return ok(1)'
   else:body=' own b=move(a)\n return ok(0)'
   src=H+'fn borrowed(a:Numbers):IO\n'+body+'\nend\nfn main(argc,argv)\nreturn 0\nend\n'
   refused('borrow-cannot-'+operation.split('(')[0],src,opt)
 report=dict(passed=True,schema='rf2.heap.ownership.redteam.v1',cases=len(ROWS),rows=ROWS,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits='Finite native local ownership/data/borrow controls. Raw pointer/syscall interference excluded. Fault injections, if present, are explicitly labelled and are not actual OOM. No whole-language memory-safety, concurrency or general allocator guarantee.')
 (D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(ROWS),report=str(D/'report.json'))))
if __name__=='__main__':main()
