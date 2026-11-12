"""Independent owned-file admission and in-process lifetime oracles.

Controlled raw-descriptor close is used only for explicit cleanup-error injection;
it is outside the checked owned-resource contract. No network or performance claims.
"""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,time
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
D=R/'artifacts/ownership-adversarial'/str(time.time_ns());D.mkdir(parents=True)
H='profile RF2_SYSTEM_A64_V1\nresult Outcome(u64,u64)\nresource File(Outcome)\narray Bytes(u8,8)\n'
CASES=[]
def add(name,body,tag=0,payload=42,good=True,extra=''):
 work='fn work(path,missing,expected):Outcome\n'+body+'\nend\n'
 main='''fn main(argc,argv)
 let path=load64(argv+8)
 let missing=load64(argv+16)
 let expected=open(path,0,0)
 if expected>>63
  return 100
 end
 do close(expected)
 let tag=7
 let payload=0
 handle work(path,missing,expected)
 ok value
  set tag=0
  set payload=value
 err cause
  set tag=1
  set payload=cause
 end
 let after=open(path,0,0)
 do close(after)
 return (tag!='''+str(tag)+')|(payload!='+str(payload)+''')|(after!=expected)
end
'''
 CASES.append((name,H+extra+work+main,good))
add('ordinary-ok','own f=File(path,0,0)\nreturn ok(42)')
add('ordinary-err','own f=File(path,0,0)\nreturn err(77)',1,77)
add('early-before-own','if 1\n return ok(42)\nend\nown f=File(path,0,0)\nreturn ok(3)')
add('branch-return','own f=File(path,0,0)\nif 1\n return ok(42)\nend\nreturn ok(3)')
add('loop-return','own f=File(path,0,0)\nlet i=0\nwhile i<4\n if i==2\n  return ok(42)\n end\n set i=i+1\nend\nreturn ok(3)')
add('two-owners','own first=File(path,0,0)\nown second=File(path,0,0)\nreturn ok(42)')
add('second-acquisition-fails','own first=File(path,0,0)\nown second=File(missing,0,0)\nreturn ok(42)',1,2)
add('first-acquisition-fails','own first=File(missing,0,0)\nreturn ok(42)',1,2)
add('release-success','own f=File(path,0,0)\nhandle release(f)\nok value\n return ok(42)\nerr cause\n return err(cause)\nend\nreturn ok(3)')
add('read-owned','own f=File(path,0,0)\nlet b=Bytes()\nhandle read_owned(f,b,8)\nok n\n if (n==8)&(b[0]==104)\n  return ok(42)\n end\nerr cause\n return err(cause)\nend\nreturn ok(3)')
add('read-zero','own f=File(path,0,0)\nlet b=Bytes()\nhandle read_owned(f,b,0)\nok n\n return ok(n)\nerr cause\n return err(cause)\nend\nreturn ok(3)',0,0)
add('write-read-only','own f=File(path,0,0)\nlet b=Bytes()\nhandle write_owned(f,b,1)\nok n\n return ok(3)\nerr cause\n return err(cause)\nend\nreturn ok(3)',1,9)
add('read-over-capacity','own f=File(path,0,0)\nlet b=Bytes()\nhandle read_owned(f,b,9)\nok n\n return ok(3)\nerr cause\n return err(cause)\nend\nreturn ok(3)',1,22)
add('release-error-consumed','own f=File(path,0,0)\ndo close(expected)\nhandle release(f)\nok value\n return ok(3)\nerr cause\n if cause==9\n  return ok(42)\n end\nend\nreturn ok(3)')
add('auto-close-error','own f=File(path,0,0)\ndo close(expected)\nreturn ok(42)',1,65545)
add('primary-error-wins','own f=File(path,0,0)\ndo close(expected)\nreturn err(77)',1,77)
add('prior-close-error-acquire-primary','own f=File(path,0,0)\ndo close(expected)\nown second=File(missing,0,0)\nreturn ok(42)',1,2)
add('multiple-auto-errors-first','own first=File(path,0,0)\nown second=File(path,0,0)\ndo close(expected)\ndo close(expected+1)\nreturn ok(42)',1,65545)
add('loop-release-runtime-guard','own f=File(path,0,0)\nlet i=0\nlet tally=0\nwhile i<2\n handle release(f)\n ok value\n  set tally=tally+1\n err cause\n  if cause==9\n   set tally=tally+100\n  end\n end\n set i=i+1\nend\nreturn ok(tally)',0,101)
add('scalar-registers-survive','let a=11\nlet b=13\nlet c=17\nown f=File(path,0,0)\nreturn ok(a+b+c+1)')
# Calls must execute path/flag/mode expressions once and in order.
extra='''record Probe(count:u64)
fn once(path,p:Probe)
 set p.count=p.count+1
 return path
end
'''
add('acquisition-evaluated-once','let p=Probe(0)\nown f=File(once(path,p),0,0)\nreturn ok(p.count)',0,1,extra=extra)
for n in [16,17]:
 add('owner-count-'+str(n),'\n'.join(f'own f{i}=File(path,0,0)'for i in range(n))+'\nreturn ok(42)',good=n==16)
# 3 parameters +205 ordinary locals +16*(named+2hidden)=256.
for n in [205,206]:
 add('frame-'+str(n),'\n'.join(f'let v{i}=0'for i in range(n))+'\n'+'\n'.join(f'own f{i}=File(path,0,0)'for i in range(16))+'\nreturn ok(42)',good=n==205)
for name,body in [
 ('copy','let alias=f'),('raw-close','do close(f)'),('raw-syscall','do syscall6(6,f,0,0,0,0,0)'),
 ('raw-store','do store64(0,f)'),('return-owner','return ok(f)'),('arithmetic','let x=f+1'),
 ('reverse-arithmetic','let x=1+f'),('comparison','let x=f==0'),('while-comparison','while f<1\nend'),
 ('rebind','set f=File(path,0,0)'),('property-length','let x=f.length'),('property-fd','let x=f.fd'),
 ('index','let x=f[0]'),('write-property','set f.length=1'),('standalone','do f'),
 ('defer-owner','defer close(f)'),('release-discard','do release(f)'),
 ('release-as-scalar','let x=release(f)'),('read-discard','let b=Bytes()\ndo read_owned(f,b,1)'),
 ('release-twice','handle release(f)\nok v\nerr e\nend\nhandle release(f)\nok v2\nerr e2\nend'),
 ('read-after-release','handle release(f)\nok v\nerr e\nend\nlet b=Bytes()\nhandle read_owned(f,b,1)\nok n\nerr e2\nend'),
 ('post-branch-release','if 1\n handle release(f)\n ok v\n err e\n end\nend\nlet b=Bytes()\nhandle read_owned(f,b,1)\nok n\nerr e2\nend'),
 ('wrong-bytes','let x=3\nhandle read_owned(f,x,1)\nok n\nerr e\nend'),
 ('missing-count','let b=Bytes()\nhandle read_owned(f,b)\nok n\nerr e\nend'),
]:
 add(name,'own f=File(path,0,0)\n'+body+'\nreturn ok(42)',good=False)
add('owner-parameter','own f=File(path,0,0)\ndo leak(f)\nreturn ok(42)',good=False,extra='fn leak(x:File)\nreturn 0\nend\n')
add('owner-to-helper','own f=File(path,0,0)\ndo leak(f)\nreturn ok(42)',good=False,extra='fn leak(x)\nreturn 0\nend\n')
add('let-constructor','let f=File(path,0,0)\nreturn ok(42)',good=False)
add('nested-owner','if 1\n own f=File(path,0,0)\nend\nreturn ok(42)',good=False)
add('wrong-result-owner','own f=File(path,0,0)\nreturn ok(42)',good=False,extra='result Other(u64,u64)\n') # replaced return annotation below
CASES[-1]=(CASES[-1][0],CASES[-1][1].replace('fn work(path,missing,expected):Outcome','fn work(path,missing,expected):Other'),False)
# Wrong owning result annotation / scalar function must not silently drop cleanup failure.
CASES.append(('scalar-owning-function',H+'fn main(argc,argv)\nown f=File(load64(argv+8),0,0)\nreturn 0\nend\n',False))
# Repeat owned calls in a live process; ordinary process exit cannot mask leaks.
add('repeated-400',"let i=0\nwhile i<400\n handle roundtrip(path)\n ok value\n  if value!=42\n   return err(99)\n  end\n err cause\n  return err(cause)\n end\n set i=i+1\nend\nreturn ok(42)",extra='fn roundtrip(path):Outcome\nown f=File(path,0,0)\nreturn ok(42)\nend\n')
add('mixed-owner-before-defer','own f=File(path,0,0)\nlet raw=open(path,0,0)\ndefer close(raw)\ndo close(expected)\nreturn ok(42)',1,65545)
add('mixed-defer-before-owner','let raw=open(path,0,0)\ndefer close(raw)\nown f=File(path,0,0)\ndo close(expected+1)\nreturn ok(42)',1,65545)
for n in [15,16]:
 add('combined-registrations-'+str(n+1),'let raw=open(path,0,0)\ndefer close(raw)\n'+'\n'.join(f'own f{i}=File(path,0,0)'for i in range(n))+'\nreturn ok(42)',good=n==15)
extra='record Order(value:u64)\nfn path_arg(path,p:Order)\n set p.value=p.value*10+1\n return path\nend\nfn flags_arg(p:Order)\n set p.value=p.value*10+2\n return 0\nend\nfn mode_arg(p:Order)\n set p.value=p.value*10+3\n return 0\nend\n'
add('open-argument-order','let p=Order(0)\nown f=File(path_arg(path,p),flags_arg(p),mode_arg(p))\nreturn ok(p.value)',0,123,extra=extra)
# After explicit release, a raw replacement may reuse the descriptor. The old
# owner must remain disarmed and must not close that replacement at its epilogue.
CASES.append(('released-owner-preserves-replacement',H+'record Saved(fd:u64)\nfn work(path,r:Saved):Outcome\n own f=File(path,0,0)\n handle release(f)\n ok value\n err cause\n  return err(cause)\n end\n let replacement=open(path,0,0)\n set r.fd=replacement\n return ok(42)\nend\nfn main(argc,argv)\n let path=load64(argv+8)\n let expected=open(path,0,0)\n do close(expected)\n let r=Saved(0)\n let answer=0\n handle work(path,r)\n ok value\n  set answer=value\n err cause\n  return 101\n end\n let closed=close(r.fd)\n let after=open(path,0,0)\n do close(after)\n return (answer!=42)|(r.fd!=expected)|(closed!=0)|(after!=expected)\nend\n',True))
# Successful writes alter a disposable fixture, then a separately opened owner
# reads back exact bytes. The Python controller independently checks the file too.
add('write-success','own f=File(path,2,0)\nlet b=Bytes()\nset b[0]=82\nset b[1]=70\nset b[2]=50\nhandle write_owned(f,b,3)\nok n\n if n!=3\n  return err(101)\n end\nerr cause\n return err(cause)\nend\nhandle release(f)\nok closed\nerr close_error\n return err(close_error)\nend\nown check=File(path,0,0)\nhandle read_owned(check,b,8)\nok n2\n if (n2==8)&(b[0]==82)&(b[1]==70)&(b[2]==50)&(b[3]==108)&(b[4]==111)\n  return ok(42)\n end\nerr cause2\n return err(cause2)\nend\nreturn err(102)')
add('write-zero','own f=File(path,2,0)\nlet b=Bytes()\nhandle write_owned(f,b,0)\nok n\n return ok(n)\nerr cause\n return err(cause)\nend\nreturn err(102)',0,0)
for count in [9,18446744073709551615]:
 add('write-over-capacity-'+str(count),'own f=File(path,2,0)\nlet b=Bytes()\nset b[0]=88\nhandle write_owned(f,b,'+str(count)+')\nok n\n return ok(3)\nerr cause\n return err(cause)\nend\nreturn ok(3)',1,22)
for order in ['owner-first','defer-first']:
 body=('own f=File(path,0,0)\nlet raw=open(path,0,0)\ndefer close(raw)'if order=='owner-first'else'let raw=open(path,0,0)\ndefer close(raw)\nown f=File(path,0,0)')
 add('mixed-repeated-'+order,'let i=0\nwhile i<400\n handle mixed(path)\n ok value\n  if value!=42\n   return err(99)\n  end\n err cause\n  return err(cause)\n end\n set i=i+1\nend\nreturn ok(42)',extra='fn mixed(path):Outcome\n'+body+'\nreturn ok(42)\nend\n')
rows=[]
with tempfile.TemporaryDirectory(prefix='rf2-owner-independent-')as tmp:
 root=Path(tmp);sample=root/'input.txt';sample.write_bytes(b'hello owned file\n');missing=root/'absent'
 for opt in [False,True]:
  for name,src,good in CASES:
   sample.write_bytes(b'hello owned file\n')
   path=D/(name+str(opt)+'.rf2');path.write_text(src);out=path.with_suffix('.bin');p=subprocess.run([C,path,out]+(['--opt']if opt else[]),capture_output=True,timeout=30)
   row={'name':name,'optimized':opt,'expectedAdmission':good,'compileExit':p.returncode,'sourceSHA256':hashlib.sha256(src.encode()).hexdigest()}
   if good:
    assert p.returncode==0,(name,opt,p.stderr.decode());subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);q=subprocess.run([out,sample,missing],capture_output=True,timeout=10);row.update(runExit=q.returncode,stdout=q.stdout.decode(errors='replace'),stderr=q.stderr.decode(errors='replace'));assert q.returncode==0,(row,q.stderr)
   else:assert p.returncode==1 and not out.exists(),(row,p.stderr.decode())
   if good:assert sample.read_bytes()==(b'RF2lo owned file\n'if name=='write-success'else b'hello owned file\n'),(name,'unexpected file bytes',sample.read_bytes())
   row['passed']=True;rows.append(row)
report={'passed':True,'checks':len(rows),'nativeExecutions':sum(x['expectedAdmission']for x in rows),'compileRefusals':sum(not x['expectedAdmission']for x in rows),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'scope':'Independent default/optimized owned-file admission and in-process fd reuse/error oracles. Deliberate raw close injects cleanup errors outside the checked ownership contract. Finite host checks, not whole-compiler proof or protection against unsafe raw descriptors.','results':rows}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='results'},indent=2));print(D/'report.json')
