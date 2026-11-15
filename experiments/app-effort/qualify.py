"""Sequential native qualification, after timed construction calls finish."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile,time
R=Path(__file__).resolve().parents[2];C=Path(sys.argv[1]).resolve();D=Path(os.environ['RF2_QUAL_RESUME']).resolve()if os.environ.get('RF2_QUAL_RESUME')else Path(tempfile.mkdtemp(prefix='app-effort-qualification-',dir=R/'artifacts'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if len(sys.argv)>2:
 previous=Path(sys.argv[2])/'RESULTS.json'
 while not previous.exists()or len(json.loads(previous.read_text())['trialResults'])!=6:time.sleep(5)
print(json.dumps(dict(directory=str(D),compilerSHA256=sha(C))),flush=True)
env=os.environ.copy();env.update({name:str(C)for name in['RF2_TRY_COMPILER','RF2_OWNED_ROW_COMPILER','RF2_NESTED_OWNER_COMPILER','RF2_FUNCTION_OWNER_COMPILER','RF2_OWNED_COMPILER','RF2_NESTED_COMPILER','RF2_STORE_COMPILER','RF2_TEST_COMPILER']});env.update(RF2_OWNED_ROWS_EXTENSION='1',RF2_TRY_BASELINE=str(R/'artifacts/owned-rows-046-c/build/program'),RF2_TEST_COMPILER_SOURCE=str(C.parent.parent/'compiler.flow'),RF2_TEST_BINARY=str(R/'artifacts/sprint-036/RF2-0.36-dev-macos-arm64/rf2'),RF2_TEST_VERSION='0.17.0',RF2_TEST_TOOLS='9',RF2_TEST_NODE='/Users/ik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node',RF2_TEST_REPORT=str(D/'CORE.json'))
files=['try_verify.py','app_effort_verify.py','app_policy_verify.py','structured_results_verify.py','multiple_views_verify.py','owned_rows_verify.py','nested_owned_verify.py','owned_functions_verify.py','owned_values_verify.py','application_values_verify.py','heap_collection_verify.py','typed_booking_verify.py','booking_web_verify.py','booking_agent_verify.py','verify.py'];rows=[]
if os.environ.get('RF2_QUAL_RESUME'):
 previous=D/'RESULTS.json';old=json.loads(previous.read_text());assert old['compilerSHA256']==sha(C)
 for row in old['results']:
  if row['exit']:break
  assert row['sourceSHA256']==sha(R/'tests/standalone'/row['name'])
  rows.append(row)
 retained=D/('BEFORE-RESUME-'+str(time.time_ns())+'.json');shutil.copy2(previous,retained)
 if(D/'RESUME.json').exists():shutil.copy2(D/'RESUME.json',D/('RETAINED-RESUME-'+str(time.time_ns())+'.json'))
 (D/'RESUME.json').write_text(json.dumps(dict(retainedFailureReport=retained.name,sha256=sha(retained),retainedPassedPrefix=len(rows),correction=os.environ.get('RF2_QUAL_RESUME_REASON','Explicit0.46owned-row extension mode; historical0.44 refusal becomes admitted control. No test expectation changed.')),indent=2)+'\n')
 files=files[len(rows):]
for name in files:
 if shutil.disk_usage(D).free<4*1024**3:raise RuntimeError('Disk guard below4GiB; no evidence deletion')
 p=R/'tests/standalone'/name;t=time.monotonic()
 jobenv=env.copy();jobenv['RF2_TEST_REPORT']=str(D/(name+'.report.json'))
 if name=='application_values_verify.py':jobenv['RF2_TEST_COMPILER']=str(R/'artifacts/sprint-036/RF2-0.36-dev-macos-arm64/rf2c')
 q=subprocess.run([sys.executable,str(p)],cwd=R,env=jobenv,capture_output=True,timeout=600);(D/(name+'.stdout')).write_bytes(q.stdout);(D/(name+'.stderr')).write_bytes(q.stderr);row=dict(name=name,sourceSHA256=sha(p),exit=q.returncode,seconds=time.monotonic()-t,stdoutSHA256=sha(D/(name+'.stdout')),stderrSHA256=sha(D/(name+'.stderr')));rows.append(row);(D/'RESULTS.json').write_text(json.dumps(dict(compilerSHA256=sha(C),results=rows),indent=2)+'\n');print(json.dumps(row),flush=True)
 if q.returncode:print(q.stderr.decode(errors='replace')[-1800:],flush=True);raise SystemExit(1)
selfdir=D/'self';selfdir.mkdir();q=subprocess.run([str(C),str(C.parent.parent/'compiler.flow'),str(selfdir/'program'),'--opt'],capture_output=True,timeout=60);q.check_returncode();subprocess.run(['/usr/bin/codesign','-s','-',str(selfdir/'program')],check=True,capture_output=True);assert sha(C)==sha(selfdir/'program'),'Self-generation mismatch'
print(json.dumps(dict(selfGenerationSHA256=sha(selfdir/'program'),passed=True)),flush=True);(D/'SELF.json').write_text(json.dumps(dict(compilerSHA256=sha(C),selfSHA256=sha(selfdir/'program'),passed=True),indent=2)+'\n')
