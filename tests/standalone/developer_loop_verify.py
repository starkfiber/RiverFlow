"""Native failure/ownership/build-loop controls; no model calls or HTTP load."""
from pathlib import Path
import concurrent.futures, fcntl, hashlib, json, os, subprocess, tempfile, time

R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_DEV_COMPILER']).resolve()
B=Path(os.environ['RF2_DEV_BASELINE']).resolve()
DEV=Path(os.environ['RF2_DEV_DRIVER']).resolve()
D=Path(tempfile.mkdtemp(prefix='developer-loop-checks-',dir=R/'artifacts'))
checks=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check(name, ok, detail=None):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    (D/'RESULTS.json').write_text(json.dumps(dict(checks=checks,allPassed=all(x['passed'] for x in checks)),indent=2)+'\n')
    if not ok:raise AssertionError((name,detail,D))
def compile(name,source,opt=False,compiler=C,refuse=None):
    p=D/(str(len(checks))+'-'+name+'.flow');p.write_text(source);exe=p.with_suffix('')
    q=subprocess.run([str(compiler),str(p),str(exe),'--compact',*(['--opt']if opt else[])],capture_output=True,timeout=30)
    text=(q.stdout+q.stderr).decode(errors='replace')
    if refuse:
        check(name+' refusal',q.returncode!=0 and refuse in text,text)
        check(name+' no image',not exe.exists());return
    check(name+' compile',q.returncode==0,text)
    subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],check=True,capture_output=True)
    return exe
HEADER='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\nrecord Row(value:u64)\nrecord Outer(child:Row)\nfn checked(n):IO\n if n==0\n  return err(73)\n end\n return ok(n)\nend\n'
for opt in (False,True):
    for nested in (False,True):
        typ='Outer'if nested else'Row';field='child.value'if nested else'value'
        init=' let row=Row(17)\n let outer=Outer(row)\n'if nested else' let outer=Row(17)\n'
        source=HEADER+'resource File(IO)\nfn work(row:'+typ+',n):IO\n own file=File("/dev/null",0,0)\n set row.'+field+'=try checked(n)\n return ok(9)\nend\nfn main(argc,argv)\n'+init+' let error=0\n handle work(outer,argc-1)\n ok done\n err cause\n  set error=cause\n end\n let fd=open("/dev/null",0,0)\n do close(fd)\n if fd!=3\n  return 200\n end\n if argc==1\n  if (outer.'+field+'!=17)|(error!=73)\n   return 201\n  end\n else\n  if (outer.'+field+'!=argc-1)|(error!=0)\n   return 202\n  end\n end\n return 0\nend\n'
        exe=compile('field-try',source,opt)
        for n in range(9):
            q=subprocess.run([str(exe),*(['x']*n)],capture_output=True)
            check('field value, preserved failure and actual File cleanup '+str((opt,nested,n)),q.returncode==0,[q.returncode,q.stderr.decode()])
        compile('old-field-refusal',source,opt,B,'unknown local')
    owned=HEADER+'text Name(IO,32)\nrecord Owned(label:own Name,id:u64)\nrecord Nested(row:own Owned,total:u64)\nfn work(n):IO\n own value=Nested(Owned(Name(),17),18)\n set value.row.id=try checked(n)\n set value.total=try checked(18446744073709551615)\n if (value.row.id!=n)|(value.total!=18446744073709551615)\n  return err(200)\n end\n return ok(n)\nend\nfn main(argc,argv)\n handle work(argc-1)\n ok value\n  return value\n err cause\n  return cause\n end\n return 201\nend\n'
    exe=compile('owned-nested-field',owned,opt)
    for args,wanted in [([],73),(['x'],1),(['x','x'],2)]:
        q=subprocess.run([str(exe),*args],capture_output=True);check('owned nested field '+str((opt,args)),q.returncode==wanted,q.returncode)
    invalid=HEADER+'result Other(u64,u64)\nfn other():Other\n return ok(7)\nend\nfn work(row:Row):IO\n set row.value=try other()\n return ok(0)\nend\nfn main(argc,argv)\n return 0\nend\n'
    compile('nominal-refusal',invalid,opt,refuse='try error result must match')
    compile('field-expression-refusal',invalid.replace('try other()','try checked(1)+1'),opt,refuse='try is a complete statement')
    compile('field-untyped-refusal',invalid.replace('fn work(row:Row):IO','fn work(row:Row)').replace('try other()','try checked(1)').replace('return ok(0)','return 0'),opt,refuse='try requires a typed-result')

# Original source path/line after imports, shared dependency dedup, and CRLF input.
for crlf in (False,True):
    sub=D/('map-crlf'if crlf else'map-lf');(sub/'lib').mkdir(parents=True)
    (sub/'main.flow').write_text('profile RF2_SYSTEM_A64_V1\nuse "lib/middle.flow"\nuse "lib/bad.flow"\nfn main(argc,argv)\n return middle()\nend\n')
    (sub/'lib/middle.flow').write_text('module middle\nuse "lib/bad.flow"\nfn middle()\n return bad()\nend\n')
    raw='module bad\n# original source location\nfn bad()\n return missing\nend\n'
    (sub/'lib/bad.flow').write_bytes(raw.replace('\n','\r\n').encode()if crlf else raw.encode())
    q=subprocess.run([str(C),str(sub/'main.flow'),str(sub/'program'),'--compact'],capture_output=True)
    check('imported source location '+str(crlf),q.returncode!=0 and b'/lib/bad.flow:4:'in q.stderr,q.stderr.decode())
    check('import error has no image '+str(crlf),not(sub/'program').exists())
    (sub/'lib/bad.flow').write_text('module bad\nfn bad()\n return 9\nend\n')
    (sub/'main.flow').write_text('profile RF2_SYSTEM_A64_V1\nuse "lib/middle.flow"\nfn main(argc,argv)\n return absent\nend\n')
    q=subprocess.run([str(C),str(sub/'main.flow'),str(sub/'program'),'--compact'],capture_output=True)
    check('entry source location '+str(crlf),q.returncode!=0 and b'/main.flow:4:'in q.stderr,q.stderr.decode())

# Many split runs, duplicate imports and an error after a multibyte comment.
mapped=D/'map-ranges';(mapped/'lib').mkdir(parents=True)
(mapped/'lib/shared.flow').write_text('module shared\nfn shared()\n return 1\nend\n')
lines=['profile RF2_SYSTEM_A64_V1']
for i in range(27):
    name='part'+str(i)
    (mapped/('lib/'+name+'.flow')).write_text('module '+name+'\nuse "lib/shared.flow"\n# தமிழ்\nfn '+name+'()\n return shared()\nend\n')
    lines+=['# preserved comment '+str(i),'use "lib/'+name+'.flow"']
lines+=['fn main(argc,argv)',' return missing','end']
(mapped/'main.flow').write_text('\n'.join(lines))
q=subprocess.run([str(C),str(mapped/'main.flow'),str(mapped/'program'),'--compact'],capture_output=True)
check('many origin ranges and no terminal newline',q.returncode!=0 and ('/main.flow:'+str(len(lines)-1)+':').encode()in q.stderr,q.stderr.decode())
problem=mapped/'lib/part26.flow';problem.write_text(problem.read_text().replace('return shared()','return absent'))
q=subprocess.run([str(C),str(mapped/'main.flow'),str(mapped/'program'),'--compact'],capture_output=True)
check('deduplicated dependency origin with UTF8',q.returncode!=0 and b'/lib/part26.flow:5:'in q.stderr,q.stderr.decode())

simple='profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return 7\nend\n'
root=D/'build';root.mkdir(mode=0o700);src=D/'app.flow';src.write_text(simple)
command=[str(DEV),str(C),str(src),str(root)]
def build(*extra,**kw):return subprocess.run([*command,*extra],capture_output=True,timeout=30,**kw)
for i in range(3):
    q=build();check('repeat build '+str(i),q.returncode==0,q.stderr.decode())
    check('repeat image executes '+str(i),subprocess.run([str(root/'program')]).returncode==7)
image=sha(root/'program')
src.write_text(simple.replace('return 7','return no_such_value'))
q=build();check('compile rejection',q.returncode!=0 and b'previous program was preserved'in q.stderr,q.stderr.decode())
check('failed compile keeps exact signed image',sha(root/'program')==image)
check('failed compile clears candidate',not list(root.glob('.rf2-candidate-*')))
src.write_text(simple)
with(root/'.rf2-dev.lock').open('r+b')as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    q=build();check('simultaneous builder refused',q.returncode==75,q.stderr.decode())
    check('contended build preserves image',sha(root/'program')==image)
q=build('--no-opt');check('explicit unoptimized build',q.returncode==0,q.stderr.decode())
for kind in ('symlink','hardlink','directory'):
    place=D/kind;place.mkdir(mode=0o700);other=D/(kind+'-canary');other.write_bytes(b'UNCHANGED')
    if kind=='symlink':(place/'program').symlink_to(other)
    elif kind=='hardlink':os.link(other,place/'program')
    else:(place/'program').mkdir()
    q=subprocess.run([str(DEV),str(C),str(src),str(place)],capture_output=True,timeout=30)
    check('unsafe output refused '+kind,q.returncode!=0,q.stderr.decode())
    check('canary unchanged '+kind,other.read_bytes()==b'UNCHANGED')
    check('unsafe output no candidate '+kind,not list(place.glob('.rf2-candidate-*')))
for mode in (0o755,0o770):
    place=D/('public-'+str(mode));place.mkdir(mode=mode);place.chmod(mode)
    q=subprocess.run([str(DEV),str(C),str(src),str(place)],capture_output=True,timeout=30)
    check('nonprivate directory refused '+str(mode),q.returncode!=0 and not(place/'program').exists(),q.stderr.decode())
place=D/'lock-symlink';place.mkdir(mode=0o700);(place/'.rf2-dev.lock').symlink_to(src)
q=subprocess.run([str(DEV),str(C),str(src),str(place)],capture_output=True,timeout=30)
check('lock symlink refused',q.returncode!=0 and src.read_text()==simple)

# A trusted fixture compiler exits after creating incomplete bytes. Signing must
# fail, and no incomplete executable may replace the last good program.
fake=compile('partial-compiler','profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n let fd=open(load64(argv+16),3585,448)\n do write(fd,"BROKEN",6)\n do close(fd)\n return 0\nend\n',True)
before=sha(root/'program')
q=subprocess.run([str(DEV),str(fake),str(src),str(root)],capture_output=True,timeout=30)
check('nonexecutable data refused before signing',q.returncode!=0,q.stderr.decode())
check('invalid image preserves old image',sha(root/'program')==before)
check('invalid image clears candidate',not list(root.glob('.rf2-candidate-*')))
malformed=compile('malformed-compiler','profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n let bytes=buffer("malformed",40)\n do store32(bytes,4277009103)\n do store32(bytes+4,16777228)\n do store32(bytes+12,2)\n do store32(bytes+16,1)\n do store32(bytes+20,8)\n do store32(bytes+32,4294967295)\n do store32(bytes+36,8)\n let fd=open(load64(argv+16),3585,448)\n do write(fd,bytes,40)\n do close(fd)\n return 0\nend\n',True)
q=subprocess.run([str(DEV),str(malformed),str(src),str(root)],capture_output=True,timeout=30)
check('malformed Mach-O signing failure',q.returncode!=0,q.stderr.decode())
check('signing failure preserves exact old image',sha(root/'program')==before)
check('signing failure clears private candidate',not list(root.glob('.rf2-candidate-*')))
q=subprocess.run([str(DEV),str(D/'missing-compiler'),str(src),str(root)],capture_output=True,timeout=30)
check('missing compiler failure',q.returncode==127,q.stderr.decode())
check('missing compiler preserves image',sha(root/'program')==before)
with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:
    results=list(pool.map(lambda _:build(),range(8)))
check('eight actual builders bounded outcome',all(x.returncode in(0,75)for x in results),[x.returncode for x in results])
check('eight builders include a commit',any(x.returncode==0 for x in results))
check('concurrent final image signed',subprocess.run(['/usr/bin/codesign','--verify',str(root/'program')],capture_output=True).returncode==0)
check('concurrent final image executes',subprocess.run([str(root/'program')]).returncode==7)
check('concurrent candidates cleared',not list(root.glob('.rf2-candidate-*')))
src.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n do write(1,"READY",5)\n let input=buffer("wait",1)\n do read(0,input,1)\n return 7\nend\n')
q=build();check('active-image fixture build',q.returncode==0,q.stderr.decode())
running=subprocess.Popen([str(root/'program')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
    check('old image active',running.stdout.read(5)==b'READY')
    src.write_text(simple.replace('return 7','return 9'))
    q=build();check('atomic publication while old program runs',q.returncode==0,q.stderr.decode())
    output,error=running.communicate(b'x',timeout=8)
    check('old process retains old code',running.returncode==7,[running.returncode,error.decode()])
    check('new launch sees new code',subprocess.run([str(root/'program')]).returncode==9)
finally:
    if running.poll()is None:running.kill();running.communicate()
report=dict(schema='rf2.developer-loop.native.v1',compilerSHA256=sha(C),baselineSHA256=sha(B),driverSHA256=sha(DEV),checks=checks,allPassed=all(x['passed']for x in checks),count=len(checks),scope='One Mac ARM64, controlled native failure fixtures; no human/model token or universal security claim.')
(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(directory=str(D),checks=len(checks),allPassed=report['allPassed'])),flush=True)
