"""Independent native bounded growable-vector invariants and controlled faults.

RF2_TEST_COMPILER must identify the candidate. Host faults patch exact syscall
instruction pairs in disposable copies; they are injected failures, not real OOM.
"""
from pathlib import Path
import hashlib,json,os,struct,subprocess,tempfile,time
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
D=R/'artifacts/vector-adversarial'/str(time.time_ns());D.mkdir(parents=True)
H='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\nvector Bytes(IO,64)\n'
CASES=[]
def program(body,limit=64):
 return H.replace('Bytes(IO,64)',f'Bytes(IO,{limit})')+'''fn work():IO
 own b=Bytes()
'''+body+'''\nend
fn main(argc,argv)
 handle work()
 ok value
  return value
 err cause
  return 200
 end
 return 201
end
'''
def add(name,body,limit=64,status=0):CASES.append((name,program(body,limit),True,status))
def refused(name,source):CASES.append((name,source,False,None))
add('empty','return ok(b.length|b.capacity|(b.limit!=64))')
add('reserve-zero','handle buffer_reserve(b,0)\nok n\n return ok(n|b.length|b.capacity)\nerr e\n return err(e)\nend\nreturn ok(201)')
add('reserve-no-shrink','''handle buffer_reserve(b,3)
ok n
 if (n!=3)|(b.length!=0)|(b.capacity!=3)
  return ok(1)
 end
err e
 return err(e)
end
handle buffer_reserve(b,1)
ok n2
 return ok((n2!=3)|(b.length!=0)|(b.capacity!=3))
err e2
 return err(e2)
end
return ok(201)''')
add('all-byte-values','''let i=0
while i<256
 handle buffer_push(b,i)
 ok n
  if n!=i+1
   return ok(1)
  end
 err e
  return err(e)
 end
 set i=i+1
end
set i=0
while i<256
 handle buffer_get(b,i)
 ok value
  if value!=i
   return ok(2)
  end
 err e2
  return err(e2)
 end
 if b[i]!=i
  return ok(3)
 end
 set i=i+1
end
return ok((b.length!=256)|(b.capacity!=256))''',256)
add('boundary-seventeen','''let i=0
while i<17
 handle buffer_push(b,i)
 ok n
 err e
  return err(e)
 end
 set i=i+1
end
handle buffer_push(b,99)
ok n2
 return ok(1)
err e2
 return ok((e2!=22)|(b.length!=17)|(b.capacity!=17)|(b[0]!=0)|(b[16]!=16))
end
return ok(201)''',17)
add('boundary-one','''handle buffer_push(b,255)
ok n
 if (n!=1)|(b.capacity!=1)
  return ok(1)
 end
err e
 return err(e)
end
handle buffer_push(b,0)
ok n2
 return ok(2)
err e2
 return ok((e2!=22)|(b.length!=1)|(b[0]!=255))
end
return ok(201)''',1)
for n in [65,2**64-1]:
 add(f'reserve-over-{n}',f'''handle buffer_reserve(b,{n})
ok value
 return ok(1)
err cause
 return ok((cause!=22)|b.length|b.capacity)
end
return ok(201)''')
for n in [256,2**64-1]:
 add(f'bad-byte-{n}',f'''handle buffer_push(b,{n})
ok value
 return ok(1)
err cause
 return ok((cause!=22)|b.length|b.capacity)
end
return ok(201)''')
for n in [0,64,2**64-1]:
 add(f'empty-get-{n}',f'''handle buffer_get(b,{n})
ok value
 return ok(1)
err cause
 return ok((cause!=34)|b.length|b.capacity)
end
return ok(201)''')
add('clear-keeps-capacity','''handle buffer_push(b,255)
ok n
err e
 return err(e)
end
let previous=b.capacity
handle buffer_clear(b)
ok n2
 if n2|b.length|(b.capacity!=previous)
  return ok(1)
 end
err e2
 return err(e2)
end
handle buffer_get(b,0)
ok value
 return ok(2)
err e3
 if e3!=34
  return ok(3)
 end
end
handle buffer_push(b,0)
ok n3
 return ok((n3!=1)|(b[0]!=0)|(b.capacity!=previous))
err e4
 return err(e4)
end
return ok(201)''')
add('explicit-release','''handle release(b)
ok n
 return ok(n)
err e
 return err(e)
end
return ok(201)''')
add('loop-release-guard','''let i=0
let tally=0
while i<2
 handle release(b)
 ok n
  set tally=tally+1
 err e
  if e!=9
   return ok(1)
  end
  set tally=tally+10
 end
 set i=i+1
end
return ok(tally!=11)''')
add('max-reservation-bound','''handle buffer_reserve(b,1048576)
ok n
 return ok((n!=1048576)|b.length|(b.limit!=1048576))
err e
 return err(e)
end
return ok(201)''',1048576)
# Index trap is distinct from recoverable buffer_get.
add('index-trap','return ok(b[0])',status=2)
for name,line in [('copy','let x=b'),('discard','do b'),('return','return ok(b)'),('property-write','set b.length=1'),('indexed-write','set b[0]=1'),('raw-argument','do close(b)'),('discard-result','do buffer_push(b,1)'),('wrong-arity','handle buffer_push(b,1,2)\nok n\nerr e\nend'),('rebind','set b=Bytes()')]:
 refused('refuse-'+name,program(line+'\nreturn ok(0)'))
refused('use-after-release',program('handle release(b)\nok n\nerr e\nend\nhandle buffer_push(b,1)\nok v\nerr e2\nend\nreturn ok(0)'))
refused('parameter-owner',H+'fn f(b:Bytes)\nreturn 0\nend\nfn main(argc,argv)\nreturn 0\nend\n')
for bound in [0,1048577,'0001','0x40','18446744073709551617','999999999999999999999999999999999999999']:refused(f'limit-{bound}',program('return ok(0)',bound))
refused('view-while-grow',H+'array B(u8,1)\nview V(B)\nfn work():IO\nown b=Bytes()\nlet a=B()\nlet v=V(a,0,1)\nhandle buffer_push(b,1)\nok n\nerr e\nend\nreturn ok(0)\nend\nfn main(argc,argv)\nreturn 0\nend\n')
# A loop can execute an earlier read again after a later release.
for member in ['[0]','.length','.capacity','.limit']:
 add('loop-reentry-'+member.replace('.','').replace('[','').replace(']',''),'''handle buffer_push(b,65)
ok n
err e
 return err(e)
end
let i=0
let sum=0
while i<2
 set sum=sum+b'''+member+'''
 handle release(b)
 ok value
 err cause
 end
 set i=i+1
end
return ok(sum)''',status=2)
# Combined hidden slots count toward the existing frame bound.
for locals_count in [176,177]:
 source=H+'fn work():IO\n'+''.join(f' own b{i}=Bytes()\n'for i in range(16))+''.join(f' let s{i}={i}\n'for i in range(locals_count))+f' return ok(s{locals_count-1}!={locals_count-1})\nend\nfn main(argc,argv)\nhandle work()\nok v\n return v\nerr e\n return 201\nend\nreturn 202\nend\n'
 CASES.append((f'frame-{locals_count}',source,locals_count==176,0))
source=H+'fn work():IO\n'+''.join(f' own b{i}=Bytes()\n'for i in range(17))+'return ok(0)\nend\nfn main(argc,argv)\nreturn 0\nend\n';refused('seventeen-owners',source)
rows=[]
def build(src,out,opt):
 path=out.with_suffix('.rf2');path.write_text(src);q=subprocess.run([C,path,out]+(['--opt']if opt else[]),capture_output=True,timeout=30);return q,path

def sign(out):subprocess.run(['/usr/bin/codesign','-s','-','--force',out],check=True,capture_output=True)
def execute(out,status):
 q=subprocess.run([out],capture_output=True,timeout=10);assert q.returncode==status,(out,q.returncode,status,q.stderr);return q

def patch_syscall(source,out,number,index,expected):
 data=source.read_bytes();needle=struct.pack('<II',0xd2800000|(number<<5)|16,3556773889);where=[i for i in range(len(data)-7)if data[i:i+8]==needle];assert len(where)==expected,(number,len(where),expected)
 pos=where[index];replacement=struct.pack('<II',0xd2800000|(12<<5),0xeb1f03ff);out.write_bytes(data[:pos]+replacement+data[pos+8:]);out.chmod(0o700);sign(out);return {'syscall':number,'site':index,'matchingSites':len(where),'sourceSHA256':hashlib.sha256(data).hexdigest(),'patchedSHA256':hashlib.sha256(out.read_bytes()).hexdigest()}
for opt in [False,True]:
 for name,src,good,status in CASES:
  out=D/(name+str(opt));q,path=build(src,out,opt)
  if good:
   assert q.returncode==0,(name,opt,q.stderr);sign(out);run=execute(out,status)
   if status==2:assert b'RF2 bounds'in run.stderr,(name,run.stderr)
  else:assert q.returncode==1 and not out.exists(),(name,opt,q.returncode,q.stderr)
  rows.append({'name':name,'optimized':opt,'passed':True,'expectedCompile':good})
 # Controlled initial mmap failure: no actual reservation is made at the patchedsite.
 source=D/('fault-mmap'+str(opt));src=H+'''fn work():IO
 own b=Bytes()
 return ok(42)
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
''';q,_=build(src,source,opt);assert q.returncode==0,q.stderr;sign(source);execute(source,42);out=source.with_suffix('.fault');receipt=patch_syscall(source,out,197,0,1);execute(out,12);rows.append({'name':'injected-mmap','optimized':opt,'passed':True,'fault':receipt})
 # A previous successful push mustsurvive a later requested mprotect failure.
 src=H+'''fn work():IO
 own b=Bytes()
 handle buffer_push(b,170)
 ok n
 err e
  return err(e)
 end
 handle buffer_reserve(b,33)
 ok cap
  return ok(cap+100)
 err cause
  if (cause!=12)|(b.length!=1)|(b.capacity!=16)|(b[0]!=170)
   return ok(201)
  end
  return ok(cause)
 end
 return ok(202)
end
fn main(argc,argv)
 handle work()
 ok value
  return value
 err cause
  return 203
 end
 return 204
end
''';source=D/('fault-protect'+str(opt));q,_=build(src,source,opt);assert q.returncode==0,q.stderr;sign(source);execute(source,133);out=source.with_suffix('.fault');receipt=patch_syscall(source,out,74,1,2);execute(out,12);rows.append({'name':'injected-mprotect-preserves-state','optimized':opt,'passed':True,'fault':receipt})
 # Controlled automatic munmap failure must override authored success.
 src=H+'''fn work():IO
 own b=Bytes()
 return ok(42)
end
fn main(argc,argv)
 handle work()
 ok value
  return value!=42
 err cause
  if cause==65548
   return 1
  end
  return 2
 end
 return 201
end
''';source=D/('fault-cleanup'+str(opt));q,_=build(src,source,opt);assert q.returncode==0,q.stderr;sign(source);execute(source,0);out=source.with_suffix('.fault');receipt=patch_syscall(source,out,73,0,1);execute(out,1);rows.append({'name':'injected-munmap-cleanup-error','optimized':opt,'passed':True,'fault':receipt})
 # Explicit release error consumes the owner and prevents a second cleanup attempt.
 src=H+'''fn work():IO
 own b=Bytes()
 handle release(b)
 ok n
  return ok(42)
 err cause
  if cause==12
   return ok(43)
  end
  return ok(201)
 end
 return ok(202)
end
fn main(argc,argv)
 handle work()
 ok value
  return value
 err cause
  return 203
 end
 return 204
end
''';source=D/('fault-release'+str(opt));q,_=build(src,source,opt);assert q.returncode==0,q.stderr;sign(source);execute(source,42);out=source.with_suffix('.fault');receipt=patch_syscall(source,out,73,0,2);execute(out,43);rows.append({'name':'injected-release-error-consumes','optimized':opt,'passed':True,'fault':receipt})
v={'passed':True,'checks':len(rows),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'scope':'Finite native reservation-backed byte-vector probes in bothmodes. mmap/mprotect/munmap failures injected by exact machine-instruction patch in disposable signed copies, not real OS OOM or general allocatorproof.','results':rows};(D/'report.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v for k,v in v.items()if k!='results'},indent=2));print(D/'report.json')
