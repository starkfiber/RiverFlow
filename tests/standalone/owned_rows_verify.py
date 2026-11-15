"""Native owned-row state machine, refusal and labelled fault qualification."""
from pathlib import Path
import hashlib,json,os,random,shutil,struct,subprocess,tempfile
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_OWNED_ROW_COMPILER']).resolve()
D=Path(tempfile.mkdtemp(prefix='owned-rows-',dir=R/'artifacts'))
ROWS=[];SERIAL=0;BINDING=0
HEADER='''profile RF2_SYSTEM_A64_V1
result IO(u64,u64)
text Name(IO,64)
collection Numbers(IO,64)
record Row(name:own Name,numbers:own Numbers,id:u64)
result Ready(own Row,u64)
collection Rows(IO,64,Row)
result RowsReady(own Rows,u64)
'''
def check(name,ok,detail=None):
 ROWS.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:
  (D/'FAILED.json').write_text(json.dumps(ROWS,indent=2)+'\n');raise AssertionError((name,detail))
def call(args,**kw):return subprocess.run([os.fspath(a)if isinstance(a,Path)else a for a in args],capture_output=True,timeout=30,**kw)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def handle(expr,body='',error='return err($e)'):
 global BINDING
 BINDING+=1;n=str(BINDING)
 return ' handle '+expr+'\n ok v'+n+'\n'+''.join('  '+line.replace('$v','v'+n)+'\n'for line in body.splitlines())+' err e'+n+'\n'+''.join('  '+line.replace('$e','e'+n)+'\n'for line in error.splitlines())+' end\n'
def ownhandle(expr,name,kind,body,error='return err($e)'):
 global BINDING
 BINDING+=1;n=str(BINDING)
 return ' handle '+expr+'\n ok own '+name+':'+kind+'\n'+''.join('  '+line+'\n'for line in body.splitlines())+' err e'+n+'\n'+''.join('  '+line.replace('$e','e'+n)+'\n'for line in error.splitlines())+' end\n'
def wrap(body,extra='',header=HEADER):return header+extra+'fn work():IO\n'+body+'\nend\nfn main(argc,argv)\n handle work()\n ok value\n  return value\n err cause\n  return cause\n end\n return 201\nend\n'
def build(name,source,opt,refuse=None):
 global SERIAL
 SERIAL+=1;p=D/f'{SERIAL:03}-{name}.flow';p.write_text(source);exe=p.with_suffix('')
 q=call([C,p,exe,'--compact','--functions',*(['--opt']if opt else[])])
 text=(q.stdout+q.stderr).decode(errors='replace')
 if refuse:
  check(name+' refusal '+str(opt),q.returncode!=0 and refuse in text,text[:500]);check(name+' absent image',not exe.exists());return None
 check(name+' compile '+str(opt),q.returncode==0,text[:500]);call(['/usr/bin/codesign','-s','-',exe]).check_returncode();return exe
def execute(name,source,opt,expected=0):
 exe=build(name,source,opt);q=call([exe]);check(name+' execute '+str(opt),q.returncode==expected,dict(exit=q.returncode,stdout=q.stdout.hex(),stderr=q.stderr.decode(errors='replace')));return exe
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
def fault(exe,function,number,once):
 data=exe.read_bytes();start,size=ranges(exe)[function]
 sites=[i for i in range(start,start+size-3)if data[i:i+4]==struct.pack('<I',0xd4001001)]
 assert len(sites)=={'__rf2heap_grow':2,'__rf2heap_drop':1,'__rf2heap_pending':1}[function]
 offset=sites[1 if function=='__rf2heap_grow'and number==73 else 0]
 assert data[offset+4:offset+12]==struct.pack('<II',0x54000043,0xcb0003e0)
 if once:
  target=ranges(exe)['fault_once'][0];delta=target-offset;assert delta%4==0 and -(1<<27)<=delta<(1<<27)
  replacement=struct.pack('<III',0x94000000|((delta//4)&0x3ffffff),0xd503201f,0xd503201f)
 else:replacement=struct.pack('<III',0x92800000|(11<<5),0xd503201f,0xd503201f)
 out=exe.with_name(exe.name+'-fault');out.write_bytes(data[:offset]+replacement+data[offset+12:]);out.chmod(0o700);call(['/usr/bin/codesign','-s','-','--force',out]).check_returncode()
 return out,dict(kind='controlled disposable-image syscall result, not host OOM or hardware failure',function=function,syscall=number,once=once,offset=offset,original=data[offset:offset+12].hex(),replacement=replacement.hex(),inputSHA256=sha(exe),outputSHA256=sha(out))
def thunk(number):return 'fn fault_once(a,b,c,d,e,f)\n let counter=buffer("fault_counter",8)\n if load64(counter)==0\n  do store64(counter,1)\n  return -12\n end\n return syscall6('+str(number)+',a,b,c,d,e,f)\nend\n'
def observe(exe,functions):
 data=bytearray(exe.read_bytes());entries=ranges(exe);changes=[]
 for name in functions:
  offset,size=entries[name];assert size>=8
  original=bytes(data[offset:offset+8]);replacement=struct.pack('<II',0xf9400400,0xd65f03c0)
  data[offset:offset+8]=replacement;changes.append(dict(function=name,offset=offset,original=original.hex(),replacement=replacement.hex()))
 out=exe.with_name(exe.name+'-observe');out.write_bytes(data);out.chmod(0o700);call(['/usr/bin/codesign','-s','-','--force',out]).check_returncode()
 return out,dict(kind='disposable-image descriptor observation, not a source-language raw-pointer capability',changes=changes,inputSHA256=sha(exe),outputSHA256=sha(out))
FACTORY='fn make(id):Ready\n own row=Row(Name(),Numbers(),id)\n'+handle('text_append(row.name,0xb85+(id-(id//30)*30))')+handle('collection_push(row.numbers,id*17)')+' return ok(move(row))\nend\nfn pass(own rows:Rows):RowsReady\n return ok(move(rows))\nend\n'
for opt in (False,True):
 # One binary handles many fresh operation streams; Python independently models identities/order.
 push=ownhandle('make(arg)','fresh','Row',handle('rows_push(rows,move(fresh))','set answer=$v','set status=$e'))
 take=ownhandle('rows_take(rows,arg)','taken','Row','set answer=taken.id\n'+handle('text_get(taken.name,0)','if $v!=0xb85+(taken.id-(taken.id//30)*30)\n return err(71)\nend')+handle('collection_get(taken.numbers,0)','if $v!=taken.id*17\n return err(72)\nend'),'set status=$e')
 transfer=ownhandle('pass(move(rows))','forwarded','Rows',ownhandle('pass(move(forwarded))','back','Rows','return ok(back.length)'))
 driver='''fn work():IO
 own rows=Rows()
 let bytes=buffer("commands",65536)
 let used=0
 let reading=1
 while (used<65536)&reading
  let got=read(0,bytes+used,65536-used)
  if got>>63
   return err(73)
  end
  if got==0
   set reading=0
  end
  set used=used+got
 end
 if used-(used//16)*16
  return err(74)
 end
 let at=0
 while at<used
  let op=load64(bytes+at)
  let arg=load64(bytes+at+8)
  let status=0
  let answer=0
  if op==1
'''+push+'''  else
   if op==2
'''+take+'''   else
    if op==3
'''+handle('rows_reserve(rows,arg)','set answer=$v','set status=$e')+'''    else
     if op==4
'''+handle('rows_clear(rows)','set answer=$v','set status=$e')+'''     else
      return err(75)
     end
    end
   end
  end
  let output=buffer("output",32)
  do store64(output,op)
  do store64(output+8,status)
  do store64(output+16,answer)
  do store64(output+24,rows.length)
  if write(1,output,32)!=32
   return err(76)
  end
  set at=at+16
 end
 return ok(0)
end
fn main(argc,argv)
 handle work()
 ok value
  return value
 err cause
  return cause
 end
 return 201
end
'''
 exe=build('state-machine',HEADER+FACTORY+driver,opt)
 rng=random.Random(46151126)
 for trial in range(120):
  operations=[(1,i)for i in range(1,65)]+[(1,99),(2,2**64-1),(3,65)]if trial==0 else []
  operations +=[(rng.choices([1,2,3,4],[5,4,1,1])[0],rng.randrange(0,90))for _ in range(rng.randrange(8,120))]
  operations +=[(2,0)]*70
  model=[];expected=[]
  for op,arg in operations:
   status=0;answer=0
   if op==1:
    if len(model)>=64:status=22
    else:model.append(arg);answer=len(model)
   elif op==2:
    if arg>=len(model):status=34
    else:answer=model.pop(arg)
   elif op==3:
    if arg>64:status=22
    else:answer=None
   else:model.clear()
   expected.append((op,status,answer,len(model)))
  q=call([exe],input=b''.join(struct.pack('<QQ',*op)for op in operations));actual=list(struct.iter_unpack('<QQQQ',q.stdout))if len(q.stdout)%32==0 else []
  matched=q.returncode==0 and len(actual)==len(expected)and all(a[:2]==e[:2]and a[3]==e[3]and(e[2]is None or a[2]==e[2])for a,e in zip(actual,expected))
  check('independent state machine '+str(opt)+' '+str(trial),matched,dict(exit=q.returncode,operations=len(operations),records=len(actual),stderr=q.stderr.decode(errors='replace')[:300]))
 body=' own rows=Rows()\n'+ownhandle('make(9)','row','Row',handle('rows_push(rows,move(row))'))+transfer+' return err(77)'
 execute('collection-through-function-boundaries',wrap(body,FACTORY),opt,1)
 # An owned row can itself be a collection, and can appear under another record.
 header=HEADER+'collection Groups(IO,8,Rows)\nrecord Folder(groups:own Groups,tag:u64)\nresult GroupsReady(own Groups,u64)\n'
 body=' own folder=Folder(Groups(),7)\n own rows=Rows()\n'+ownhandle('make(3)','r','Row',handle('rows_push(rows,move(r))'))+handle('rows_push(folder.groups,move(rows))')+ownhandle('rows_take(folder.groups,0)','selected','Rows',ownhandle('rows_take(selected,0)','last','Row','return ok(last.id!=3)'))+' return err(78)'
 execute('nested-collection-row-and-field',wrap(body,FACTORY,header),opt)
 header='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext T(IO,8)\n'
 for i in range(20):header+='record L'+str(i)+'(child:own '+('T'if i==0 else'L'+str(i-1))+',value:u64)\n'
 header+='collection Deep(IO,8,L19)\nresult DeepReady(own L19,u64)\n'
 constructor='T()'
 for i in range(20):constructor='L'+str(i)+'('+constructor+','+str(100+i)+')'
 body=' own rows=Deep()\n own deep='+constructor+'\n'+handle('text_append(deep'+'.child'*20+',0xb85)')+handle('rows_push(rows,move(deep))')+handle('rows_reserve(rows,8)')+ownhandle('rows_take(rows,0)','taken','L19','if (taken.value!=119)|(taken'+'.child'*19+'.value!=100)\n return err(89)\nend\n'+handle('text_get(taken'+'.child'*20+',0)','return ok($v!=0xb85)'))+' return err(88)'
 execute('deep-ownership-row-relocation',wrap(body,header=header),opt)
 header='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ntext T(IO,8)\ncollection Texts(IO,8,T)\nresult TextReady(own T,u64)\n'
 body=' own rows=Texts()\n own text=T()\n'+handle('text_append(text,0xb85)')+handle('rows_push(rows,move(text))')+ownhandle('rows_take(rows,0)','taken','T',handle('text_get(taken,0)','if $v!=0xb85\n return err(87)\nend'))+' own dead=T()\n'+handle('release(dead)')+handle('rows_push(rows,move(dead))','return err(86)','if ($e!=9)|(rows.length!=0)\n return err(85)\nend')+' return ok(0)'
 execute('text-rows-and-dead-owner-refusal',wrap(body,header=header),opt)
 body=' own rows=Rows()\n'+handle('release(rows)')+' own moved=move(rows)\n return ok(0)'
 execute('dead-collection-move-error',wrap(body),opt,9)
 bad=[
  ('missing-move',' own rows=Rows()\n own row=Row(Name(),Numbers(),1)\n'+handle('rows_push(rows,row)')+' return ok(0)','expected: move'),
  ('reuse-consumed-row',' own rows=Rows()\n own row=Row(Name(),Numbers(),1)\n'+handle('rows_push(rows,move(row))')+' return ok(row.id)','local used before initialization or outside scope'),
  ('nonowned-extraction',' own rows=Rows()\n'+handle('rows_take(rows,0)')+' return ok(0)','rows_take requires an owned result handler'),
  ('scalar-copy-api',' own rows=Rows()\n own row=Row(Name(),Numbers(),1)\n'+handle('records_push(rows,row)')+' return ok(0)','record collection required'),
  ('partial-row',' own rows=Rows()\n own row=Row(Name(),Numbers(),1)\n own text=move(row.name)\n'+handle('rows_push(rows,move(row))')+' return ok(0)','transferred aggregate contains moved field'),
  ('private-owned-row-helper',' do __rf2rows_op(0,0,0,0)\n return ok(0)','reserved compiler collection helper'),
 ]
 for name,body,reason in bad:build(name,wrap(body),opt,refuse=reason)
 build('private-owned-row-definition',wrap(' return ok(0)','fn __rf2rows_forged()\n return 0\nend\n'),opt,refuse='reserved compiler collection helper')
 # Faults target allocation, relocation retirement and recursive drops separately.
 body=' own rows=Rows()\n own row=Row(Name(),Numbers(),7)\n let failed=0\n'+handle('rows_push(rows,move(row))','', 'set failed=1\nif ($e!=12)|(rows.length!=0)\n return err(80)\nend')+handle('rows_reserve(rows,64)')+' return ok(failed==0)'
 original=execute('allocation-control',wrap(body,thunk(197)),opt,1);patched,receipt=fault(original,'__rf2heap_grow',197,True);q=call([patched]);check('allocation failure preserves rows '+str(opt),q.returncode==0,dict(exit=q.returncode,fault=receipt))
 body=' own rows=Rows()\n'+ownhandle('make(7)','row','Row',handle('rows_push(rows,move(row))'))+' let failed=0\n'+handle('rows_reserve(rows,64)','','set failed=1\nif ($e!=12)|(rows.length!=1)\n return err(81)\nend')+' own moved=move(rows)\n'+handle('rows_reserve(moved,64)')+ownhandle('rows_take(moved,0)','taken','Row','if taken.id!=7\n return err(82)\nend')+' return ok(failed==0)'
 original=execute('retirement-control',wrap(body,FACTORY+thunk(73)),opt,1);patched,receipt=fault(original,'__rf2heap_grow',73,True);q=call([patched]);check('failed retirement retry and rebasing '+str(opt),q.returncode==0,dict(exit=q.returncode,fault=receipt))
 body=' own rows=Rows()\n'+ownhandle('make(7)','row','Row',handle('rows_push(rows,move(row))'))+' let failed=0\n'+handle('rows_clear(rows)','','set failed=1\nif $e!=12\n return err(83)\nend')+' if failed\n'+ownhandle('rows_take(rows,0)','unavailable','Row','return err(84)','if $e!=16\n return err(85)\nend')+' end\n'+handle('rows_clear(rows)')+' if rows.length!=0\n return err(86)\n end\n return ok(failed==0)'
 original=execute('partial-cleanup-control',wrap(body,FACTORY+thunk(73)),opt,1);patched,receipt=fault(original,'__rf2heap_drop',73,True);q=call([patched]);check('partial cleanup quarantines then recovers '+str(opt),q.returncode==0,dict(exit=q.returncode,fault=receipt))
 probes='fn pointer_text(value:Name)\n return 0\nend\nfn pointer_numbers(value:Numbers)\n return 0\nend\nfn pointer_rows(value:Rows)\n return 0\nend\n'
 body=' own rows=Rows()\n own row=Row(Name(),Numbers(),7)\n'+handle('text_append(row.name,65)')+handle('collection_push(row.numbers,17)')+' do store64(buffer("observed",24),pointer_text(row.name))\n do store64(buffer("observed",24)+8,pointer_numbers(row.numbers))\n'+handle('rows_push(rows,move(row))')+handle('rows_reserve(rows,64)')+' do store64(buffer("observed",24)+16,pointer_rows(rows))\n return ok(0)'
 main='fn main(argc,argv)\n handle work()\n ok value\n err error\n  return 90\n end\n let i=0\n while i<3\n  let p=load64(buffer("observed",24)+i*8)\n  if p==0\n   return 94\n  end\n  if syscall6(74,p,1,3,0,0,0)!=-12\n   return 95+i\n  end\n  set i=i+1\n end\n return 0\nend\n'
 original=build('recursive-retirement-observation',HEADER+probes+'fn work():IO\n'+body+'\nend\n'+main,opt);check('no-probe control '+str(opt),call([original]).returncode==94);patched,receipt=observe(original,['pointer_text','pointer_numbers','pointer_rows']);q=call([patched]);check('child and row mappings actually retired '+str(opt),q.returncode==0,dict(exit=q.returncode,probe=receipt))
 # Complete command-line application, reusing the existing UTF-8/output libraries.
 app=D/('catalog-opt'if opt else'catalog-default');(app/'lib').mkdir(parents=True)
 dependencies=[(R/'experiments/owned-rows/catalog.flow',app/'main.flow'),(R/'experiments/owned-functions/examples/lib/batch.flow',app/'lib/batch.flow'),(R/'examples/collection-tools/lib/numbers.rf2',app/'lib/numbers.rf2'),(R/'examples/collection-tools/lib/output.rf2',app/'lib/output.rf2')]
 for source,target in dependencies:shutil.copy2(source,target)
 exe=app/'program';q=call([C,app/'main.flow',exe,'--compact',*(['--opt']if opt else[])]);check('catalog compile '+str(opt),q.returncode==0,(q.stdout+q.stderr).decode(errors='replace')[:500]);call(['/usr/bin/codesign','-s','-',exe]).check_returncode()
 cases=[['தமிழ்','Jitra','👩🏽\u200d💻'],['','A\nB','"\\','e\u0301'],['\U0010ffff'],['a'*256],['x']*64]
 rng=random.Random(460246)
 alphabet=['a','Z','0','\n','\t','"','\\','அ','ழ','é','\u0301','🙂','\U0010ffff']
 for trial in range(70):cases.append([''.join(rng.choice(alphabet)for _ in range(rng.randrange(20)))for _ in range(rng.randrange(1,30))])
 for number,labels in enumerate(cases):
  q=call([exe,*labels]);expected=[dict(id=i+1,label=label,scalars=len(label),scalar_sum=sum(map(ord,label)))for i,label in enumerate(labels)]
  try:actual=json.loads(q.stdout)
  except (ValueError,UnicodeError):actual=None
  check('catalog independent Unicode manifest '+str(opt)+' '+str(number),q.returncode==0 and actual==expected,dict(exit=q.returncode,stdout=q.stdout[:200].decode(errors='replace'),stderr=q.stderr.decode(errors='replace')[:200]))
 for number,labels in enumerate([[],['a']*65,['a'*257],['தமிழ்','ok',b'\xff'],['ok',b'\xed\xa0\x80'],['🙂'*257]]):
  q=call([exe,*labels]);check('catalog rejects before publishing '+str(opt)+' '+str(number),q.returncode==2 and q.stdout==b''and q.stderr.startswith(b'Error '),dict(exit=q.returncode,stdout=q.stdout[:100].hex(),stderr=q.stderr.decode(errors='replace')[:200]))
 q=call([exe,'தமிழ்','Jitra'],preexec_fn=lambda:os.close(1));check('catalog closed output '+str(opt),q.returncode==2 and q.stderr==b'Error 5\n',dict(exit=q.returncode,stderr=q.stderr.decode(errors='replace')))
 print('owned row mode',opt,'passed',flush=True)
(D/'report.json').write_text(json.dumps(dict(checks=len(ROWS),compilerSHA256=sha(C),results=ROWS),indent=2)+'\n')
print(json.dumps(dict(checks=len(ROWS),report=str(D/'report.json'))))
