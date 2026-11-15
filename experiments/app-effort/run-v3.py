"""Post-failure follow-up; independently frozen, never overwritesv2."""
from pathlib import Path
import hashlib,json,os,platform,shutil,signal,subprocess,sys,tempfile,time
R=Path(__file__).resolve().parents[2];S=R/'experiments/app-effort';OLD=R/'experiments/development-task';sys.path.insert(0,str(S));from stage import stage
COLD=R/'artifacts/nested-owned-044-f/build/program';CNEW=R/'artifacts/app-effort-047-b/build/program';LIB=R/'artifacts/typed-booking-release-045/source/lib'
D=Path(tempfile.mkdtemp(prefix='app-effort-v3-trials-',dir=R/'artifacts'));cli=shutil.which('codex');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
clarification='\nHTTP status clarification: rejected CSRF tokens, duplicate fields and unknown fields must return400 or403 and leave the journal unchanged. Business overlap/stale errors may render a retained form with200 if the error and fresh saved state are visible.\n'
(D/'TASK.md').write_text((OLD/'TASK.md').read_text()+clarification)
assert cli,'Installed Codex CLI required'
source=(OLD/'grade.py').read_text();a="'conflict'in body.lower()or'already'in body.lower()";assert source.count(a)==1;source=source.replace(a,a+"or'revision changed'in body.lower()");a="'error'in rs[4]and'error'in rs[5]";assert source.count(a)==1;source=source.replace(a,"('error'in rs[4]or rs[4].get('result',{}).get('isError')is True)and'error'in rs[5]");(D/'grade.py').write_text(source)
manifest=dict(protocol='app-effort-sdk-v3',repositoryCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),host=platform.platform(),requestedModel='gpt-6.1-sol',requestedReasoningEffort='low',servedModelIdentity='not inferred; inspect emitted traces',cli=subprocess.check_output([cli,'--version'],text=True).strip(),order=['python','newRF2','newRF2','python'],maxSecondsPerAttempt=900,graderSHA256=sha(D/'grade.py'),baseTaskSHA256=sha(OLD/'TASK.md'),taskSHA256=sha(D/'TASK.md'),sourceFiles={str(p.relative_to(R)):sha(p)for p in sorted(S.rglob('*'))if p.is_file()and'__pycache__'not in str(p)},oldCompilerSHA256=sha(COLD),newCompilerSHA256=sha(CNEW),trialResults=[])
stage(D/'frozen-new-lib');shutil.copytree(LIB,D/'frozen-old-lib')
for name in('API.md','mcp_sdk.py','api-index.py','api-cards.json','build-docs.py'):shutil.copy2(S/name,D/name)
subprocess.run([sys.executable,str(D/'build-docs.py'),str(CNEW),str(D/'frozen-new-lib'),str(D/'frozen-docs')],check=True,capture_output=True)
manifest['nativeAPILookupSHA256']=sha(D/'frozen-docs/rf2-doc')
manifest['taskClarification']='All arms receive explicit400/403 rejection requirement, already required by the unchanged grader.'
manifest['newLibraryFiles']={p.name:sha(p)for p in sorted((D/'frozen-new-lib').iterdir())}
manifest['oldLibraryFiles']={p.name:sha(p)for p in sorted((D/'frozen-old-lib').iterdir())}
(D/'FROZEN.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(dict(directory=str(D),frozenSHA256=sha(D/'FROZEN.json'))),flush=True)
for n,arm in enumerate(manifest['order'],1):
 if shutil.disk_usage(D).free<4*1024**3:print('Stopped: less than4GiB free',flush=True);break
 W=D/f'{n}-{arm}';W.mkdir();shutil.copy2(D/'TASK.md',W/'TASK.md')
 if arm in('oldRF2','newRF2'):
  shutil.copy2(COLD if arm=='oldRF2'else CNEW,W/'rf2c');(W/'rf2c').chmod(0o755)
  if arm=='oldRF2':shutil.copytree(D/'frozen-old-lib',W/'lib');shutil.copy2(OLD/'SDK-RF2.md',W/'SDK.md')
  else:
   shutil.copytree(D/'frozen-new-lib',W/'lib');shutil.copy2(D/'API.md',W/'SDK.md');shutil.copy2(D/'frozen-docs/rf2-doc',W/'rf2-doc');subprocess.run([sys.executable,str(D/'api-index.py'),str(W/'lib'),str(W/'SIGNATURES.md')],check=True)
 else:
  shutil.copy2(OLD/'booking_sdk.py',W/'booking_sdk.py');shutil.copy2(D/'mcp_sdk.py',W/'mcp_sdk.py');shutil.copy2(OLD/'SDK-PYTHON.md',W/'SDK.md')
  with(W/'SDK.md').open('a')as out:out.write('\nOptional generic protocol helper: from mcp_sdk import serve; serve(server_name,version,tool_name,description,zero_arg_callback). Callback returns a JSON object or raises. It implements the specified bounded legacy read-only MCP subset. You still assemble CLI, GUI, validation and the selected-path callback.\n')
 (W/'AGENTS.md').write_text('Isolated application-construction test. Work only in this directory. Read TASK.md and SDK.md. No other workspaces, prior attempts, remote services, installs, secrets, GitHub writes, external grader, delegation, Memory or shared compute. Preserve actual failures. Do not modify TASK.md or SDK.md. Prefer targeted API lookup and inspect only needed source functions (at most150 lines per read, unless a broader read is necessary and explained). Batch independent documentation queries and tests without skipping validations. Avoid dumping full libraries. RF2 has native ./rf2-doc symbol and ./rf2-doc --list. Python has its SDK guide and stdlib.\n')
 language='Python'if arm=='python'else'RF2'
 prompt=f'Build the complete Study Rooms application in {language} using TASK.md and SDK.md in this isolated directory. Implement, build, self-test and document it. Runtime source must be in this language; supplied libraries are starting SDKs, not a complete app. Deliver launch.json and README.md. Work autonomously inside this directory, no other workspace access, remote calls, installs, delegation or prebuilt app. Use actual tests and disclose limits, no fake claims. Do not edit TASK.md or SDK.md. You have one900second attempt.'
 prompt+=' Use targeted SDK/API retrieval before source inspection; keep source reads bounded. Preserve all failures and do not claim unseen grader results.'
 (W/'PROMPT.txt').write_text(prompt+'\n');command=[cli,'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--json','--sandbox','workspace-write','--model','gpt-6.1-sol','-c','model_reasoning_effort="low"','-c','approval_policy="never"','-C',str(W),'-']
 started=time.monotonic();timeout=False
 with(W/'TRACE.jsonl').open('wb')as out,(W/'STDERR.txt').open('wb')as err:
  child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=err,start_new_session=True);child.stdin.write(prompt.encode());child.stdin.close()
  try:code=child.wait(timeout=900)
  except subprocess.TimeoutExpired:
   timeout=True;os.killpg(child.pid,signal.SIGTERM)
   try:code=child.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);code=child.wait()
 elapsed=time.monotonic()-started;events=[];parse_errors=0
 for line in(W/'TRACE.jsonl').read_text(errors='replace').splitlines():
  try:events.append(json.loads(line))
  except ValueError:parse_errors+=1
 usage=[e['usage']for e in events if isinstance(e.get('usage'),dict)];commands=[e for e in events if e.get('type')=='item.completed'and e.get('item',{}).get('type')=='command_execution']
 try:q=subprocess.run([sys.executable,str(D/'grade.py'),str(W),str(W/'GRADE.json')],cwd=R,capture_output=True,timeout=120);grader_exit=q.returncode;(W/'GRADE-CONTROLLER.txt').write_bytes(q.stdout+q.stderr)
 except subprocess.TimeoutExpired:grader_exit='timeout'
 grade=json.loads((W/'GRADE.json').read_text())if(W/'GRADE.json').exists()else None
 result=dict(attempt=n,arm=arm,exit=code,timedOut=timeout,seconds=elapsed,reportedUsage=usage,usageAvailable=bool(usage),JSONLErrors=parse_errors,completedCommands=len(commands),traceSHA256=sha(W/'TRACE.jsonl'),promptSHA256=sha(W/'PROMPT.txt'),sdkFiles={str(p.relative_to(W)):sha(p)for p in sorted(W.rglob('*'))if p.is_file()and p.suffix in('.flow','.rf2','.py','.md')},graderExit=grader_exit,grade=grade,humanRepairs=0)
 manifest['trialResults'].append(result);(D/'RESULTS.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('grade','sdkFiles')}|dict(gradeAllPassed=grade['allPassed']if grade else False,gradePassed=grade['passed']if grade else None)),flush=True)
 if not events or any(e.get('type')=='error'and'auth'in str(e).lower()for e in events):print('Stopped on CLI/auth failure; no workaround',flush=True);break
print(json.dumps(dict(results=str(D/'RESULTS.json'))),flush=True)
