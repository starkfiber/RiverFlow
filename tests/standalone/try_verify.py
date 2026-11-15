"""Statement-level propagation, nominal refusals and native cleanup evidence."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
R=Path(__file__).resolve().parents[2]; C=Path(os.environ['RF2_TRY_COMPILER']).resolve()
BASE=Path(os.environ.get('RF2_TRY_BASELINE',str(C))).resolve()
D=Path(tempfile.mkdtemp(prefix='try-',dir=R/'artifacts')); checks=[]
HEADER='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\n'
CALL='fn checked(n):IO\n if n==0\n  return err(73)\n end\n return ok(n)\nend\n'
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok: (D/'FAILED.json').write_text(json.dumps(checks,indent=2));raise AssertionError((name,detail))
def build(name,source,opt,refusal=None,compiler=C):
 p=D/(str(len(checks))+'-'+name+'.flow');p.write_text(source);exe=p.with_suffix('')
 q=subprocess.run([str(compiler),str(p),str(exe),'--compact',*(['--opt']if opt else[])],capture_output=True,timeout=30)
 if refusal:
  check(name+' refusal',q.returncode!=0 and refusal in (q.stdout+q.stderr).decode(),(q.stdout+q.stderr).decode());check(name+' no image',not exe.exists());return
 check(name+' compile',q.returncode==0,(q.stdout+q.stderr).decode());subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],check=True,capture_output=True);return exe
def main(body,extra='',parent='IO'):
 return HEADER+extra+CALL+'fn work(n):'+parent+'\n'+body+'\nend\nfn main(argc,argv)\n handle work(argc-1)\n ok value\n  return value\n err cause\n  return cause\n end\n return 201\nend\n'
for opt in (False,True):
 implicit=build('root',main(' let v=try checked(n)\n set v=try checked(v+1)\n do try checked(v)\n return ok(v)'),opt)
 explicit=build('explicit',main(' let v=0\n handle checked(n)\n ok a\n  set v=a\n err e\n  return err(e)\n end\n handle checked(v+1)\n ok b\n  set v=b\n err f\n  return err(f)\n end\n handle checked(v)\n ok c\n err g\n  return err(g)\n end\n return ok(v)'),opt,compiler=BASE)
 for n in range(12):
  a=subprocess.run([str(implicit)]+['x']*n,capture_output=True);b=subprocess.run([str(explicit)]+['x']*n,capture_output=True)
  check('explicit equivalence '+str(opt)+' '+str(n),(a.returncode,a.stdout,a.stderr)==(b.returncode,b.stdout,b.stderr),[a.returncode,b.returncode])
 # Owned files must close on the primary-error jump; an invalid close must not replace it.
 resource='resource File(IO)\n'
 exe=build('owned-cleanup',main(' own file=File("/dev/null",0,0)\n let v=try checked(n)\n return ok(v)',resource),opt)
 for args,expected in [([],73),(['x'],1)]:
  q=subprocess.run([str(exe)]+args,capture_output=True);check('owned primary '+str(opt)+str(args),q.returncode==expected,q.returncode)
 # A closed borrowed descriptor creates a controlled cleanup failure, never a host failure.
 exe=build('cleanup-primary',main(' own file=File("/dev/null",0,0)\n do close(3)\n let v=try checked(n)\n return ok(v)',resource),opt)
 q=subprocess.run([str(exe)],capture_output=True);check('cleanup preserves error '+str(opt),q.returncode==73,q.returncode)
 q=subprocess.run([str(exe),'x'],capture_output=True);check('cleanup failure after success '+str(opt),q.returncode==9,q.returncode)
 nested=build('loop',main(' let i=0\n while i<n\n  if i<10\n   do try checked(i+1)\n  end\n  set i=i+1\n end\n return ok(i)'),opt)
 q=subprocess.run([str(nested),'a','b','c'],capture_output=True);check('loop '+str(opt),q.returncode==3,q.returncode)
 refusals=[('untyped',HEADER+CALL+'fn main(argc,argv)\n do try checked(1)\n return 0\nend\n','try requires a typed-result'),('wrong-error',main(' do try other()\n return ok(0)','result Other(u64,u64)\nfn other():Other\n return err(7)\nend\n'),'try error result must match'),('expression',main(' let v=try checked(1)+2\n return ok(v)'),'try is a complete statement'),('argument',main(' let v=checked(try checked(1))\n return ok(0)'),'unknown local'),('ordinary',main(' do try plain()\n return ok(0)','fn plain()\n return 1\nend\n'),'try requires a scalar typed result')]
 for name,source,message in refusals: build(name,source,opt,message)
 # After propagated failure, a fresh open must reuse descriptor3: owner closed.
 cleanup=HEADER+resource+CALL+'fn work():IO\n own file=File("/dev/null",0,0)\n do try checked(0)\n return ok(0)\nend\nfn main(argc,argv)\n let status=0\n handle work()\n ok impossible\n  return 91\n err cause\n  set status=cause\n end\n let fd=open("/dev/null",0,0)\n do close(fd)\n if (status!=73)|(fd!=3)\n  return 92\n end\n return 0\nend\n'
 exe=build('closed-after-propagation',cleanup,opt);q=subprocess.run([str(exe)],capture_output=True);check('owner actually closed '+str(opt),q.returncode==0,q.returncode)
 maxvalue=build('u64-success',main(' let v=try checked(18446744073709551615)\n if v!=18446744073709551615\n  return err(94)\n end\n return ok(0)'),opt);q=subprocess.run([str(maxvalue)],capture_output=True);check('u64 exact '+str(opt),q.returncode==0,q.returncode)
 owner_source=HEADER+CALL+'text Name(IO,64)\nrecord Row(name:own Name,id:u64)\nresult Ready(own Row,u64)\nfn make(n):Ready\n own row=Row(Name(),n)\n do try checked(n)\n do try text_append(row.name,2949)\n return ok(move(row))\nend\nfn run(n):IO\n handle make(n)\n ok own row:Row\n  return ok(row.id)\n err cause\n  return err(cause)\n end\n return err(201)\nend\nfn main(argc,argv)\n handle run(argc-1)\n ok complete\n  return complete\n err failure\n  return failure\n end\n return 201\nend\n'
 exe=build('owned-result-parent',owner_source,opt)
 for args,expected in[([],73),(['x'],1)]:
  q=subprocess.run([str(exe)]+args,capture_output=True);check('owned result nominal IO '+str(opt)+str(args),q.returncode==expected,q.returncode)
 forwarded=build('forwarded',main(' return checked(n)'),opt)
 for args,expected in[([],73),(['x'],1)]:
  q=subprocess.run([str(forwarded)]+args,capture_output=True);check('matching scalar forward '+str(opt)+str(args),q.returncode==expected,q.returncode)
 forwarded_cleanup=build('forwarded-cleanup',main(' own file=File("/dev/null",0,0)\n do close(3)\n return checked(n)',resource),opt)
 for args,expected in[([],73),(['x'],9)]:
  q=subprocess.run([str(forwarded_cleanup)]+args,capture_output=True);check('forward preserves cleanup contract '+str(opt)+str(args),q.returncode==expected,q.returncode)
 build('forward-wrong',main(' return other()','result Other(u64,u64)\nfn other():Other\n return ok(1)\nend\n'),opt,'forwarded result must match')
 build('forward-expression',main(' return checked(1)+2'),opt,'forwarding is a complete call')
 # Existing function named try remains legal: no prefix identifier follows it.
 exe=build('old-identifier',HEADER+'fn try(n)\n return n+1\nend\nfn main(argc,argv)\n return try(4)\nend\n',opt)
 q=subprocess.run([str(exe)],capture_output=True);check('identifier compatibility '+str(opt),q.returncode==5,q.returncode)
receipt=dict(schema='rf2.try-qualification.v1',compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),referenceCompilerSHA256=hashlib.sha256(BASE.read_bytes()).hexdigest(),checks=len(checks),passed=sum(x['passed']for x in checks),results=checks,scope='Statement-root scalar IO propagation; controlled close failure is not a host fault. Ordinary returns only.')
(D/'RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(D),checks=receipt['checks'],passed=receipt['passed'])))
