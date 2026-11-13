"""Native check-only command: no publication, clean status and independent byte oracles."""
from pathlib import Path
import hashlib,json,os,subprocess,time,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'bootstrap'))
from seed import Compiler
D=R/'artifacts/check-only';D.mkdir(exist_ok=True);C=Path(os.environ['RF2_TEST_COMPILER']).resolve();OLD=Path(os.environ.get('RF2_OLD_COMPILER',R/'output/rf2c-031-diagnostics-v3')).resolve();W=D/('verify-'+str(time.time_ns()));W.mkdir();WORK=W/'workspace';WORK.mkdir();O=W/'oracles';O.mkdir();ROWS=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():return {str(p.relative_to(WORK)):dict(sha=digest(p),size=p.stat().st_size,mode=p.stat().st_mode,mtime=p.stat().st_mtime_ns)for p in WORK.rglob('*')if p.is_file()}
def run(args):return subprocess.run(list(map(str,args)),capture_output=True,timeout=30,cwd=WORK,env={'PATH':'/nonexistent'})
H='profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n'
for name,text,valid in [('valid',H+' return 0\nend\n',True),('bad-local',H+' return absent\nend\n',False),('overflow',H+' return 18446744073709551616\nend\n',False),('missing-end',H+' return 0\n',False),('bad-intrinsic',H+' return load64(0,1)\nend\n',False),('array-bound','profile RF2_SYSTEM_A64_V1\narray A(u64,255)\nfn main(argc,argv)\n let a=A()\n return 0\nend\n',False),('owned-result','profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\nresource File(IO)\nfn f():IO\n own file=File("not-opened",0,0)\n return ok(0)\nend\nfn main(argc,argv)\n return 0\nend\n',True)]:
 p=WORK/(name+'.rf2');p.write_text(text);before=snapshot();q=run([C,'--check',p]);after=snapshot();assert before==after,(name,'modifiedworkspace');assert(q.returncode==0)==valid,(name,q.stderr)
 old=run([OLD,p,O/(name+'-old')]);assert q.returncode==old.returncode,(name,q.stderr,old.stderr)
 if valid:assert q.stdout==b'RF2 source checked; no executable written.\n'
 else:assert q.stderr==old.stderr,(name,q.stderr,old.stderr)
 ROWS.append(dict(case=name,accepted=valid,workspaceUnchanged=True,cleanCompilerStatusMatch=True))
 if valid:
  for k,flags in enumerate([[],['--opt'],['--opt','--compact']]):
   a=O/(name+'-candidate-'+str(k));b=O/(name+'-baseline-'+str(k));qa=run([C,p,a,*flags]);qb=run([OLD,p,b,*flags]);assert qa.returncode==qb.returncode==0 and a.read_bytes()==b.read_bytes(),name
   ROWS.append(dict(case=name,flags=flags,normalCompileByteMatch=True))
# Imports resolve normally but neither imported nor entry code executes.
(WORK/'helper.rf2').write_text('module helper\nfn f(x)\n return x+1\nend\n');p=WORK/'imports.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\nuse "helper.rf2"\nfn main(argc,argv)\n return f(0)\nend\n');before=snapshot();q=run([C,'--check',p]);assert q.returncode==0 and before==snapshot();ROWS.append(dict(case='imports',accepted=True,workspaceUnchanged=True))
for extra in [[],['--opt'],['--compact'],['--functions'],['--reuse-pack',str(WORK)],['--reuse-cache',str(WORK)],['extra']]:
 args=[C,'--check']+([]if not extra else[str(p),*extra]);before=snapshot();q=run(args);assert q.returncode==1 and before==snapshot();assert b'check requires exactly one source path' in q.stderr;ROWS.append(dict(case='extra-option-refusal',args=list(map(str,args[1:])),workspaceUnchanged=True))
before=snapshot();q=run([C,'--check',WORK/'absent.rf2']);assert q.returncode==1 and b'source open failed'in q.stderr and before==snapshot();ROWS.append(dict(case='missing-file',workspaceUnchanged=True))
# This program would create/write a supplied path when run. Check-only must not run it.
p=WORK/'writer.rf2';p.write_text(H+' let fd=open(load64(argv+8),3585,384)\n do write(fd,"executed",8)\n do close(fd)\n return 0\nend\n');before=snapshot();q=run([C,'--check',p]);assert q.returncode==0 and before==snapshot()
bin=O/'writer';assert run([C,p,bin,'--opt','--compact']).returncode==0;subprocess.run(['/usr/bin/codesign','-s','-',bin],check=True,capture_output=True);marker=O/'explicit-run-marker';q=run([bin,marker]);assert q.returncode==0 and marker.read_bytes()==b'executed';ROWS.append(dict(case='check-noexecute-positive-control',workspaceUnchanged=True,explicitRunCreatedExpectedMarker=True))
# Maintained independent encoder and a native default-mode fixed point for isolated compiler source.
p=R/'native/compiler/compiler.rf2';raw=Compiler().compile(p.read_text())[0];a=O/'self1';b=O/'self2';assert run([C,p,a]).returncode==0 and a.read_bytes()==raw;subprocess.run(['/usr/bin/codesign','-s','-',a],check=True,capture_output=True);assert run([a,p,b]).returncode==0 and b.read_bytes()==raw;ROWS.append(dict(case='default-self-fixedpoint',independentEncoderByteMatch=True,unsignedSHA256=hashlib.sha256(raw).hexdigest()))
report=dict(passed=True,compilerSHA256=digest(C),sourceSHA256=digest(R/'native/compiler/compiler.rf2'),controllerSHA256=digest(Path(__file__)),workspace=str(WORK),workspaceManifest=snapshot(),cases=ROWS,limits='Native trusted systems compiler. Check uses default compiler options and checks code generation without publication, not runtime safety. Imports still read trusted local files; no sandbox or new MCP effects. FIFO/device inputs deliberately not tested because existing reader can block.')
(W/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(W/'report.json'),cases=len(ROWS),passed=True)))
