"""Independent finite native fixed-array layout, initialization and lifetime checks."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();OLD=Path(os.environ.get('RF2_OLD_COMPILER',R/'output/rf2c-031-final')).resolve();D=R/'artifacts/structured-storage'/('verify-'+str(time.time_ns()));D.mkdir(parents=True);ROWS=[];SERIAL=0

def run(args):return subprocess.run(list(map(str,args)),capture_output=True,timeout=30,env={'PATH':'/nonexistent'})
def check(name,source,expected=0,refuse=False,stdout=b'',stderr=None):
 global SERIAL
 for opt in [False,True]:
  SERIAL+=1;p=D/f'case-{SERIAL}.rf2';p.write_text(source);out=D/f'case-{SERIAL}';flags=['--compact']+(['--opt']if opt else[]);q=run([C,p,out,*flags])
  if refuse:assert q.returncode!=0 and not out.exists(),(name,opt,q.stderr)
  else:
   assert q.returncode==0,(name,opt,q.stderr);unsigned=hashlib.sha256(out.read_bytes()).hexdigest();q=run(['/usr/bin/codesign','-s','-',out]);assert q.returncode==0,q.stderr;q=run([out]);assert q.returncode==expected and q.stdout==stdout,(name,opt,q.returncode,q.stdout,q.stderr)
   if stderr is not None:assert stderr in q.stderr,(name,opt,q.stderr)
  ROWS.append(dict(case=name,optimized=opt,refused=refuse,expectedExit=None if refuse else expected,sourceSHA256=hashlib.sha256(p.read_bytes()).hexdigest()))

def program(decls,body,helpers=''):
 return 'profile RF2_SYSTEM_A64_V1\n'+decls+'\n'+helpers+'fn main(argc,argv)\n'+body+'\nend\n'
for n in [1,127,128,253,254,255,256,511,512,513,2048,4096]:
 s=program(f'array A(u64,{n})',' let before=123\n let a=A()\n let after=456\n let i=0\n while i<a.length\n  if a[i]!=0\n   return 3\n  end\n  set a[i]=i*7+1\n  set i=i+1\n end\n set i=0\n while i<a.length\n  if a[i]!=i*7+1\n   return 4\n  end\n  set i=i+1\n end\n return (before!=123)|(after!=456)')
 check('u64 length '+str(n),s)
for n in [1,7,8,9,255,256,511,512,513,4095,4096,4097,16384,32767,32768]:
 s=program(f'array A(u8,{n})',' let before=123\n let a=A()\n let after=456\n let i=0\n while i<a.length\n  if a[i]!=0\n   return 3\n  end\n  set a[i]=(i*11+3)&255\n  set i=i+1\n end\n set i=0\n while i<a.length\n  if a[i]!=((i*11+3)&255)\n   return 4\n  end\n  set i=i+1\n end\n return (before!=123)|(after!=456)')
 check('u8 length '+str(n),s)
check('exact49152 arena and register saves',program('array A(u64,4096)\narray B(u64,2048)',' let a=A()\n let b=B()\n let c=17\n let d=29\n let e=41\n set a[4095]=700\n set b[2047]=900\n let z=helper(c,d,e)\n return (z!=87)|(a[4095]!=700)|(b[2047]!=900)|(c!=17)|(d!=29)|(e!=41)','fn helper(a,b,c)\n return a+b+c\nend\n'))
check('borrowedlargearray',program('array A(u64,4096)',' let a=A()\n set a[4095]=98765\n return readtail(a)!=98765','fn readtail(a:A)\n return a[4095]\nend\n'))
check('recursiveframeisolation',program('array A(u64,4096)',' return recurse(3)!=4006','fn recurse(n)\n let a=A()\n if a[4095]!=0\n  return 90000\n end\n set a[4095]=1000+n\n if n\n  let child=recurse(n-1)\n  return a[4095]+child\n end\n return a[4095]\nend\n'))
check('mixedrecordresource-layout-preserved',program('array A(u8,513)\nrecord Pair(left:u64,right:u64)',' let p=Pair(7,9)\n let a=A()\n let q=Pair(11,13)\n set a[512]=255\n return (p.left!=7)|(p.right!=9)|(q.left!=11)|(q.right!=13)|(a[512]!=255)'))
check('boundsbeforeRHS',program('array A(u64,512)',' let a=A()\n set a[512]=effect()\n return 0','fn effect()\n do write(1,"BAD",3)\n return 1\nend\n'),expected=2,stderr=b'RF2 bounds')
for decl in ['array A(u64,4097)','array A(u8,32769)','array A(u64,0)','array A(u64,0512)','array A(u64,0x200)','array A(u64,18446744073709551615)']:
 check('invalid declaration '+decl,program(decl,' return 0'),refuse=True)
check('aggregatearena+8reject',program('array A(u64,4096)\narray B(u64,2048)\narray C(u64,1)',' let a=A()\n let b=B()\n let c=C()\n return 0'),refuse=True)
check('array nonescape return reject',program('array A(u64,512)',' let a=A()\n return a'),refuse=True)
check('array copying reject',program('array A(u64,512)',' let a=A()\n let b=a\n return 0'),refuse=True)
check('nestedownerreject',program('array A(u64,512)',' if 1\n  let a=A()\n end\n return 0'),refuse=True)
# No-owned-array programs preserve the prior exact unsigned code in each mode.
for name,source in [('small',R/'examples/function-changes/main.rf2'),('checksum',R/'examples/file-checksum.rf2')]:
 for opt in [False,True]:
  for compact in [False,True]:
   flags=(['--opt']if opt else[])+(['--compact']if compact else[]);new=D/f'new-{name}-{opt}-{compact}';old=D/f'old-{name}-{opt}-{compact}'
   q=run([C,source,new,*flags]);assert q.returncode==0,q.stderr;q=run([OLD,source,old,*flags]);assert q.returncode==0,q.stderr;assert new.read_bytes()==old.read_bytes(),(name,opt,compact)
   ROWS.append(dict(case='unchanged no-array '+name,optimized=opt,compact=compact,unsignedByteMatch=True))
report=dict(passed=True,schema='rf2.structured.storage.verification.v1',cases=ROWS,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits='Finite AppleSiliconMac native tests, not unlimited stack/heap or general memory safety. Guard-page/ABI instruction probes are separately reviewed.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(ROWS),report=str(D/'report.json'))))
