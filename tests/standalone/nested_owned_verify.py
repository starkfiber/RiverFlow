"""Cross-function ownership qualification. Native execution; injected faults are labelled."""
from pathlib import Path
import hashlib,json,os,random,shutil,struct,subprocess,tempfile
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_NESTED_OWNER_COMPILER']).resolve()
D=Path(tempfile.mkdtemp(prefix='nested-owned-',dir=R/'artifacts'))
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


N=H+'record Envelope(packet:own Packet,title:own Title,revision:u64)\nresult EnvelopeReady(own Envelope,u64)\n'
ROWS_HEADER='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\nrecord Row(id:u64,a:u64,b:u64,c:u64,d:u64)\nrecord Wrong(id:u64,a:u64,b:u64,c:u64,d:u64)\ncollection Rows(IO,64,Row)\nresult RowsReady(own Rows,u64)\n'
def owner_handle(expr,name,kind,body,error='return err(error)'):
 global BINDING
 BINDING+=1;e='owner_error'+str(BINDING)
 return ' handle '+expr+'\n ok own '+name+':'+kind+'\n'+''.join('  '+x+'\n'for x in body.splitlines())+' err '+e+'\n'+''.join('  '+x.replace('error',e)+'\n'for x in error.splitlines())+' end\n'

for opt in (False,True):
 extra='fn factory():EnvelopeReady\n own e=Envelope(Packet(Title(),Numbers(),7),Title(),1)\n'+handle('text_append(e.packet.name,0xb85)')+handle('collection_push(e.packet.values,55)')+' set e.packet.id=9\n return ok(move(e))\nend\nfn forward(own e:Envelope):EnvelopeReady\n set e.revision=2\n return ok(move(e))\nend\n'
 body=owner_handle('factory()','e','Envelope',owner_handle('forward(move(e))','q','Envelope','if (q.packet.id!=9)|(q.revision!=2)\n return err(71)\nend\n'+handle('text_get(q.packet.name,0)','if $v!=0xb85\n return err(72)\nend')+handle('collection_get(q.packet.values,0)','if $v!=55\n return err(73)\nend')))+' return ok(0)'
 execute('nested-owner-function-handoff',wrap(body,extra,header=N),opt)
 body=' own e=Envelope(Packet(Title(),Numbers(),7),Title(),1)\n'+handle('text_append(e.packet.name,65)')+' own selected=move(e.packet)\n'+handle('text_get(selected.name,0)','if $v!=65\n return err(74)\nend')+handle('text_append(e.title,66)')+' set e.revision=3\n return ok(e.revision!=3)'
 execute('nested-subtree-move-preserves-peer',wrap(body,header=N),opt)
 body=' own e=Envelope(Packet(Title(),Numbers(),7),Title(),1)\n'+handle('text_append(e.packet.name,65)')+' own leaf=move(e.packet.name)\n'+handle('collection_push(e.packet.values,55)')+handle('text_get(leaf,0)','return ok($v!=65)')+' return err(75)'
 execute('deep-leaf-extraction',wrap(body,header=N),opt)
 # All properties and row operations use record counts, despite the word-backed heap.
 body=' own rows=Rows()\n let input=Row(1,2,3,4,5)\n let output=Row(9,9,9,9,9)\n'+handle('records_push(rows,input)','if ($v!=1)|(rows.length!=1)\n return err(71)\nend')+' set input.a=99\n'+handle('records_read(rows,0,output)','if ($v!=5)|(output.a!=2)\n return err(72)\nend')+handle('records_read(rows,1,output)','return err(73)','if ($e!=34)|(output.id!=1)|(output.a!=2)\n return err(74)\nend')+handle('records_set(rows,0,input)')+handle('records_read(rows,0,output)','if output.a!=99\n return err(75)\nend')+handle('records_reserve(rows,64)','if ($v<64)|(rows.capacity<64)|(rows.limit!=64)\n return err(76)\nend')+handle('records_read(rows,0,output)','if output.a!=99\n return err(77)\nend')+handle('records_remove(rows,0)','if ($v!=0)|(rows.length!=0)\n return err(78)\nend')+handle('records_remove(rows,0)','return err(79)','if $e!=34\n return err(80)\nend')+handle('records_push(rows,input)')+handle('records_clear(rows)','if rows.length!=0\n return err(81)\nend')+' own moved=move(rows)\n'+handle('records_push(moved,input)')+handle('release(moved)')+handle('records_push(moved,input)','return err(82)','if $e!=9\n return err(83)\nend')+' return ok(0)'
 execute('structured-row-copy-update-reserve-remove-clear-release',wrap(body,header=ROWS_HEADER),opt)
 extra='fn produce():RowsReady\n own rows=Rows()\n let row=Row(5,6,7,8,9)\n'+handle('records_push(rows,row)')+' return ok(move(rows))\nend\nfn pass(own rows:Rows):RowsReady\n return ok(move(rows))\nend\n'
 body=' let out=Row(0,0,0,0,0)\n'+owner_handle('produce()','rows','Rows',owner_handle('pass(move(rows))','again','Rows',handle('records_read(again,0,out)','if (out.id!=5)|(out.d!=9)\n return err(84)\nend')))+' return ok(0)'
 execute('structured-collection-function-transfer',wrap(body,extra,header=ROWS_HEADER),opt)
 # Saturation and failed mutations leave the existing rows and output intact.
 body=' own rows=Rows()\n let row=Row(1,2,3,4,5)\n let out=Row(9,9,9,9,9)\n let i=0\n while i<64\n  set row.id=i\n'+handle('records_push(rows,row)')+'  set i=i+1\n end\n'+handle('records_push(rows,row)','return err(85)','if ($e!=22)|(rows.length!=64)\n return err(86)\nend')+handle('records_reserve(rows,65)','return err(87)','if $e!=22\n return err(88)\nend')+handle('records_read(rows,63,out)','if out.id!=63\n return err(89)\nend')+handle('records_set(rows,18446744073709551615,row)','return err(90)','if ($e!=34)|(rows.length!=64)\n return err(91)\nend')+' return ok(0)'
 execute('row-limit-and-bounds-no-mutation',wrap(body,header=ROWS_HEADER),opt)
 for width in (1,2,8,16):
  header='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\nrecord Wide('+','.join(f'f{i}:u64'for i in range(width))+')\ncollection Items(IO,4,Wide)\n'
  body=' own items=Items()\n let input=Wide('+','.join(str(i+10)for i in range(width))+')\n let out=Wide('+','.join('0'for _ in range(width))+')\n'+handle('records_push(items,input)')+handle('records_read(items,0,out)','if '+ '|'.join(f'(out.f{i}!={i+10})'for i in range(width))+'\n return err(92)\nend')+' return ok(0)'
  execute('record-width-'+str(width),wrap(body,header=header),opt)
 invalid=[
 ('deep-moved-leaf',N,' own e=Envelope(Packet(Title(),Numbers(),1),Title(),1)\n own leaf=move(e.packet.name)\n'+handle('text_get(e.packet.name,0)')+' return ok(0)','owned field was moved'),
 ('moved-subtree',N,' own e=Envelope(Packet(Title(),Numbers(),1),Title(),1)\n own part=move(e.packet)\n return ok(e.packet.id)','owned field was moved'),
 ('partial-parent-move',N,' own e=Envelope(Packet(Title(),Numbers(),1),Title(),1)\n own leaf=move(e.packet.name)\n own q=move(e)\n return ok(0)','transferred aggregate contains moved field'),
 ('wrong-row',ROWS_HEADER,' own rows=Rows()\n let wrong=Wrong(1,2,3,4,5)\n'+handle('records_push(rows,wrong)')+' return ok(0)','record collection row type mismatch'),
 ('wrong-read-output',ROWS_HEADER,' own rows=Rows()\n let wrong=Wrong(1,2,3,4,5)\n'+handle('records_read(rows,0,wrong)')+' return ok(0)','record collection row type mismatch'),
 ('scalar-op-on-rows',ROWS_HEADER,' own rows=Rows()\n'+handle('collection_get(rows,0)')+' return ok(0)','nominal collection or text owner required'),
 ('raw-row-owner',ROWS_HEADER,' own rows=Rows()\n do load64(rows)\n return ok(0)','record passed to raw intrinsic'),
 ('copy-rows',ROWS_HEADER,' own rows=Rows()\n let copy=rows\n return ok(0)','scalar expression required'),
 ('row-word-overflow','profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\nrecord R(a:u64,b:u64)\ncollection Rows(IO,65536,R)\n',' return ok(0)','record collection word bound'),
 ('borrowed-row-shape','profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\nrecord A(x:u64)\nrecord B(a:A)\ncollection Rows(IO,16,B)\n',' return ok(0)','record collection requires flat scalar row'),
 ('owned-row-shape',N+'collection Rows(IO,16,Envelope)\n',' return ok(0)','record collection requires flat scalar row'),
 ('private-record-helper',ROWS_HEADER,' do __rf2heap_records(0,0,0,0,5,64)\n return ok(0)','reserved compiler collection helper'),
 ]
 for name,header,body,error in invalid:
  if name=='owned-row-shape' and os.environ.get('RF2_OWNED_ROWS_EXTENSION')=='1':
   # 0.46 deliberately admits this declaration. Original 0.44 mode retains refusal.
   # Full consuming/extraction/failure behavior is qualified in owned_rows_verify.py.
   execute('owned-row-shape-now-admitted',wrap(body,header=header),opt)
  else:build(name,wrap(body,header=header),opt,refuse=error)
 print('nested/row mode',opt,'core controls passed',flush=True)

# Deep shape boundaries and failure paths are executed, not inferred from syntax.
for opt in (False,True):
 header='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext T(IO,4)\n'
 for i in range(29):header+='record L'+str(i)+'(child:own '+('T'if i==0 else'L'+str(i-1))+')\n'
 path='deep'+'.child'*29
 body=' own deep='+''.join('L'+str(i)+'('for i in reversed(range(29)))+'T()'+')'*29+'\n'+handle('text_append('+path+',65)')+' own moved=move(deep)\n'+handle('text_get(moved'+'.child'*29+',0)','return ok($v!=65)')+' return err(93)'
 execute('maximum-declared-type-depth',wrap(body,header=header),opt)
 header='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext T(IO,4)\nrecord Many('+','.join('f'+str(i)+':own T'for i in range(16))+')\n'
 # Repeating a large child would exceed the bounded frame even though the type graph is acyclic.
 header+='record TooLarge(a:own Many,b:own Many)\n'
 build('nested-layout-refusal',wrap(' own x=TooLarge(Many('+','.join('T()'for _ in range(16))+'),Many('+','.join('T()'for _ in range(16))+'))\n return ok(0)',header=header),opt,refuse='nested owned layout bound')
 # Failed initial allocation must not publish a partial row or alter the source row.
 body=' own rows=Rows()\n let row=Row(1,2,3,4,5)\n let failed=0\n'+handle('records_push(rows,row)','', 'set failed=1\nif ($e!=12)|(rows.length!=0)|(rows.capacity!=0)|(row.d!=5)\n return err(71)\nend')+handle('records_push(rows,row)','if $v!=2-failed\n return err(72)\nend')+' return ok(failed==0)'
 original=execute('row-allocation-control',wrap(body,thunk(197),header=ROWS_HEADER),opt,1);patched=original.with_name(original.name+'-fault');receipt=fault(original,patched,'__rf2heap_grow',197,True);q=call([patched]);check('row initial allocation retry '+str(opt),q.returncode==0,dict(exit=q.returncode,fault=receipt))
 # Failed growth retirement retains active row contents and count across owner transfer.
 body=' own rows=Rows()\n let row=Row(1,2,3,4,5)\n let out=Row(0,0,0,0,0)\n'+handle('records_push(rows,row)')+' let before=rows.capacity\n let failed=0\n'+handle('records_reserve(rows,before+1)','', 'set failed=1\nif ($e!=12)|(rows.length!=1)|(rows.capacity!=before)\n return err(73)\nend')+' own moved=move(rows)\n'+handle('records_reserve(moved,before+1)')+handle('records_read(moved,0,out)','if (out.id!=1)|(out.d!=5)\n return err(74)\nend')+' return ok(failed==0)'
 original=execute('row-retirement-control',wrap(body,thunk(73),header=ROWS_HEADER),opt,1);patched=original.with_name(original.name+'-fault');receipt=fault(original,patched,'__rf2heap_grow',73,True);q=call([patched]);check('row pending state survives move '+str(opt),q.returncode==0,dict(exit=q.returncode,fault=receipt))
 # Recursive cleanup is observable while the process is still running.
 probes='fn pointer_text(t:Title)\n return 0\nend\nfn pointer_numbers(n:Numbers)\n return 0\nend\n'
 body=' own e=Envelope(Packet(Title(),Numbers(),1),Title(),1)\n'+handle('text_append(e.packet.name,65)')+handle('collection_push(e.packet.values,19)')+handle('text_append(e.title,66)')+' do store64(buffer("saved",24),pointer_text(e.packet.name))\n do store64(buffer("saved",24)+8,pointer_numbers(e.packet.values))\n do store64(buffer("saved",24)+16,pointer_text(e.title))\n own moved=move(e)\n return ok(0)'
 main='fn main(argc,argv)\n handle work()\n ok complete\n err error\n  return 90\n end\n let i=0\n while i<3\n  let p=load64(buffer("saved",24)+i*8)\n  if p==0\n   return 94\n  end\n  if syscall6(74,p,1,3,0,0,0)!=-12\n   return 95+i\n  end\n  set i=i+1\n end\n return 0\nend\n'
 src=N+probes+'fn work():IO\n'+body+'\nend\n'+main;original=build('nested-mapping-cleanup',src,opt);check('nested pointer no-patch control',call([original]).returncode==94);patched=original.with_name(original.name+'-observe');receipt=pointer_probe(original,patched,['pointer_text','pointer_numbers']);q=call([patched]);check('all nested mappings retired '+str(opt),q.returncode==0,dict(exit=q.returncode,probe=receipt))
 # A moved nested result whose first arm drop fails still attempts peers and retries.
 factory='fn factory():EnvelopeReady\n'+body.replace(' own moved=move(e)\n return ok(0)',' return ok(move(e))')+'\nend\n'
 work=owner_handle('factory()','e','Envelope','')+' return ok(0)'
 main=main.replace(' ok complete\n err error\n  return 90',' ok complete\n  return 89\n err error\n  if error!=65548\n   return 90\n  end')
 src=N+probes+thunk(73)+factory+'fn work():IO\n'+work+'\nend\n'+main;original=build('nested-arm-drop-failure',src,opt);observed=original.with_name(original.name+'-observe');r1=pointer_probe(original,observed,['pointer_text','pointer_numbers']);shutil.copy2(str(original)+'.functions',str(observed)+'.functions');check('nested arm no-fault control',call([observed]).returncode==89);patched=original.with_name(original.name+'-fault');r2=fault(observed,patched,'__rf2heap_drop',73,True);q=call([patched]);check('nested arm drop peer retry '+str(opt),q.returncode==0,dict(exit=q.returncode,probe=r1,fault=r2))

# Real in-memory booking decisions compared against an independent Python interval model.
app=D/'app';(app/'lib').mkdir(parents=True)
for src,dst in [(R/'experiments/nested-owned/examples/booking-values.flow',app/'main.flow'),(R/'experiments/nested-owned/examples/lib/booking.flow',app/'lib/booking.flow'),(R/'examples/collection-tools/lib/numbers.rf2',app/'lib/numbers.rf2'),(R/'examples/collection-tools/lib/output.rf2',app/'lib/output.rf2')]:shutil.copy2(src,dst)
rng=random.Random(44151126)
for opt in (False,True):
 exe=app/('program-opt'if opt else'program-default');q=call([C,app/'main.flow',exe,*(['--opt']if opt else[])]);check('booking values compile '+str(opt),q.returncode==0,(q.stdout+q.stderr).decode(errors='replace'));call(['/usr/bin/codesign','-s','-',exe]).check_returncode()
 for trial in range(160):
  requests=[];stored=[];expected=dict(accepted=0,conflicts=0,refused=0)
  for i in range(rng.randrange(1,100)):
   row=(i+1,rng.randrange(1,6),739935+rng.randrange(3),rng.randrange(1440),0);row=(*row[:4],min(1440,row[3]+rng.randrange(1,121)))
   if i%17==0:row=(*row[:3],800,700)
   if i%19==0 and requests:row=requests[-1]
   requests.append(row);id,room,day,start,finish=row
   if not(id>0 and 1<=room<=16 and 1<=day<=3652059 and start<finish<=1440):expected['refused']+=1
   else:
    # Match the engine's first encountered rejection order: duplicate ID or conflict.
    decision='accepted'
    for prev in stored:
     if prev[0]==id:decision='refused';break
     if prev[1]==room and prev[2]==day and prev[3]<finish and start<prev[4]:decision='conflicts';break
    expected[decision]+=1
    if decision=='accepted':stored.append(row)
  expected['stored']=len(stored);q=call([exe],input=','.join(str(x)for row in requests for x in row).encode())
  check('booking independent model '+str(opt)+' '+str(trial),q.returncode==0 and json.loads(q.stdout)==expected,dict(exit=q.returncode,stdout=q.stdout.decode(errors='replace')[:200],expected=expected))
 for bad in (b'1,2,3',b'1,,2',b'18446744073709551616',b'bad'):
  q=call([exe],input=bad);check('booking invalid input '+str(opt)+' '+bad.decode(),q.returncode==2 and q.stdout==b'')
 q=call([exe],input=b'1,1,739935,540,600',preexec_fn=lambda:os.close(1));check('booking closed output '+str(opt),q.returncode==2)

(D/'report.json').write_text(json.dumps(dict(checks=len(ROWS),compilerSHA256=sha(C),ownedRowsExtension=os.environ.get('RF2_OWNED_ROWS_EXTENSION')=='1',controllerSHA256=sha(Path(__file__)),results=ROWS),indent=2)+'\n')
print(json.dumps(dict(checks=len(ROWS),report=str(D/'report.json'))))
