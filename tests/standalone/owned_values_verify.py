"""Native owned aggregate/text controls. Faults patch disposable test images only."""
from pathlib import Path
import hashlib,json,os,random,shutil,struct,subprocess,tempfile
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_OWNED_COMPILER']).resolve()
D=Path(tempfile.mkdtemp(prefix='owned-values-',dir=R/'artifacts'))
ROWS=[];SERIAL=0;BINDING=0
H='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext Title(IO,64)\ncollection Numbers(IO,64)\nrecord Packet(name:own Title,values:own Numbers,id:u64)\n'

def check(name,ok,detail=None):
 ROWS.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:
  (D/'FAILED.json').write_text(json.dumps(ROWS,indent=2)+'\n');raise AssertionError((name,detail))

def call(args,**kw):return subprocess.run([os.fspath(a) if isinstance(a,Path) else a for a in args],capture_output=True,timeout=20,**kw)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def handle(expr,body='',error='return err(e)'):
 global BINDING
 BINDING+=1;n=str(BINDING)
 # Explicit placeholders avoid collisions with user-authored variable names.
 return ' handle '+expr+'\n ok v'+n+'\n'+''.join('  '+line.replace('$v','v'+n)+'\n'for line in body.splitlines())+' err e'+n+'\n'+''.join('  '+line.replace('$e','e'+n)+'\n'for line in error.replace('err(e)','err($e)').splitlines())+' end\n'

def wrap(body,extra='',header=H):
 return header+extra+'fn work():IO\n'+body+'\nend\nfn main(argc,argv)\n handle work()\n ok value\n  return value\n err cause\n  return cause\n end\n return 201\nend\n'

def build(name,source,opt,refuse=None):
 global SERIAL
 SERIAL+=1;p=D/f'{SERIAL:03}-{name}.flow';p.write_text(source);exe=p.with_suffix('')
 q=call([C,p,exe,'--compact','--functions',*(['--opt']if opt else[])])
 diagnostic=(q.stdout+q.stderr).decode(errors='replace')
 if refuse:
  check(f'{name} refusal {opt}',q.returncode!=0 and refuse in diagnostic,diagnostic[:500]);check(name+' no output',not exe.exists());return None
 check(f'{name} compile {opt}',q.returncode==0,diagnostic[:500])
 call(['/usr/bin/codesign','-s','-',exe]).check_returncode()
 return exe

def execute(name,src,opt,expected=0):
 exe=build(name,src,opt);q=call([exe]);check(f'{name} execution {opt}',q.returncode==expected,dict(exit=q.returncode,stdout=q.stdout.decode(errors='replace')[:200],stderr=q.stderr.decode(errors='replace')[:200]));return exe

def ranges(exe):
 data=exe.read_bytes();pos=32;base=None
 for _ in range(struct.unpack_from('<I',data,16)[0]):
  cmd,size=struct.unpack_from('<II',data,pos)
  if cmd==0x80000028:base=struct.unpack_from('<Q',data,pos+8)[0]
  pos+=size
 assert base is not None
 result={}
 for line in Path(str(exe)+'.functions').read_text().splitlines():
  f=line.split()
  if f and f[0]=='F':result[f[1]]=(base+int(f[2]),int(f[3]))
 return result

def pointer_probe(exe,out,functions):
 data=bytearray(exe.read_bytes());entries=ranges(exe);changes=[]
 for name in functions:
  offset,size=entries[name];assert size>=8
  original=bytes(data[offset:offset+8]);replacement=struct.pack('<II',0xf9400400,0xd65f03c0)
  data[offset:offset+8]=replacement;changes.append(dict(function=name,offset=offset,original=original.hex(),replacement=replacement.hex()))
 out.write_bytes(data);out.chmod(0o700);call(['/usr/bin/codesign','-s','-','--force',out]).check_returncode()
 return dict(kind='test-only descriptor data-address observation; no source API exposes it',changes=changes,inputSHA256=sha(exe),outputSHA256=sha(out))

def fault(exe,out,function,number,once):
 data=exe.read_bytes();start,size=ranges(exe)[function]
 sites=[i for i in range(start,start+size-3)if data[i:i+4]==struct.pack('<I',3556773889)]
 assert len(sites)=={'__rf2heap_grow':2,'__rf2heap_drop':1,'__rf2heap_pending':1}[function]
 offset=sites[1 if function=='__rf2heap_grow' and number==73 else 0]
 assert data[offset+4:offset+12]==struct.pack('<II',0x54000043,0xcb0003e0)
 if once:
  assert struct.unpack_from('<I',data,start)[0]==2847898621
  target=ranges(exe)['fault_once'][0];delta=target-offset;assert delta%4==0 and -(1<<27)<=delta<(1<<27)
  replacement=struct.pack('<III',0x94000000|((delta//4)&0x3ffffff),0xd503201f,0xd503201f)
 else:replacement=struct.pack('<III',0x92800000|(11<<5),0xd503201f,0xd503201f)
 out.write_bytes(data[:offset]+replacement+data[offset+12:]);out.chmod(0o700);call(['/usr/bin/codesign','-s','-','--force',out]).check_returncode()
 return dict(kind='controlled test-image syscall result; not real host OOM/kernel failure',function=function,syscall=number,once=once,offset=offset,original=data[offset:offset+12].hex(),replacement=replacement.hex(),inputSHA256=sha(exe),outputSHA256=sha(out))

def thunk(number):return 'fn fault_once(a,b,c,d,e,f)\n let c1=buffer("fault_counter",8)\n if load64(c1)==0\n  do store64(c1,1)\n  return -12\n end\n return syscall6('+str(number)+',a,b,c,d,e,f)\nend\n'

for opt in (False,True):
 # Unicode values are code points, with surrogate and out-of-range admission refused.
 valid=[0,1,31,32,127,128,2047,2048,0xb85,0xd7ff,0xe000,0xffff,0x10000,0x1f600,0x10ffff]
 body=' own p=Packet(Title(),Numbers(),7)\n'
 for i,value in enumerate(valid):body+=handle(f'text_append(p.name,{value})',f'if $v!={i+1}\n return err(71)\nend')
 for value in (0xd800,0xdfff,0x110000,(1<<64)-1):body+=handle(f'text_append(p.name,{value})','return err(72)','if $e!=22\n return err(73)\nend')
 body+=f' if p.name.length!={len(valid)}\n  return err(74)\n end\n'
 body+=handle('collection_push(p.values,91)')+' own moved=move(p)\n set moved.id=9\n'
 for i,value in enumerate(valid):body+=handle(f'text_get(moved.name,{i})',f'if $v!={value}\n return err(75)\nend')
 body+=handle('collection_get(moved.values,0)','if $v!=91\n return err(76)\nend')+' return ok(moved.id!=9)'
 execute('unicode-and-aggregate-move',wrap(body),opt)
 # Field extraction transfers responsibility; the parent keeps other fields.
 body=' own p=Packet(Title(),Numbers(),7)\n'+handle('text_append(p.name,65)')+' own extracted=move(p.name)\n'+handle('text_get(extracted,0)','if $v!=65\n return err(70)\nend')+handle('collection_push(p.values,88)')+' return ok(p.values.length!=1)'
 execute('move-field-out',wrap(body),opt)
 # Entire aggregate transfer and cleanup work with maximum registration budget.
 header='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext T(IO,4)\nrecord Many('+','.join(f'f{i}:own T'for i in range(8))+')\n'
 body=' own a=Many('+','.join('T()'for _ in range(8))+')\n'+handle('text_append(a.f7,0x1f600)')+' own b=move(a)\n'+handle('text_get(b.f7,0)','return ok($v!=0x1f600)')+' return ok(3)'
 execute('sixteen-cleanup-registrations',wrap(body,header=header),opt)
 # Released child state transfers without duplicating or resurrecting ownership.
 body=' own p=Packet(Title(),Numbers(),1)\n'+handle('release(p.name)')+' own q=move(p)\n'+handle('text_append(q.name,65)','return err(71)','if $e!=9\n return err(72)\nend')+' return ok(0)'
 execute('released-field-stays-released',wrap(body),opt)
 invalid={
  'copy-root':(' own p=Packet(Title(),Numbers(),1)\n let copy=p\n return ok(0)','aggregate is not a value'),
  'use-moved-root':(' own p=Packet(Title(),Numbers(),1)\n own q=move(p)\n return ok(p.id)','used before initialization'),
  'use-moved-field':(' own p=Packet(Title(),Numbers(),1)\n own q=move(p.name)\n'+handle('text_append(p.name,65)')+' return ok(0)','owned field was moved'),
  'duplicate-field-move':(' own name=Title()\n own p=Packet(move(name),Numbers(),1)\n own twice=move(name)\n return ok(0)','used before initialization'),
  'wrong-text-api':(' own p=Packet(Title(),Numbers(),1)\n'+handle('collection_push(p.name,65)')+' return ok(0)','nominal collection or text owner required'),
  'wrong-collection-api':(' own p=Packet(Title(),Numbers(),1)\n'+handle('text_append(p.values,65)')+' return ok(0)','nominal collection or text owner required'),
  'field-rebind':(' own p=Packet(Title(),Numbers(),1)\n set p.name=0\n return ok(0)','nested child binding is immutable'),
  'read-moved-field':(' own p=Packet(Title(),Numbers(),1)\n own t=move(p.name)\n return ok(p.name.length)','owned field was moved'),
  'descriptor-field-write':(' own p=Packet(Title(),Numbers(),1)\n set p.name.length=9\n return ok(0)','nested path requires plain borrowed record'),
  'raw-escape':(' own p=Packet(Title(),Numbers(),1)\n return ok(load64(p.name))','record passed to raw intrinsic'),
  'move-partial-root':(' own p=Packet(Title(),Numbers(),1)\n own t=move(p.name)\n own q=move(p)\n return ok(0)','aggregate contains moved field'),
 }
 for name,(body,message)in invalid.items():build(name,wrap(body),opt,message)
 # Type/layout exclusions stay explicit instead of admitting pointer-shaped owners.
 bad_types={
  'different-results':(H+'result Other(u64,u64)\ncollection Foreign(Other,4)\nrecord Bad(a:own Title,b:own Foreign)\nfn main(argc,argv)\n return 0\nend\n','aggregate result types differ'),
  'owned-file-field':(H+'resource File(IO)\nrecord Bad(file:own File)\nfn main(argc,argv)\n return 0\nend\n','owned field requires collection or text'),
  'unowned-text-field':(H+'record Bad(name:Title)\nfn main(argc,argv)\n return 0\nend\n','nested field requires plain borrowed record'),
  'borrow-aggregate':(H+'fn bad(p:Packet)\n return 0\nend\nfn main(argc,argv)\n return 0\nend\n','result/view parameters unsupported'),
  'return-aggregate':(H+'result Bad(Packet,u64)\nfn main(argc,argv)\n return 0\nend\n','result payload requires scalar record'),
  'borrow-release':(H+'fn bad(t:Title):IO\n'+handle('release(t)')+' return ok(0)\nend\nfn main(argc,argv)\n return 0\nend\n','borrowed collection cannot be released'),
  'wrong-constructor':(wrap(' own p=Packet(Numbers(),Numbers(),1)\n return ok(0)'),'collection constructor mismatch'),
  'too-long-text':('profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext Huge(IO,65537)\nfn main(argc,argv)\n return 0\nend\n','vector limit bound'),
 }
 for name,(source,message)in bad_types.items():build(name,source,opt,message)
 header='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext T(IO,4)\nrecord Many('+','.join(f'f{i}:own T'for i in range(9))+')\n'
 build('seventeen-cleanup-refusal',wrap(' own a=Many('+','.join('T()'for _ in range(9))+')\n own b=move(a)\n return ok(0)',header=header),opt,'aggregate cleanup count bound')
 # Partial construction: the first field moved, the second source is runtime-closed.
 probe='fn pointer_text(t:Title)\n return 0\nend\nfn pointer_numbers(n:Numbers)\n return 0\nend\n'
 body=' own name=Title()\n'+handle('text_append(name,65)')+' do store64(buffer("saved",16),pointer_text(name))\n own numbers=Numbers()\n'+handle('release(numbers)')+' own p=Packet(move(name),move(numbers),1)\n return ok(99)'
 source=H+probe+'fn partial():IO\n'+body+'\nend\nfn main(argc,argv)\n handle partial()\n ok impossible\n  return 91\n err cause\n  if cause!=9\n   return 92\n  end\n end\n if load64(buffer("saved",16))==0\n  return 94\n end\n if syscall6(74,load64(buffer("saved",16)),1,3,0,0,0)!=-12\n  return 93\n end\n return 0\nend\n'
 original=build('partial-construction',source,opt);check('partial probe zero-address control '+str(opt),call([original]).returncode==94);patched=original.with_name(original.name+'-observe');receipt=pointer_probe(original,patched,['pointer_text']);q=call([patched]);check('partial constructor retires acquired child '+str(opt),q.returncode==0,{'exit':q.returncode,'instrumentation':receipt})
 # Verify successful return actually retires both mappings in-process after two moves.
 body=' own p=Packet(Title(),Numbers(),1)\n'+handle('text_append(p.name,65)')+handle('collection_push(p.values,99)')+' do store64(buffer("saved",16),pointer_text(p.name))\n do store64(buffer("saved",16)+8,pointer_numbers(p.values))\n own q=move(p)\n own z=move(q)\n return ok(0)'
 source=H+probe+'fn made():IO\n'+body+'\nend\nfn main(argc,argv)\n handle made()\n ok done\n err failure\n  return 90\n end\n let i=0\n while i<2\n  if load64(buffer("saved",16)+i*8)==0\n   return 94\n  end\n  if syscall6(74,load64(buffer("saved",16)+i*8),1,3,0,0,0)!=-12\n   return 91+i\n  end\n  set i=i+1\n end\n return 0\nend\n'
 original=build('cleanup-after-moves',source,opt);check('cleanup probe zero-address control '+str(opt),call([original]).returncode==94);patched=original.with_name(original.name+'-observe');receipt=pointer_probe(original,patched,['pointer_text','pointer_numbers']);q=call([patched]);check('both child mappings retired '+str(opt),q.returncode==0,{'exit':q.returncode,'instrumentation':receipt})
 # Allocation fault preserves an empty text and retry works.
 body=' own p=Packet(Title(),Numbers(),1)\n let failed=0\n'+handle('text_append(p.name,65)','', 'set failed=1\nif ($e!=12)|(p.name.length!=0)|(p.name.capacity!=0)\n return err(70)\nend')+handle('text_append(p.name,66)')+' return ok(failed==0)'
 original=execute('mmap-retry-control',wrap(body,thunk(197)),opt,1);patched=original.with_name(original.name+'-fault');receipt=fault(original,patched,'__rf2heap_grow',197,True);q=call([patched]);check('text allocation failure and retry '+str(opt),q.returncode==0,{'exit':q.returncode,'fault':receipt})
 # Retirement failure retains active and pending mappings across aggregate move.
 body=' own p=Packet(Title(),Numbers(),1)\n let i=0\n while i<16\n'+handle('text_append(p.name,65)')+'  set i=i+1\n end\n let failed=0\n'+handle('text_reserve(p.name,64)','', 'set failed=1\nif ($e!=12)|(p.name.capacity!=16)|(p.name.length!=16)\n return err(71)\nend')+' own q=move(p)\n'+handle('text_reserve(q.name,64)')+handle('text_get(q.name,0)','if $v!=65\n return err(72)\nend')+' return ok(failed==0)'
 original=execute('retirement-move-control',wrap(body,thunk(73)),opt,1);patched=original.with_name(original.name+'-fault');receipt=fault(original,patched,'__rf2heap_grow',73,True);q=call([patched]);check('pending retirement survives aggregate move '+str(opt),q.returncode==0,{'exit':q.returncode,'fault':receipt})
 # Explicit release failure retains a child for retry after whole-aggregate transfer.
 body=' own p=Packet(Title(),Numbers(),1)\n'+handle('text_append(p.name,65)')+' let failed=0\n'+handle('release(p.name)','', 'set failed=1\nif $e!=12\n return err(70)\nend')+' if failed==0\n  return ok(1)\n end\n own q=move(p)\n'+handle('release(q.name)')+' return ok(failed==0)'
 original=execute('release-move-control',wrap(body,thunk(73)),opt,1);patched=original.with_name(original.name+'-fault');receipt=fault(original,patched,'__rf2heap_drop',73,True);q=call([patched]);check('release failure survives move and retries '+str(opt),q.returncode==0,{'exit':q.returncode,'fault':receipt})
 for primary in (False,True):
  body=' own p=Packet(Title(),Numbers(),1)\n'+handle('text_append(p.name,65)')+handle('collection_push(p.values,99)')+(' return err(77)'if primary else' return ok(0)')
  source=wrap(body).replace('  return cause\n','  return cause=='+str(77 if primary else 65548)+'\n')
  original=execute('automatic-cleanup-control-'+str(primary),source,opt,1 if primary else 0);patched=original.with_name(original.name+'-fault');receipt=fault(original,patched,'__rf2heap_drop',73,False);q=call([patched]);check('cleanup error precedence '+str(primary)+' '+str(opt),q.returncode==1,{'exit':q.returncode,'fault':receipt})
 # A failed first child drop must not suppress cleanup of its peer.
 body=' own p=Packet(Title(),Numbers(),1)\n'+handle('text_append(p.name,65)')+handle('collection_push(p.values,99)')+' do store64(buffer("saved",16),pointer_text(p.name))\n do store64(buffer("saved",16)+8,pointer_numbers(p.values))\n if (load64(buffer("saved",16))==0)|(load64(buffer("saved",16)+8)==0)\n  return err(97)\n end\n if (syscall6(74,load64(buffer("saved",16)),1,3,0,0,0)!=0)|(syscall6(74,load64(buffer("saved",16)+8),1,3,0,0,0)!=0)\n  return err(98)\n end\n return ok(0)'
 source=H+probe+thunk(73)+'fn made():IO\n'+body+'\nend\nfn main(argc,argv)\n handle made()\n ok unexpected\n  return 89\n err cause\n  if cause!=65548\n   return 90\n  end\n end\n if syscall6(74,load64(buffer("saved",16)),1,3,0,0,0)!=-12\n  return 91\n end\n if syscall6(74,load64(buffer("saved",16)+8),1,3,0,0,0)!=0\n  return 92\n end\n if syscall6(73,load64(buffer("saved",16)+8),128,0,0,0,0)!=0\n  return 93\n end\n return 0\nend\n'
 original=build('peer-cleanup-after-failure',source,opt);observed=original.with_name(original.name+'-observe');probe_receipt=pointer_probe(original,observed,['pointer_text','pointer_numbers']);shutil.copy2(str(original)+'.functions',str(observed)+'.functions');check('peer-cleanup no-fault control '+str(opt),call([observed]).returncode==89);patched=original.with_name(original.name+'-fault');fault_receipt=fault(observed,patched,'__rf2heap_drop',73,True);q=call([patched]);check('peer cleaned despite first retirement failure '+str(opt),q.returncode==0,{'exit':q.returncode,'probe':probe_receipt,'fault':fault_receipt})
 print('owned core mode',opt,'passed',flush=True)

# The actual app snapshots reviewed modules and compares emitted JSON, including Unicode.
app=D/'app';(app/'lib').mkdir(parents=True)
for src,dst in [(R/'experiments/owned-values/examples/owned-batch.flow',app/'main.flow'),(R/'experiments/owned-values/examples/lib/batch.flow',app/'lib/batch.flow'),(R/'examples/collection-tools/lib/numbers.rf2',app/'lib/numbers.rf2'),(R/'examples/collection-tools/lib/output.rf2',app/'lib/output.rf2')]:shutil.copy2(src,dst)
rng=random.Random(42151126)
for opt in (False,True):
 exe=app/('program-opt'if opt else'program-default');q=call([C,app/'main.flow',exe,*(['--opt']if opt else[])]);check('real app compile '+str(opt),q.returncode==0,(q.stdout+q.stderr).decode(errors='replace'));clean_image=exe.read_bytes();call(['/usr/bin/codesign','-s','-',exe]).check_returncode()
 labels=['தமிழ் test 😀','', 'quote " slash \\ newline\n', '\u0001 control','e\u0301', '👩\u200d🔬', 'a'*256]
 for i in range(140):
  label=labels[i%len(labels)]
  if i>=100:
   points=[rng.choice([rng.randrange(1,0xd800),rng.randrange(0xe000,0x110000)])for _ in range(rng.randrange(60))];label=''.join(map(chr,points))
  values=[rng.randrange(100000)for _ in range(rng.randrange(120))]
  q=call([exe,label],input=','.join(map(str,values)).encode());expected={'label':label,'characters':len(label),'count':len(values),'sum':sum(values),'revision':1}
  check('real app JSON '+str(opt)+' '+str(i),q.returncode==0 and json.loads(q.stdout)==expected,{'expected':expected,'exit':q.returncode,'stdout':q.stdout.decode(errors='replace')[:200]})
 for label,values in [('a'*257,b'1'),('valid',b'1,,2'),('valid',b'18446744073709551615,1')]:
  q=call([exe,label],input=values);check('app refusal '+str(opt)+' '+str(len(label)),q.returncode==2 and q.stdout==b'')
 for malformed in (b'\xed\xa0\x80',b'\xc0\xaf',b'\xf4\x90\x80\x80',b'\xe2\x82',b'\x80'):
  q=call([os.fsencode(exe),malformed],input=b'1');check('invalid UTF8 app '+str(opt)+' '+malformed.hex(),q.returncode==2 and q.stdout==b'')
 q=call([exe,'valid'],input=b'1',preexec_fn=lambda:os.close(1));check('app failed output '+str(opt),q.returncode==2)
 # Existing scalar cache reuse must not freeze old owned-type limits or layouts.
 cache=app/('cache-opt'if opt else'cache-default');cache.mkdir(mode=0o700)
 for iteration in (0,1):
  target=app/(f'cached-{opt}-{iteration}');q=call([C,app/'main.flow',target,*(['--opt']if opt else[]),'--reuse-pack',cache]);check(f'owned app pack compile {opt} {iteration}',q.returncode==0,(q.stdout+q.stderr).decode(errors='replace')[:400]);check(f'owned app pack clean equality {opt} {iteration}',target.read_bytes()==clean_image)
 library=app/'lib/batch.flow';original_library=library.read_bytes();library.write_bytes(original_library.replace(b'text BatchLabel(IO,256)',b'text BatchLabel(IO,4)'))
 changed=app/('changed-clean-'+str(opt));q=call([C,app/'main.flow',changed,*(['--opt']if opt else[])]);check('changed owned limit compile '+str(opt),q.returncode==0,(q.stdout+q.stderr).decode(errors='replace')[:400]);expected_image=changed.read_bytes()
 target=app/('changed-cached-'+str(opt));q=call([C,app/'main.flow',target,*(['--opt']if opt else[]),'--reuse-pack',cache]);check('changed owned limit cached compile '+str(opt),q.returncode==0,(q.stdout+q.stderr).decode(errors='replace')[:400]);check('changed owned limit clean equality '+str(opt),target.read_bytes()==expected_image);call(['/usr/bin/codesign','-s','-',target]).check_returncode();q=call([target,'12345'],input=b'1');check('new scalar text limit enforced after cache reuse '+str(opt),q.returncode==2 and q.stdout==b'');library.write_bytes(original_library)

report={'schema':'rf2.owned-values.acceptance.v1','allPassed':all(r['passed']for r in ROWS),'compilerSHA256':sha(C),'controllerSHA256':sha(__file__),'checks':ROWS,'appSources':{str(p.relative_to(app)):sha(p)for p in app.rglob('*')if p.is_file()and p.suffix in('.flow','.rf2')},'scope':'Isolated Mac candidate; bounded owned Unicode scalar text and u64 collection fields, local moves and ordinary cleanup. Test-only injected syscall results and pointer probes; no actual host OOM, raw-pointer safety, cross-function owner return, hardware or speed/token claim.'}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(ROWS),'report':str(D/'report.json')}),flush=True)
