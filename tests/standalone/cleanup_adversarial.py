"""Independently authored in-process oracles for bounded defer-close cleanup.

No clock/speed claims. File effects are restricted to tempfile fixtures. Raw descriptor
reuse remains trusted systems behavior; these checks do not claim linear ownership.
"""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
R=Path(__file__).resolve().parents[2]
C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-text-cleanup-candidate'))
BADFD='18446744073709551607'
head='profile RF2_SYSTEM_A64_V1\nrecord Ref(one:u64,two:u64)\nresult Number(u64,u64)\n'
cases=[]
def add(name,source,accepted=True,status=0):cases.append((name,head+source,accepted,status))
def wrapper(body,expected=42):
 return '''fn work(path,r:Ref)
 let fd=open(path,0,0)
 if fd>=9223372036854775808
  return 101
 end
 set r.one=fd
'''+body+'''\nend
fn main(argc,argv)
 let r=Ref(0,0)
 let value=work(load64(argv+8),r)
 let closed=close(r.one)
 return (value!='''+str(expected)+''')|(closed!='''+BADFD+''')
end
'''
add('scalar-return',wrapper(' defer close(fd)\n return 42'))
add('fallthrough',wrapper(' defer close(fd)',0))
add('branch-return',wrapper(' defer close(fd)\n if fd<9223372036854775808\n  return 42\n end\n return 3'))
add('loop-return',wrapper(' defer close(fd)\n let i=0\n while i<4\n  if i==2\n   return 42\n  end\n  set i=i+1\n end\n return 3'))
for arm in ['ok','err']:
 add('typed-'+arm,'''fn work(path,r:Ref):Number
 let fd=open(path,0,0)
 if fd>=9223372036854775808
  return err(101)
 end
 set r.one=fd
 defer close(fd)
 return '''+arm+'''(42)
end
fn main(argc,argv)
 let r=Ref(0,0)
 let result=99
 handle work(load64(argv+8),r)
 ok value
  set result='''+('value'if arm=='ok'else'100')+'''
 err cause
  set result='''+('cause'if arm=='err'else'100')+'''
 end
 let closed=close(r.one)
 return (result!=42)|(closed!='''+BADFD+''')
end
''')
add('early-before-registration', '''fn work(path,r:Ref)
 let fd=open(path,0,0)
 set r.one=fd
 if fd<9223372036854775808
  return 42
 end
 defer close(fd)
 return 3
end
fn main(argc,argv)
 let r=Ref(0,0)
 let value=work(load64(argv+8),r)
 let closed=close(r.one)
 return (value!=42)|(closed!=0)
end
''')
add('snapshot-mutated-local', '''fn work(path,r:Ref)
 let fd=open(path,0,0)
 set r.one=fd
 defer close(fd)
 let replacement=open(path,0,0)
 set r.two=replacement
 set fd=replacement
 return 42
end
fn main(argc,argv)
 let r=Ref(0,0)
 let value=work(load64(argv+8),r)
 let closed1=close(r.one)
 let closed2=close(r.two)
 return (value!=42)|(closed1!='''+BADFD+''')|(closed2!=0)
end
''')
add('capture-expression-evaluated-once', '''fn acquire(path,r:Ref)
 set r.two=r.two+1
 let fd=open(path,0,0)
 set r.one=fd
 return fd
end
fn work(path,r:Ref)
 defer close(acquire(path,r))
 return 42
end
fn main(argc,argv)
 let r=Ref(0,0)
 let value=work(load64(argv+8),r)
 let closed=close(r.one)
 return (value!=42)|(r.two!=1)|(closed!='''+BADFD+''')
end
''')
add('nested-call-register-preservation', '''fn touch(n)
 let a=n*3+1
 let b=a*5
 return b
end
'''+wrapper(' defer close(fd)\n let x=touch(fd)\n let y=touch(x)\n return 42+(y==0)'))
add('repeated-no-fd-leak', '''fn work(path)
 let fd=open(path,0,0)
 if fd>=9223372036854775808
  return 1
 end
 defer close(fd)
 return 0
end
fn main(argc,argv)
 let probe=open(load64(argv+8),0,0)
 do close(probe)
 let i=0
 let failed=0
 while i<400
  set failed=failed|work(load64(argv+8))
  set i=i+1
 end
 let again=open(load64(argv+8),0,0)
 let closed=close(again)
 return failed|(again!=probe)|(closed!=0)
end
''')
add('runtime-arm-flags-per-invocation', '''fn work(path,early)
 if early
  return 42
 end
 let fd=open(path,0,0)
 defer close(fd)
 return 42
end
fn main(argc,argv)
 let probe=open(load64(argv+8),0,0)
 let a=work(load64(argv+8),0)
 let b=work(load64(argv+8),1)
 let still_open=close(probe)
 return (a!=42)|(b!=42)|(still_open!=0)
end
''')
add('cleanup-does-not-replace-result-on-close-error','''fn work()
 defer close(18446744073709551615)
 return 42
end
fn main(argc,argv)
 return work()!=42
end
''')
add('raw-descriptor-reuse-is-not-ownership','''fn work(path,r:Ref)
 let fd=open(path,0,0)
 defer close(fd)
 do close(fd)
 let replacement=open(path,0,0)
 set r.one=replacement
 set r.two=fd
 return 42
end
fn main(argc,argv)
 let r=Ref(0,0)
 let value=work(load64(argv+8),r)
 let closed=close(r.one)
 return (value!=42)|(r.one!=r.two)|(closed!='''+BADFD+''')
end
''')
# Multiple registrations: every descriptor closed; LIFO order is not distinguished
# by independent close syscalls. Do not label this an observable ordering proof.
add('multiple-registrations', '''fn work(path,r:Ref)
 let first=open(path,0,0)
 set r.one=first
 defer close(first)
 let second=open(path,0,0)
 set r.two=second
 defer close(second)
 return 42
end
fn main(argc,argv)
 let r=Ref(0,0)
 let value=work(load64(argv+8),r)
 let c1=close(r.one)
 let c2=close(r.two)
 return (value!=42)|(c1!='''+BADFD+''')|(c2!='''+BADFD+''')
end
''')
for n in [16,17]:
 add('registration-bound-'+str(n),'fn work()\n'+''.join(' defer close(18446744073709551615)\n'for _ in range(n))+' return 42\nend\nfn main(argc,argv)\n return work()!=42\nend\n',n==16)
# Capture slots and ordinary locals must share the same checked frame budget.
for n,good in [(223,True),(224,False)]:
 body='fn work(path)\n'+''.join(f' let v{i}={i}\n'for i in range(n))+''.join(' defer close(18446744073709551615)\n'for _ in range(16))+' return 42+v0\nend\nfn main(argc,argv)\n return work(load64(argv+8))!=42\nend\n'
 add('frame-capture-budget-'+str(n),body,good)
for name,body in [
 ('branch-registration','if argc\n defer close(1)\nend'),
 ('loop-registration','while 0\n defer close(1)\nend'),
 ('wrong-operation','defer open(0,0,0)'),
 ('wrong-arity','defer close(1,2)'),
 ('missing-argument','defer close()'),
 ('uninitialized-capture','let fd=fd+1\ndefer close(fd)'),
 ('block-escaped-capture','if 0\n let fd=1\nend\ndefer close(fd)'),
]:add(name,'fn main(argc,argv)\n'+body+'\nreturn 0\nend\n',False)
rows=[]
with tempfile.TemporaryDirectory(prefix='rf2-cleanup-agent-')as tmp:
 root=Path(tmp);sample=root/'input.txt';sample.write_bytes(b'clean temporary fixture\n')
 for opt in [False,True]:
  for name,src,accepted,status in cases:
   source=root/(name+str(opt)+'.rf2');source.write_text(src);out=root/(name+str(opt));p=subprocess.run([C,source,out]+(['--opt']if opt else[]),capture_output=True,timeout=30)
   row={'name':name,'optimized':opt,'expectedAdmission':accepted,'compileExit':p.returncode,'sourceSHA256':hashlib.sha256(src.encode()).hexdigest()}
   if accepted:
    assert p.returncode==0,(name,opt,p.stderr.decode());subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
    q=subprocess.run([out,sample],capture_output=True,timeout=10);row.update(runExit=q.returncode,stdout=q.stdout.decode(errors='replace'),stderr=q.stderr.decode(errors='replace'));assert q.returncode==status,(row,status)
   else:assert p.returncode==1 and not out.exists(),(name,opt,p.returncode,p.stderr.decode())
   row['passed']=True;rows.append(row)
report={'passed':True,'checks':len(rows),'nativeExecutions':sum(x['expectedAdmission']for x in rows),'compileRefusals':sum(not x['expectedAdmission']for x in rows),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'scope':'Independent default/optimized in-process close validity, captured value, early return, result preservation and bound checks. Raw descriptor reuse remains trusted; close errors do not overwrite ordinary returns. No runtime LIFO-order proof, trap cleanup guarantee, linear ownership or universal leak/security proof.','results':rows}
out=Path(os.environ.get('RF2_TEST_REPORT',R/'artifacts/cleanup-agent-verification.json'));out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='results'},indent=2))
