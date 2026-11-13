"""Independent native structured-array/ARM64-frame controls.

The SP probe patches only a disposable test function with two independently
assembled instructions. It is test instrumentation, not an RF2 source feature.
No network, production device, privileged VM or shared-memory operation occurs.
"""
from pathlib import Path
import hashlib,json,os,random,struct,subprocess,time
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
OLD=Path(os.environ.get('RF2_OLD_COMPILER',R/'output/rf2c-031-final')).resolve()
D=R/'artifacts/sprint-032'/('redteam-'+str(time.time_ns()));D.mkdir(parents=True)
ROWS=[];SERIAL=0;U=(1<<64)-1
PREFIX='profile RF2_SYSTEM_A64_V1\n'
COMPILER_SHA=hashlib.sha256(C.read_bytes()).hexdigest()
SOURCE_SHA=hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest()
CONTROLLER_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def run(args,data=None,timeout=30):
 return subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=timeout,env={'PATH':'/nonexistent'})
def sign(path):
 q=run(['/usr/bin/codesign','-s','-',path]);assert q.returncode==0,q.stderr

def build(label,body,opt=False,good=True,extra=(),compiler=C):
 global SERIAL
 SERIAL+=1;p=D/f'{SERIAL:04}-{label}';src=p.with_suffix('.rf2');src.write_text(body if body.startswith('profile ')else PREFIX+body)
 q=run([compiler,src,p,*(['--opt']if opt else[]),'--compact',*extra])
 if good:assert q.returncode==0,(label,opt,q.returncode,q.stderr)
 else:assert q.returncode!=0 and not p.exists(),(label,opt,q.returncode,q.stderr)
 return p,q

def check(label,body,opt=False,expected_exit=0,expected_stdout=b'',expected_stderr=b''):
 p,q=build(label,body,opt);unsigned=hashlib.sha256(p.read_bytes()).hexdigest();sign(p);q=run([p],timeout=10)
 assert(q.returncode,q.stdout,q.stderr)==(expected_exit,expected_stdout,expected_stderr),(label,opt,q.returncode,q.stdout,q.stderr)
 ROWS.append(dict(case=label,optimized=opt,outcome='executed',exit=q.returncode,unsignedSHA256=unsigned));return p

def reject(label,body,opt=False):
 p,q=build(label,body,opt,False);ROWS.append(dict(case=label,optimized=opt,outcome='compile-refusal',diagnostic=q.stderr.decode(errors='replace')[:300]))

def text_section(data):
 assert struct.unpack_from('<I',data)[0]==0xfeedfacf
 count=struct.unpack_from('<I',data,16)[0];pos=32;entry=None
 for _ in range(count):
  kind,size=struct.unpack_from('<II',data,pos)
  if kind==0x80000028:entry=struct.unpack_from('<Q',data,pos+8)[0]
  if kind==0x19:
   nsects=struct.unpack_from('<I',data,pos+64)[0]
   for i in range(nsects):
    sec=pos+72+i*80
    if data[sec:sec+16].rstrip(b'\0')==b'__text':return struct.unpack_from('<I',data,sec+48)[0]
  pos+=size
 if entry is not None:return entry
 raise AssertionError('no __text section or LC_MAIN entry')

def functions(path):
 result={}
 for line in Path(str(path)+'.functions').read_text().splitlines():
  f=line.split()
  if f and f[0]=='F':result[f[1]]=tuple(map(int,f[2:4]))
 return result

def assembler_oracle():
 asm=D/'frame-oracle.s';obj=D/'frame-oracle.o';asm.write_text('''.text
.globl _probe
_probe:
 mov x0, sp
 ret
 sub sp, sp, #4096
 str xzr, [sp]
 add sp, sp, #4096
 sub sp, sp, #64
 add sp, sp, #64
''')
 q=subprocess.run(['/usr/bin/clang','-arch','arm64','-c',str(asm),'-o',str(obj)],capture_output=True,timeout=30);assert q.returncode==0,q.stderr
 raw=obj.read_bytes();off=text_section(raw);words=list(struct.unpack_from('<7I',raw,off))
 assert words==[0x910003e0,0xd65f03c0,0xd14007ff,0xf90003ff,0x914007ff,0xd10103ff,0x910103ff],list(map(hex,words))
 ROWS.append(dict(case='independent-clang-ARM64-instruction-oracle',words=[hex(x)for x in words],outcome='encoded-matched'));return words[:2]

def frame_probe(opt,probe_words):
 body='''array Whole(u64,4096)
array Half(u64,2048)
fn stack_probe()
 return 0
end
fn descend(n)
 let a=Whole()
 let before=stack_probe()
 set a[0]=n
 set a[4095]=n+17
 let result=0
 if n>0
  set result=descend(n-1)
 end
 let after=stack_probe()
 return result|(before&15)|(after&15)|(before!=after)|(a[0]!=n)|(a[4095]!=(n+17))
end
fn main(argc,argv)
 let a=Whole()
 let b=Half()
 let before=stack_probe()
 set a[4095]=123
 set b[2047]=456
 let got=descend(12)
 let after=stack_probe()
 return got|(before!=after)|(before&15)|(after&15)|(a[4095]!=123)|(b[2047]!=456)
end
'''
 p,_=build('stack-probe',body,opt,extra=('--functions',));raw=bytearray(p.read_bytes());maps=functions(p);base=text_section(raw)
 off,size=maps['stack_probe'];assert size>=8
 raw[base+off:base+off+8]=struct.pack('<2I',*probe_words)
 for j in range(8,size,4):struct.pack_into('<I',raw,base+off+j,0xd503201f)
 # Independently decode entry-frame reservation: STP then SUB SP and page probes,
 # followed by MOV FP,SP. Reject non-SP SUBs or unprobed page-size decrements.
 mainoff,mainsize=maps['main'];words=list(struct.unpack_from('<'+str(mainsize//4)+'I',raw,base+mainoff))
 assert words[0]==0xa9bf7bfd,hex(words[0]);reserved=0;probes=0;i=1
 while words[i]!=0x910003fd:
  w=words[i]
  if(w&0xff8003ff)==0xd10003ff:
   imm=(w>>10)&4095;shift=(w>>22)&1;amount=imm<<(12 if shift else 0);assert amount and amount%16==0
   reserved+=amount
   if amount>=4096:assert amount==4096 and words[i+1]==0xf90003ff,(amount,list(map(hex,words[i:i+3])))
  elif w==0xf90003ff:probes+=1
  else:raise AssertionError(('unexpected prologue instruction',hex(w),i))
  i+=1;assert i<100
 expected=49152+64+(64 if opt else 0)
 assert reserved==expected,(opt,reserved,expected)
 assert probes>=12,(opt,probes)
 p.write_bytes(raw);sign(p);q=run([p]);assert q.returncode==0 and not q.stdout and not q.stderr,(q.returncode,q.stderr)
 ROWS.append(dict(case='large-frame-SP-alignment-restoration-and-recursive-canaries',optimized=opt,reservedBytes=reserved,pageTouches=probes,probe='test-only MOV x0,SP;RET patched into own function, verified by clang',prologueWords=[hex(w)for w in words[:i+1]],instrumentedSHA256=hashlib.sha256(p.read_bytes()).hexdigest(),outcome='executed'))

def value_cases(opt):
 for cap in [512,1024,4096]:
  expected=sum((i*37+17)&U for i in range(cap))&U
  body=f'''array Values(u64,{cap})
fn touch(a:Values)
 let i=0
 let sum=0
 while i<a.length
  if a[i]!=0
   return 1
  end
  set a[i]=i*37+17
  set sum=sum+a[i]
  set i=i+1
 end
 return sum!={expected}
end
fn main(argc,argv)
 let before=1234567
 let a=Values()
 let after=7654321
 let failed=touch(a)
 return failed|(before!=1234567)|(after!=7654321)|(a[0]!=17)|(a[{cap-1}]!={((cap-1)*37+17)&U})
end
'''
  check('u64-zero-write-borrow-'+str(cap),body,opt)
 for cap in [511,512,513,32768]:
  body=f'''array Bytes(u8,{cap})
fn touch(a:Bytes)
 let i=0
 while i<a.length
  if a[i]!=0
   return 1
  end
  set a[i]=(i*13+7)&255
  set i=i+1
 end
 set i=0
 while i<a.length
  if a[i]!=((i*13+7)&255)
   return 1
  end
  set i=i+1
 end
 return 0
end
fn main(argc,argv)
 let a=Bytes()
 return touch(a)|(a.length!={cap})|(a[{cap-1}]!={((cap-1)*13+7)&255})
end
'''
  check('packed-u8-zero-tail-'+str(cap),body,opt)
 body='''array A(u8,511)
array B(u8,512)
array C(u8,513)
array D(u64,512)
record Pair(left:u64,right:u64)
fn child(v)
 return v+1
end
fn main(argc,argv)
 let p=Pair(11,22)
 let a=A()
 let x=33
 let b=B()
 let y=44
 let c=C()
 let d=D()
 set a[510]=7
 set b[511]=8
 set c[512]=9
 set d[511]=18446744073709551615
 let got=child(66)
 return (p.left!=11)|(p.right!=22)|(x!=33)|(y!=44)|(got!=67)|(a[510]!=7)|(b[511]!=8)|(c[512]!=9)|(d[511]!=18446744073709551615)|(a[0]!=0)|(b[0]!=0)|(c[0]!=0)|(d[0]!=0)
end
'''
 check('mixed-packed-arrays-records-scalars',body,opt)
 body='''array A(u64,512)
fn borrow8(a:A,b:A,c,d,e,f,g,h)
 set a[511]=c+d+e+f+g+h
 return b[511]+a[511]
end
fn main(argc,argv)
 let a=A()
 let b=A()
 set b[511]=101
 let got=borrow8(a,b,1,2,3,4,5,6)
 return (got!=122)|(a[511]!=21)|(b[511]!=101)
end
'''
 check('eight-argument-typed-borrow-ABI',body,opt)
 body='''array A(u64,512)
array Large(u64,4096)
fn choose(a:A)
 set a[0]=100
 return 511
end
fn value(a:A)
 let scratch=Large()
 set scratch[4095]=9
 set a[0]=a[0]+1
 return scratch[4095]
end
fn main(argc,argv)
 let a=A()
 let before=67890
 set a[choose(a)]=value(a)
 return (a[0]!=101)|(a[511]!=9)|(before!=67890)
end
'''
 check('array-address-index-survives-large-RHS-call-and-order',body,opt)
 body='''array Whole(u64,4096)
array Half(u64,2048)
fn recurse(n)
 let a=Whole()
 let b=Half()
 let low=101
 let high=909
 if (a[4095]!=0)|(b[2047]!=0)
  return 100000
 end
 set a[4095]=n
 set b[2047]=n+11
 let child=0
 if n>0
  set child=recurse(n-1)
 end
 if (a[4095]!=n)|(b[2047]!=(n+11))|(low!=101)|(high!=909)
  return 100000
 end
 return child+n
end
fn main(argc,argv)
 return recurse(16)!=136
end
'''
 check('maximum-arena-recursive-activation-isolation',body,opt)
 # Repeated function calls must construct fresh zero-filled payloads.
 body='''array A(u64,512)
fn once(v)
 let a=A()
 if (a[0]!=0)|(a[511]!=0)
  return 1
 end
 set a[0]=v
 set a[511]=v+1
 return 0
end
fn main(argc,argv)
 let i=0
 let bad=0
 while i<30
  set bad=bad|once(i)
  set i=i+1
 end
 return bad
end
'''
 check('fresh-array-on-each-call',body,opt)
 # The declared budgets permit256 metadata slots plus49152 payload bytes.
 # This is the largest constructible frame today, below the defensive65536 cap.
 declarations=''.join(' let v'+str(i)+'='+str(i+1000)+'\n'for i in range(251))
 assertions='|'.join('(v'+str(i)+'!='+str(i+1000)+')'for i in range(251))
 body='array A(u64,4096)\narray B(u64,2048)\nfn helper()\nreturn 777\nend\nfn main(argc,argv)\n let a=A()\n let b=B()\n'+declarations+' let got=helper()\n set a[4095]=17\n set b[2047]=29\n return '+assertions+'|(got!=777)|(a[4095]!=17)|(b[2047]!=29)\nend\n'
 p,_=build('maximum-named-slots-plus-arena',body,opt,extra=('--functions',))
 raw=p.read_bytes();off,size=functions(p)['main'];base=text_section(raw);words=list(struct.unpack_from('<'+str(size//4)+'I',raw,base+off))
 assert words[0]==0xa9bf7bfd
 reserved=0;i=1;touches=0
 while words[i]!=0x910003fd:
  w=words[i]
  if(w&0xff8003ff)==0xd10003ff:
   amount=((w>>10)&4095)<<(12 if(w>>22)&1 else 0);assert amount and amount%16==0;reserved+=amount
   if amount>=4096:assert amount==4096 and words[i+1]==0xf90003ff
  else:assert w==0xf90003ff;touches+=1
  i+=1;assert i<100
 assert reserved==51200+(64 if opt else 0),(opt,reserved)
 sign(p);q=run([p]);assert q.returncode==0 and not q.stdout and not q.stderr,(opt,q.returncode,q.stderr)
 ROWS.append(dict(case='actual-maximum-256-slots-and49152-arena',optimized=opt,reservedBytes=reserved,pageTouches=touches,outcome='executed-scalar-and-array-canaries'))
 reject('257th-local-still-refuses',body.replace(' let got=helper()',' let beyond=0\n let got=helper()'),opt)


def boundary_cases(opt):
 for cap,kind in [(0,'u64'),(4097,'u64'),(32769,'u8')]:
  reject('declaration-budget-'+kind+'-'+str(cap),f'array A({kind},{cap})\nfn main(argc,argv)\nreturn 0\nend\n',opt)
 for token in ['0512','0x200','-1','18446744073709551616']:
  reject('noncanonical-'+token.replace('-','negative'),f'array A(u64,{token})\nfn main(argc,argv)\nreturn 0\nend\n',opt)
 reject('arena-one-word-over-budget','''array Whole(u64,4096)
array Half(u64,2048)
array One(u64,1)
fn main(argc,argv)
 let a=Whole()
 let b=Half()
 let c=One()
 return 0
end
''',opt)
 reject('byte-arena-padding-one-cell-over-budget','''array A(u8,32768)
array B(u8,16383)
array C(u8,1)
fn main(argc,argv)
 let a=A()
 let b=B()
 let c=C()
 return 0
end
''',opt)
 check('byte-arena-exact-budget','''array A(u8,32768)
array B(u8,16384)
fn main(argc,argv)
 let a=A()
 let b=B()
 set a[32767]=123
 set b[16383]=231
 return (a.length!=32768)|(b.length!=16384)|(a[32767]!=123)|(b[16383]!=231)|(a[0]!=0)|(b[0]!=0)
end
''',opt)
 for value in [256,U]:
  check('u8-value-overflow-'+str(value),'array A(u8,513)\nfn main(argc,argv)\nlet a=A()\nset a[512]='+str(value)+'\nreturn 0\nend\n',opt,2,b'',b'RF2 bounds\n')
 for index in [512,U]:
  body=f'''array A(u64,512)
fn effect()
 do write(1,"UNEXPECTED",10)
 return 9
end
fn main(argc,argv)
 let a=A()
 set a[{index}]=effect()
 return 0
end
'''
  check('bounds-before-RHS-'+str(index),body,opt,2,b'',b'RF2 bounds\n')
  check('bounds-read-'+str(index),'array A(u64,512)\nfn main(argc,argv)\nlet a=A()\nreturn a['+str(index)+']\nend\n',opt,2,b'',b'RF2 bounds\n')
 forbidden=[('copy','let a=A()\nlet b=a\nreturn 0'),('return','let a=A()\nreturn a'),('raw-escape','let a=A()\ndo write(1,a,8)\nreturn 0'),('rebind','let a=A()\nset a=A()\nreturn 0')]
 for label,body in forbidden:reject('ownership-'+label,'array A(u64,512)\nfn main(argc,argv)\n'+body+'\nend\n',opt)
 reject('view-freeze-still-rejects-write','''array B(u8,513)
view Slice(B)
fn main(argc,argv)
 let a=B()
 let v=Slice(a,0,2)
 set a[0]=5
 return 0
end
''',opt)


def scalar_compatibility():
 programs=[('arithmetic','fn main(argc,argv)\nreturn (17*19+4)//3\nend\n'),('calls','fn child(a,b,c,d,e,f,g,h)\nreturn a+b+c+d+e+f+g+h\nend\nfn main(argc,argv)\nreturn child(1,2,3,4,5,6,7,8)\nend\n'),('record','record Pair(x:u64,y:u64)\nfn main(argc,argv)\nlet p=Pair(17,23)\nreturn p.x+p.y\nend\n')]
 for opt in [False,True]:
  for label,body in programs:
   p,_=build('compat-'+label,body,opt);old,_=build('old-'+label,body,opt,compiler=OLD)
   assert p.read_bytes()==old.read_bytes(),(label,opt)
   ROWS.append(dict(case='no-array-byte-compat-'+label,optimized=opt,outcome='prior-compiler-exact-unsigned-bytes'))


def reuse_controls():
 cache=D/'pack';cache.mkdir(mode=0o700)
 body='''array Large(u64,512)
fn pure(v)
 let t=v*7
 return t+3
end
fn array_work(v)
 let a=Large()
 set a[511]=v
 return a[511]
end
fn main(argc,argv)
 return (pure(5)!=38)|(array_work(123)!=123)
end
'''
 src=D/'reuse-source.rf2';src.write_text(PREFIX+body)
 for stage in ['cold','warm','edited']:
  if stage=='edited':src.write_text(PREFIX+body.replace('set a[511]=v','set a[511]=v+1').replace('array_work(123)!=123','array_work(123)!=124'))
  clean=D/('reuse-clean-'+stage);cached=D/('reuse-cached-'+stage)
  a=run([C,src,clean,'--opt','--compact']);b=run([C,src,cached,'--opt','--compact','--reuse-pack',cache]);assert a.returncode==b.returncode==0,(a.stderr,b.stderr)
  assert clean.read_bytes()==cached.read_bytes();receipt=json.loads(Path(str(cached)+'.reuse.json').read_text())
  assert receipt['reused']==(0 if stage=='cold'else 1),(stage,receipt)
  assert receipt['ineligible']>=2,(stage,receipt)
  sign(cached);q=run([cached]);assert q.returncode==0 and not q.stdout and not q.stderr,(stage,q.stderr)
  ROWS.append(dict(case='array-function-never-admitted-scalar-reuse-'+stage,outcome='clean-byte-and-execution-match',receipt=receipt))

def main():
 oracle=assembler_oracle()
 scalar_compatibility()
 for opt in [False,True]:
  value_cases(opt);boundary_cases(opt);frame_probe(opt,oracle)
 reuse_controls()
 assert hashlib.sha256(C.read_bytes()).hexdigest()==COMPILER_SHA,'candidate changed during qualification'
 assert hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest()==SOURCE_SHA,'source changed during qualification'
 report=dict(passed=True,schema='rf2.structured.storage.independent.v1',compilerSHA256=COMPILER_SHA,compilerSourceSHA256=SOURCE_SHA,controllerSHA256=CONTROLLER_SHA,cases=len(ROWS),rows=ROWS,scope='Finite actual Apple Silicon Mac native tests, independent arithmetic/zeroing canaries and clang encoding oracle. SP instrumentation patches only disposable test functions. No all-program memory-safety, unlimited stack, concurrency, other-target or security certification claim.')
 (D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),passed=True,cases=len(ROWS))))
if __name__=='__main__':main()
