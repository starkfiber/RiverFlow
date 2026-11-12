"""Independent native value-result ABI/lifetime and refusal probes.

Controlled tempfile descriptors test cleanup without relying on process exit.
No human review, security proof, performance or token-saving claim.
"""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,time
R=Path(__file__).resolve().parents[2]
C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-storage-results-candidate')).resolve()
D=R/'artifacts/structured-results-adversarial'/str(time.time_ns());D.mkdir(parents=True)
SOURCE=Path(os.environ.get('RF2_TEST_COMPILER_SOURCE',R/'native/compiler/compiler.rf2'));SOURCE_BYTES=SOURCE.read_bytes();(D/'working-compiler-source.rf2').write_bytes(SOURCE_BYTES)
H='profile RF2_SYSTEM_A64_V1\nrecord Stats(a:u64,b:u64,c:u64,d:u64)\nrecord Other(a:u64,b:u64,c:u64,d:u64)\nresult Report(Stats,u64)\nresult Scalar(u64,u64)\n'
M='fn make():Report\nlet s=Stats(11,22,33,44)\nreturn ok(s)\nend\n'
CASES=[]
def add(name,source,good=True,status=0):CASES.append((name,source,good,status))
def main(body):return 'fn main(argc,argv)\n'+body+'\nend\n'
def handled(body='return (s.a!=11)|(s.b!=22)|(s.c!=33)|(s.d!=44)', call='make()', err='return 2'):
 return 'handle '+call+'\nok s:Stats\n'+body+'\nerr e\n'+err+'\nend\nreturn 3'
add('four-fields',H+M+main(handled()))
for n in [1,2,3]:
 fields=','.join(f'f{i}:u64'for i in range(n));vals=','.join(str(17+i*41)for i in range(n));cmp='|'.join(f'(v.f{i}!={17+i*41})'for i in range(n))
 add(f'{n}-fields','profile RF2_SYSTEM_A64_V1\nrecord Small('+fields+')\nresult Report(Small,u64)\nfn make():Report\nlet s=Small('+vals+')\nreturn ok(s)\nend\n'+main('handle make()\nok v:Small\nreturn '+cmp+'\nerr e\nreturn 2\nend\nreturn 3'))
add('full-u64-register-payload',H+'fn make():Report\nlet s=Stats(18446744073709551615,9223372036854775808,81985529216486895,0)\nreturn ok(s)\nend\n'+main(handled('return (s.a!=18446744073709551615)|(s.b!=9223372036854775808)|(s.c!=81985529216486895)|s.d')))
add('parenthesized-record-return',H+'fn make():Report\nlet s=Stats(11,22,33,44)\nreturn ok(((s)))\nend\n'+main(handled()))
add('record-local-mutated-before-copy',H+'fn make():Report\nlet s=Stats(1,2,3,4)\nset s.a=11\nset s.b=22\nset s.c=33\nset s.d=44\nreturn ok(s)\nend\n'+main(handled()))
add('helper-before-return',H+'fn mutate(x:Stats)\nset x.a=11\nset x.b=22\nset x.c=33\nset x.d=44\nreturn 0\nend\nfn make():Report\nlet s=Stats(0,0,0,0)\ndo mutate(s)\nreturn ok(s)\nend\n'+main(handled()))
add('late-calls-do-not-clobber-returned-value',H+M+'fn clobber(a,b,c,d,e,f,g,h)\nlet x=Stats(111,222,333,444)\nreturn a+b+c+d+e+f+g+h+x.a\nend\n'+main(handled('do clobber(1,2,3,4,5,6,7,8)\nreturn (s.a!=11)|(s.b!=22)|(s.c!=33)|(s.d!=44)')))
add('forward-call',H+'fn wrapper():Report\nhandle later()\nok value:Stats\nreturn ok(value)\nerr cause\nreturn err(cause)\nend\nreturn err(99)\nend\nfn later():Report\nlet x=Stats(11,22,33,44)\nreturn ok(x)\nend\n'+main(handled(call='wrapper()')))
add('nested-wrapper-copy',H+M+'fn wrap():Report\nhandle make()\nok v:Stats\nreturn ok(v)\nerr e\nreturn err(e)\nend\nreturn err(99)\nend\nfn wrap2():Report\nhandle wrap()\nok w:Stats\nreturn ok((w))\nerr failure\nreturn err(failure)\nend\nreturn err(98)\nend\n'+main(handled(call='wrap2()')))
add('error-payload',H+'fn make():Report\nreturn err(18446744073709551615)\nend\n'+main(handled('return 1',err='return e!=18446744073709551615')))
add('scalar-field-helper-argument',H+M+'fn take(a,b,c,d)\nreturn (a!=11)|(b!=22)|(c!=33)|(d!=44)\nend\n'+main(handled('return take(s.a,s.b,s.c,s.d)')))
add('parenthesized-field-read',H+M+main(handled('return (((s)).a!=11)|((s).b!=22)|((s).c!=33)|((s).d!=44)')))
add('field-scalar-copies-escape-arm',H+M+main('let a=0\nlet b=0\nlet c=0\nlet d=0\nhandle make()\nok s:Stats\nset a=s.a\nset b=s.b\nset c=s.c\nset d=s.d\nerr e\nreturn 2\nend\nreturn (a!=11)|(b!=22)|(c!=33)|(d!=44)'))
add('nested-handlers-own-copies',H+M+main('handle make()\nok first:Stats\n handle make()\n ok second:Stats\n  return (first.a!=second.a)|(first.b!=second.b)|(first.c!=33)|(second.d!=44)\n err inner_error\n  return 2\n end\nerr outer_error\n return 3\nend\nreturn 4'))
add('loop-many-results',H+M+main('let i=0\nlet sum=0\nwhile i<1000\n handle make()\n ok v:Stats\n  set sum=sum+v.a+v.b+v.c+v.d\n err failure\n  return 1\n end\n set i=i+1\nend\nreturn sum!=110000'))
# Defers run after the record return has been copied into its register payload.
for count in [1,4,16]:
 body='let s=Stats(11,22,33,44)\n'+'\n'.join(f'let fd{i}=open(path,0,0)\ndefer close(fd{i})'for i in range(count))+'\nreturn ok(s)'
 add('defer-preserves-all-fields-'+str(count),H+'fn make(path):Report\n'+body+'\nend\n'+main('let path=load64(argv+8)\nlet before=open(path,0,0)\ndo close(before)\nlet answer=1\nhandle make(path)\nok s:Stats\nset answer=(s.a!=11)|(s.b!=22)|(s.c!=33)|(s.d!=44)\nerr e\nreturn 2\nend\nlet after=open(path,0,0)\ndo close(after)\nreturn answer|(after!=before)'))
add('defer-preserves-error',H+'fn make(path):Report\nlet fd=open(path,0,0)\ndefer close(fd)\nreturn err(1234567890123456789)\nend\n'+main(handled('return 1',call='make(load64(argv+8))',err='return e!=1234567890123456789')))
add('defer-close-error-keeps-record',H+'fn make(path):Report\nlet s=Stats(11,22,33,44)\nlet fd=open(path,0,0)\ndefer close(fd)\ndo close(fd)\nreturn ok(s)\nend\n'+main(handled(call='make(load64(argv+8))')))
# Borrowed output belongs to caller; after IO helper cleanup, wrapper copies it byvalue.
add('scalar-io-wrapper',H+'resource File(Scalar)\nfn collect(path,out:Stats):Scalar\nown f=File(path,0,0)\nset out.a=11\nset out.b=22\nset out.c=33\nset out.d=44\nreturn ok(0)\nend\nfn make(path):Report\nlet out=Stats(0,0,0,0)\nhandle collect(path,out)\nok n\nreturn ok(out)\nerr e\nreturn err(e)\nend\nreturn err(99)\nend\n'+main(handled(call='make(load64(argv+8))')))
# 2 parameters +248 ordinarylocals +5payloadslots +1errslot=256.
for n in [248,249]:
 add('frame-'+str(n),H+M+main('\n'.join(f'let x{i}=0'for i in range(n))+'\n'+handled()),n==248)
# Native functions can still use the old scalar result protocol in same source.
add('scalar-result-compatible',H+M+'fn old():Scalar\nreturn ok(42)\nend\n'+main('let answer=0\nhandle old()\nok n\nset answer=n\nerr e\nreturn 1\nend\nhandle make()\nok s:Stats\nreturn (answer!=42)|(s.d!=44)\nerr cause\nreturn 2\nend\nreturn 3'))
# Mutating a caller-owned input after the call must not mutate the returnedvalue.
add('borrowed-source-independent-value',H+'fn make(source:Stats):Report\nreturn ok(source)\nend\n'+main('let original=Stats(11,22,33,44)\nhandle make(original)\nok s:Stats\nset original.a=999\nset original.b=888\nset original.c=777\nset original.d=666\nreturn (s.a!=11)|(s.b!=22)|(s.c!=33)|(s.d!=44)\nerr failure\nreturn 2\nend\nreturn 3'))
add('nested-scalar-calls-construct-before-return',H+'fn id(x)\nreturn x\nend\nfn make():Report\nlet out=Stats(id(id(11)),id(id(22)),id(id(33)),id(id(44)))\nreturn ok(out)\nend\n'+main(handled()))
# Refusal probes: no pointer escape or payload mutation masquerading as a byvalue result.
for name,body in [
 ('direct-mutation','set s.a=99'),('binding-reassignment','set s=Stats(1,2,3,4)'),
 ('helper-mutation','do mutate(s)'),('helper-parentheses','do mutate(((s)))'),
 ('raw-store-payload','do store64(0,s)'),('raw-return-pointer','return s'),
 ('payload-copy-as-scalar','let alias=s'),('payload-arithmetic','let x=s+1'),
 ('payload-index','let x=s[0]'),('payload-compare','let x=s==0'),
]:
 extra='fn mutate(x:Stats)\nset x.a=99\nreturn 0\nend\n'
 add('refuse-'+name,H+M+extra+main(handled(body+'\nreturn 0')),False)
add('refuse-after-arm',H+M+main('handle make()\nok s:Stats\nerr e\nreturn 2\nend\nreturn s.a'),False)
add('refuse-opposite-arm',H+'fn make():Report\nreturn err(4)\nend\n'+main('handle make()\nok s:Stats\nreturn 0\nerr e\nreturn s.a\nend\nreturn 3'),False)
for annotation in ['',':Other',':u64']:
 add('refuse-annotation-'+(annotation or 'missing'),H+M+main('handle make()\nok s'+annotation+'\nreturn 0\nerr e\nreturn 2\nend\nreturn 3'),False)
add('refuse-scalar-annotated-record',H+'fn make():Scalar\nreturn ok(42)\nend\n'+main('handle make()\nok s:Stats\nreturn s.a\nerr e\nreturn 2\nend\nreturn 3'),False)
add('refuse-error-record-annotation',H+M+main('handle make()\nok s:Stats\nreturn 0\nerr e:Stats\nreturn 2\nend\nreturn 3'),False)
for name,ret in [('wrong-nominal','let x=Other(11,22,33,44)\nreturn ok(x)'),('scalar-in-record-ok','return ok(42)'),('record-in-err','let x=Stats(1,2,3,4)\nreturn err(x)')]:
 add('refuse-'+name,H+'fn make():Report\n'+ret+'\nend\n'+main(handled()),False)
add('refuse-record-in-scalar-result',H+'fn make():Scalar\nlet x=Stats(1,2,3,4)\nreturn ok(x)\nend\n'+main('return 0'),False)
add('refuse-structured-result-discard',H+M+main('do make()\nreturn 0'),False)
add('refuse-structured-result-as-scalar',H+M+main('let x=make()\nreturn 0'),False)
# Unsupported payload shapes must be refused at declaration, not accepted untiluse.
for name,decl in [
 ('five-fields','record Big(a:u64,b:u64,c:u64,d:u64,e:u64)\nresult Bad(Big,u64)'),
 ('record-error','record BadError(e:u64)\nresult Bad(u64,BadError)'),
 ('array-payload','array B(u8,8)\nresult Bad(B,u64)'),
 ('view-payload','array B(u8,8)\nview V(B)\nresult Bad(V,u64)'),
 ('owner-payload','result IO(u64,u64)\nresource File(IO)\nresult Bad(File,u64)'),
 ('nested-result','result A(u64,u64)\nresult Bad(A,u64)'),
 ('vector-payload','result IO(u64,u64)\nvector B(IO,65536)\nresult Bad(B,u64)'),
]:add('refuse-'+name,'profile RF2_SYSTEM_A64_V1\n'+decl+'\n'+main('return 0'),False)
add('refuse-resource-structured-result',H+'resource File(Report)\n'+main('return 0'),False)
add('refuse-owner-in-structured-function',H+'resource File(Scalar)\nfn make(path):Report\nown file=File(path,0,0)\nlet s=Stats(1,2,3,4)\nreturn ok(s)\nend\n'+main('return 0'),False)
rows=[]
with tempfile.TemporaryDirectory(prefix='rf2-structured-independent-')as tmp:
 sample=Path(tmp)/'input.txt';sample.write_bytes(b'original\n')
 for opt in [False,True]:
  for name,src,good,status in CASES:
   source=D/(name+str(opt)+'.rf2');source.write_text(src);out=source.with_suffix('.bin')
   p=subprocess.run([C,source,out]+(['--opt']if opt else[]),capture_output=True,timeout=30)
   row={'name':name,'optimized':opt,'expectedAdmission':good,'compileExit':p.returncode,'sourceSHA256':hashlib.sha256(src.encode()).hexdigest()}
   if good:
    assert p.returncode==0,(name,opt,p.stderr.decode());subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);q=subprocess.run([out,sample],capture_output=True,timeout=10);row.update(runExit=q.returncode,stdout=q.stdout.decode(errors='replace'),stderr=q.stderr.decode(errors='replace'));assert q.returncode==status,(row,status)
   else:assert p.returncode==1 and not out.exists(),(row,p.stderr.decode())
   assert sample.read_bytes()==b'original\n';row['passed']=True;rows.append(row)
report={'passed':True,'checks':len(rows),'nativeExecutions':sum(x['expectedAdmission']for x in rows),'compileRefusals':sum(not x['expectedAdmission']for x in rows),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256(SOURCE_BYTES).hexdigest(),'sourceHashScope':'Supplied compiler source or working source snapshot at run start; compiler binary hash recorded separately','scope':'Independent finite record-value ABI/lifetime, handler scope/immutability, cleanup register preservation and refusal probes in default/optimized modes. Scalar-only fields, u64 errors; no arbitrary deepownership or whole-compiler proof.','results':rows}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='results'},indent=2));print(D/'report.json')
