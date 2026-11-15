"""Cross-function ownership qualification. Native execution; injected faults are labelled."""
from pathlib import Path
import hashlib,json,os,random,shutil,struct,subprocess,tempfile
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_FUNCTION_OWNER_COMPILER']).resolve()
D=Path(tempfile.mkdtemp(prefix='owned-functions-',dir=R/'artifacts'))
ROWS=[];SERIAL=0;BINDING=0
H='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext Title(IO,64)\ncollection Numbers(IO,64)\nrecord Packet(name:own Title,values:own Numbers,id:u64)\nresult Made(own Packet,u64)\nresult TextMade(own Title,u64)\nresult NumbersMade(own Numbers,u64)\n'

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

FACTORY='fn factory(n):Made\n own p=Packet(Title(),Numbers(),n)\n'+handle('text_append(p.name,0xb85)')+handle('collection_push(p.values,n+7)')+' return ok(move(p))\nend\n'
FORWARD='fn forward(own p:Packet,n):Made\n'+handle('collection_push(p.values,n)')+' return ok(move(p))\nend\n'

def owned(expr,name,kind,body,error='return err(error)'):
 global BINDING
 BINDING+=1;err='error'+str(BINDING)
 return ' handle '+expr+'\n ok own '+name+':'+kind+'\n'+''.join('  '+line+'\n'for line in body.splitlines())+' err '+err+'\n'+''.join('  '+line.replace('error',err)+'\n'for line in error.splitlines())+' end\n'

for opt in (False,True):
 body=owned('factory(5)','p','Packet','if p.id!=5\n return err(71)\nend\n'+handle('text_get(p.name,0)','if $v!=0xb85\n return err(72)\nend')+handle('collection_get(p.values,0)','if $v!=12\n return err(73)\nend'))+' return ok(0)'
 execute('callee-storage-does-not-escape',wrap(body,FACTORY),opt)
 body=owned('factory(5)','p','Packet',owned('forward(move(p),19)','q','Packet',handle('collection_get(q.values,1)','if $v!=19\n return err(74)\nend'))) + ' own after=Packet(Title(),Numbers(),3)\n'+handle('text_append(after.name,65)')+' return ok(0)'
 execute('receive-modify-return-and-local-after-handler',wrap(body,FACTORY+FORWARD),opt)
 for kind,ctor,result,api,value in [('Title','Title()','TextMade','text',0x1f600),('Numbers','Numbers()','NumbersMade','collection',123)]:
  extra=f'fn leaf(n):{result}\n own x={ctor}\n'+handle(f'{api}_'+('append'if api=='text'else'push')+'(x,n)')+' return ok(move(x))\nend\n'
  extra+=f'fn pass(own x:{kind}):{result}\n return ok(move(x))\nend\n'
  body=owned(f'leaf({value})','x',kind,owned('pass(move(x))','y',kind,handle(f'{api}_get(y,0)',f'if $v!={value}\n return err(75)\nend')))+' return ok(0)'
  execute('primitive-return-and-transfer-'+kind,wrap(body,extra),opt)
 # 3,000 dynamic frame handoffs, both success and explicit failure, without stack escape.
 extra=FACTORY+FORWARD+'fn maybe(n):Made\n if n&1\n  return err(77)\n end\n'+owned('factory(n)','p','Packet','return ok(move(p))')+' return err(99)\nend\n'
 body=' let n=0\n let successes=0\n let failures=0\n while n<3000\n'+owned('maybe(n)','value','Packet','if value.id!=n\n return err(76)\nend\n'+owned('forward(move(value),n+1)','again','Packet',handle('collection_get(again.values,1)','if $v!=n+1\n return err(77)\nend'))+'set successes=successes+1','if error!=77\n return err(78)\nend\nset failures=failures+1')+'  set n=n+1\n end\n return ok((successes!=1500)|(failures!=1500))'
 execute('repeated-success-failure-handler-cleanup',wrap(body,extra),opt)
 # A consuming function owns its arguments on either success or failure.
 consume='fn consume(own a:Title,own b:Numbers,n):IO\n'+handle('text_get(a,0)','if $v!=65\n return err(81)\nend')+handle('collection_get(b,0)','if $v!=19\n return err(82)\nend')+' if n\n  return err(77)\n end\n return ok(0)\nend\n'
 for primary in (False,True):
  body=' own p=Packet(Title(),Numbers(),7)\n'+handle('text_append(p.name,65)')+handle('collection_push(p.values,19)')+handle('consume(move(p.name),move(p.values),'+str(int(primary))+')','return ok(0)'if not primary else'return err(83)','return ok($e!=77)'if primary else'return err($e)')+' return err(84)'
  execute('multiple-field-inputs-'+str(primary),wrap(body,consume),opt)
 # Input owner reception must not disturb subsequent local cleanup registration.
 extra='fn local_after(own x:Title):IO\n own another=Title()\n'+handle('text_append(another,66)')+handle('text_get(x,0)','return ok($v!=65)')+' return err(79)\nend\n'
 body=' own x=Title()\n'+handle('text_append(x,65)')+handle('local_after(move(x))','return ok($v)')+' return err(80)'
 execute('parameter-before-local-cleanup',wrap(body,extra),opt)
 # ABI: x8 must be set after scalar argument calls and handle eight registers correctly.
 extra=FACTORY+'fn scalar(n)\n return n+1\nend\nfn eight(a,b,c,d,e,f,g,h):Made\n'+owned('factory(a+b+c+d+e+f+g+h)','p','Packet','return ok(move(p))')+' return err(90)\nend\n'
 body=owned('eight(scalar(0),scalar(1),scalar(2),scalar(3),scalar(4),scalar(5),scalar(6),scalar(7))','p','Packet','if p.id!=36\n return err(91)\nend')+' return ok(0)'
 execute('eight-scalar-args-after-call-clobber',wrap(body,extra),opt)
 # Refusals must produce no executable; all source remains statically checked.
 invalid=[
 ('use-after-input-move',FACTORY+FORWARD,' own p=Packet(Title(),Numbers(),1)\n'+owned('forward(move(p),1)','q','Packet','')+' return ok(p.id)','local used before initialization'),
 ('copy-returned-owner',FACTORY,owned('factory(1)','q','Packet','let alias=q')+' return ok(0)','aggregate is not a value'),
 ('returned-arm-escape',FACTORY,owned('factory(1)','q','Packet','')+' return ok(q.id)','local used before initialization'),
 ('missing-explicit-input-move',FORWARD,' own p=Packet(Title(),Numbers(),1)\n'+owned('forward(p,1)','q','Packet','')+' return ok(0)','expected: move'),
 ('borrowed-parameter-move','fn borrow(t:Title):TextMade\n return ok(move(t))\nend\n',' return ok(0)','borrow cannot escape'),
 ('wrong-return-type','fn wrong():TextMade\n own x=Numbers()\n return ok(move(x))\nend\n',' return ok(0)','owned result move type mismatch'),
 ('wrong-input-type','fn take(own x:Title):IO\n return ok(0)\nend\n',' own x=Numbers()\n'+handle('take(move(x))')+' return ok(0)','owned argument type mismatch'),
 ('return-without-move','fn wrong():TextMade\n own x=Title()\n return ok(x)\nend\n',' return ok(0)','expected: move'),
 ('discard-owner-result',FACTORY,' do factory(1)\n return ok(0)','owned call requires explicit'),
 ('plain-result-arm',FACTORY,' handle factory(1)\n ok p\n err e\n  return err(e)\n end\n return ok(0)','owned call requires explicit'),
 ('partial-aggregate-return','fn bad():Made\n own p=Packet(Title(),Numbers(),1)\n own x=move(p.name)\n return ok(move(p))\nend\n',' return ok(0)','transferred aggregate contains moved field'),
 ('borrow-plus-owned-param','fn bad(t:Title,own n:Numbers):IO\n return ok(0)\nend\n',' return ok(0)','owned and borrowed parameters cannot mix'),
 ('untyped-owned-param','fn bad(own n):IO\n return ok(0)\nend\n',' return ok(0)','owned parameter requires nominal annotation'),
 ('scalar-owned-param','fn bad(own n:u64):IO\n return ok(0)\nend\n',' return ok(0)','owned parameter cannot be scalar'),
 ('unannotated-consuming-function','fn bad(own n:Numbers)\n return 0\nend\n',' return ok(0)','owned parameter requires compatible result'),
 ('repeated-owned-argument','fn both(own a:Title,own b:Title):IO\n return ok(0)\nend\n',' own x=Title()\n'+handle('both(move(x),move(x))')+' return ok(0)','local used before initialization'),
 ('result-not-declared-owned','result Nope(Packet,u64)\n',' return ok(0)','result payload requires scalar record'),
 ('moved-parent-field','fn take(own p:Packet):IO\n return ok(0)\nend\n',' own p=Packet(Title(),Numbers(),1)\n'+handle('take(move(p))')+handle('text_get(p.name,0)')+' return ok(0)','local used before initialization'),
 ]
 for name,extra,body,message in invalid:build(name,wrap(body,extra),opt,refuse=message)
 print('owned function mode',opt,'functional/refusal controls passed',flush=True)

# In-process mapping observations and disposable fault images are separate controls.
PROBES='fn pointer_text(t:Title)\n return 0\nend\nfn pointer_numbers(n:Numbers)\n return 0\nend\n'
for opt in (False,True):
 producer='fn observed_factory():Made\n own p=Packet(Title(),Numbers(),7)\n'+handle('text_append(p.name,65)')+handle('collection_push(p.values,19)')+' do store64(buffer("saved",24),pointer_text(p.name))\n do store64(buffer("saved",24)+8,pointer_numbers(p.values))\n return ok(move(p))\nend\n'
 for early in (False,True):
  body=owned('observed_factory()','p','Packet',('return ok(0)'if early else''))+' return ok(0)'
  main='fn main(argc,argv)\n handle work()\n ok result\n err cause\n  return 90\n end\n let i=0\n while i<2\n  let p=load64(buffer("saved",24)+i*8)\n  if p==0\n   return 94\n  end\n  if syscall6(74,p,1,3,0,0,0)!=-12\n   return 95+i\n  end\n  set i=i+1\n end\n return 0\nend\n'
  src=H+PROBES+producer+'fn work():IO\n'+body+'\nend\n'+main
  original=build('returned-owner-cleanup-'+str(early),src,opt);check('observer no-patch control',call([original]).returncode==94)
  patched=original.with_name(original.name+'-observe');receipt=pointer_probe(original,patched,['pointer_text','pointer_numbers']);q=call([patched]);check('returned owner actually retired '+str(early)+' '+str(opt),q.returncode==0,dict(exit=q.returncode,instrumentation=receipt))
 # Failed drop at the success-arm boundary must clean peers and retry on function exit.
 body=owned('observed_factory()','p','Packet','')+' return ok(0)'
 main='fn main(argc,argv)\n handle work()\n ok unexpected\n  return 89\n err cause\n  if cause!=65548\n   return 90\n  end\n end\n let i=0\n while i<2\n  if syscall6(74,load64(buffer("saved",24)+i*8),1,3,0,0,0)!=-12\n   return 91+i\n  end\n  set i=i+1\n end\n return 0\nend\n'
 src=H+PROBES+thunk(73)+producer+'fn work():IO\n'+body+'\nend\n'+main
 original=build('arm-cleanup-failure',src,opt);observed=original.with_name(original.name+'-observe');r1=pointer_probe(original,observed,['pointer_text','pointer_numbers']);shutil.copy2(str(original)+'.functions',str(observed)+'.functions');check('arm cleanup no-fault control',call([observed]).returncode==89)
 patched=original.with_name(original.name+'-fault');r2=fault(observed,patched,'__rf2heap_drop',73,True);q=call([patched]);check('arm cleanup error peers and retry '+str(opt),q.returncode==0,dict(exit=q.returncode,probe=r1,fault=r2))
 # A producer that moved its result can still fail while dropping a separate local.
 # The caller must dispose the undeliverable result. The failed callee-local drop
 # retains a mapping until process exit, as in the existing cleanup contract.
 producer=producer.replace(' return ok(move(p))',' own spare=Title()\n'+handle('text_append(spare,66)')+' do store64(buffer("saved",24)+16,pointer_text(spare))\n return ok(move(p))')
 body=owned('observed_factory()','p','Packet','return err(88)','if error!=65548\n return err(87)\nend')+' return ok(0)'
 main='fn main(argc,argv)\n handle work()\n ok result\n err cause\n  return 90\n end\n let i=0\n while i<2\n  if syscall6(74,load64(buffer("saved",24)+i*8),1,3,0,0,0)!=-12\n   return 91+i\n  end\n  set i=i+1\n end\n let retained=load64(buffer("saved",24)+16)\n if syscall6(74,retained,1,3,0,0,0)!=0\n  return 93\n end\n return syscall6(73,retained,128,0,0,0,0)!=0\nend\n'
 src=H+PROBES+thunk(73)+producer+'fn work():IO\n'+body+'\nend\n'+main
 original=build('undeliverable-result',src,opt);observed=original.with_name(original.name+'-observe');r1=pointer_probe(original,observed,['pointer_text','pointer_numbers']);shutil.copy2(str(original)+'.functions',str(observed)+'.functions');check('undeliverable no-fault control',call([observed]).returncode==90)
 patched=original.with_name(original.name+'-fault');r2=fault(observed,patched,'__rf2heap_drop',73,True);q=call([patched]);check('undeliverable result disposed '+str(opt),q.returncode==0,dict(exit=q.returncode,probe=r1,fault=r2,limitation='Failed callee-local unmap remains until exit; test explicitly retires observed mapping.'))

# Actual Unicode/number document pipeline: loader returns an owner, renderer consumes it.
app=D/'app';(app/'lib').mkdir(parents=True)
for src,dst in [(R/'experiments/owned-functions/examples/batch-pipeline.flow',app/'main.flow'),(R/'experiments/owned-functions/examples/lib/batch.flow',app/'lib/batch.flow'),(R/'examples/collection-tools/lib/numbers.rf2',app/'lib/numbers.rf2'),(R/'examples/collection-tools/lib/output.rf2',app/'lib/output.rf2')]:shutil.copy2(src,dst)
rng=random.Random(43151126)
for opt in (False,True):
 exe=app/('program-opt'if opt else'program-default');q=call([C,app/'main.flow',exe,*(['--opt']if opt else[])]);check('pipeline app compile '+str(opt),q.returncode==0,(q.stdout+q.stderr).decode(errors='replace'));call(['/usr/bin/codesign','-s','-',exe]).check_returncode()
 for i in range(140):
  label=['தமிழ் 😀','', 'quote " slash \\ new\n','e\u0301','👩\u200d🔬','a'*256][i%6]
  if i>=100:label=''.join(chr(rng.choice([rng.randrange(1,0xd800),rng.randrange(0xe000,0x110000)]))for _ in range(rng.randrange(60)))
  values=[rng.randrange(100000)for _ in range(rng.randrange(120))];q=call([exe,label],input=','.join(map(str,values)).encode());expected=dict(label=label,characters=len(label),count=len(values),sum=sum(values),revision=1)
  check('pipeline JSON '+str(opt)+' '+str(i),q.returncode==0 and json.loads(q.stdout)==expected,dict(exit=q.returncode,expected=expected,stdout=q.stdout.decode(errors='replace')[:100]))
 for label,values in [('a'*257,b'1'),('valid',b'1,,2'),('valid',b'18446744073709551615,1')]:
  q=call([exe,label],input=values);check('pipeline rejects '+str(opt)+' '+str(len(label)),q.returncode==2 and q.stdout==b'')
 for malformed in (b'\xed\xa0\x80',b'\xc0\xaf',b'\xf4\x90\x80\x80',b'\xe2\x82',b'\x80'):
  q=call([os.fsencode(exe),malformed],input=b'1');check('pipeline invalid UTF8 '+str(opt)+' '+malformed.hex(),q.returncode==2 and q.stdout==b'')
 q=call([exe,'valid'],input=b'1',preexec_fn=lambda:os.close(1));check('pipeline closed output '+str(opt),q.returncode==2)

(D/'report.json').write_text(json.dumps({'checks':len(ROWS),'compilerSHA256':sha(C),'results':ROWS},indent=2)+'\n')
print(json.dumps({'checks':len(ROWS),'report':str(D/'report.json')}))
