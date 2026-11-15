"""Explicit, local, counterbalanced Codex SDK-construction experiment. No remote MCP jobs."""
from pathlib import Path
import hashlib,json,os,platform,shutil,signal,subprocess,sys,tempfile,time
R=Path(__file__).resolve().parents[2];S=R/'experiments/development-task';C=R/'artifacts/nested-owned-044-f/build/program';LIB=R/'artifacts/typed-booking-release-045/source/lib'
D=Path(tempfile.mkdtemp(prefix='development-task-',dir=R/'artifacts'));cli=shutil.which('codex')
if not cli:raise SystemExit('Installed Codex CLI required. Do not substitute estimated usage.')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
version=subprocess.run([cli,'--version'],capture_output=True,text=True,check=True).stdout.strip()
manifest=dict(protocol='warm-complete-app-sdk-construction-v1',repositoryCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),host=platform.platform(),cli=version,order=['rf2','python','python','rf2'],maxSecondsPerAttempt=900,sourceFiles={str(p.relative_to(R)):sha(p)for p in sorted(S.iterdir())if p.is_file()},nativeCompilerSHA256=sha(C),libraryFiles={p.name:sha(p)for p in sorted(LIB.iterdir())if p.is_file()},trialResults=[])
(D/'FROZEN.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(dict(directory=str(D),frozenSHA256=sha(D/'FROZEN.json'))),flush=True)
for n,language in enumerate(manifest['order'],1):
 W=D/f'{n}-{language}';W.mkdir();shutil.copy2(S/'TASK.md',W/'TASK.md');shutil.copy2(S/f'SDK-{language.upper()}.md',W/'SDK.md')
 if language=='rf2':shutil.copy2(C,W/'rf2c');(W/'rf2c').chmod(0o755);shutil.copytree(LIB,W/'lib')
 else:shutil.copy2(S/'booking_sdk.py',W/'booking_sdk.py')
 (W/'AGENTS.md').write_text('This is an isolated SDK construction benchmark. Work only in this trial directory. Read TASK.md and SDK.md. No remote services, installs, secrets, other workspace reads/writes, GitHub activity, delegation or Memory/shared-compute tools. Do not access other attempts or the external grader. Preserve failures and never invent tests/usage.\n')
 prompt=f'Build the complete Study Rooms application in {language.upper()} using TASK.md and SDK.md in this isolated directory. Implement, build, test and document it. All app runtime logic must be in this language. No other workspace access, remote calls, installs, delegation or prebuilt application execution. The supplied libraries are starting SDKs, not a finished app. Deliver launch.json and README.md. Do not edit TASK.md or SDK.md. Work autonomously within this trial and report actual self-test outcomes and limitations. No fake claims.'
 (W/'PROMPT.txt').write_text(prompt+'\n')
 command=[cli,'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--json','--sandbox','workspace-write','-c','approval_policy="never"','-C',str(W),'-']
 started=time.monotonic();timed_out=False
 with(W/'TRACE.jsonl').open('wb')as out,(W/'STDERR.txt').open('wb')as err:
  child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=err,start_new_session=True);child.stdin.write(prompt.encode());child.stdin.close()
  try:code=child.wait(timeout=900)
  except subprocess.TimeoutExpired:
   timed_out=True;os.killpg(child.pid,signal.SIGTERM)
   try:code=child.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);code=child.wait()
 elapsed=time.monotonic()-started;events=[];parse_errors=0
 for line in(W/'TRACE.jsonl').read_text(errors='replace').splitlines():
  try:events.append(json.loads(line))
  except ValueError:parse_errors+=1
 usage=[e['usage']for e in events if isinstance(e.get('usage'),dict)];completed=[e for e in events if e.get('type')=='turn.completed'];commands=[e for e in events if e.get('type')=='item.completed'and e.get('item',{}).get('type')=='command_execution']
 grade=subprocess.run([sys.executable,str(S/'grade.py'),str(W),str(W/'GRADE.json')],cwd=R,capture_output=True,timeout=120);(W/'GRADE-CONTROLLER.txt').write_bytes(grade.stdout+grade.stderr)
 result=dict(attempt=n,language=language,exit=code,timedOut=timed_out,seconds=elapsed,completedTurns=len(completed),reportedUsage=usage,usageAvailable=bool(usage),JSONLErrors=parse_errors,completedCommands=len(commands),traceSHA256=sha(W/'TRACE.jsonl'),promptSHA256=sha(W/'PROMPT.txt'),graderExit=grade.returncode,grade=json.loads((W/'GRADE.json').read_text())if(W/'GRADE.json').is_file()else None,humanRepairs=0)
 manifest['trialResults'].append(result);(D/'RESULTS.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='grade'}|dict(gradeAllPassed=result['grade']['allPassed']if result['grade']else False)),flush=True)
print(json.dumps(dict(results=str(D/'RESULTS.json'))),flush=True)
