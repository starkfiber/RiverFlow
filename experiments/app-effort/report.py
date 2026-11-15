"""Bind completed construction studies and native qualification; never drop a failed run.
Raw account/session traces stay local. Public source bundles contain no binaries or databases.
"""
from pathlib import Path
import datetime,hashlib,io,json,os,shutil,statistics,subprocess,sys,tarfile,tempfile
R=Path(__file__).resolve().parents[2]
if len(sys.argv)!=5:raise SystemExit('Usage: report.py V2-DIRECTORY V3-DIRECTORY QUALIFICATION-DIRECTORY NEW-DIRECTORY')
V2,V3,Q,D=[Path(x).resolve()for x in sys.argv[1:]];D.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=R/'artifacts/app-effort-047-b/build/program';CS=C.parent.parent/'compiler.flow'
q=json.loads((Q/'RESULTS.json').read_text());assert len(q['results'])==15 and all(x['exit']==0 for x in q['results']);assert q['compilerSHA256']==sha(C)
selfgen=json.loads((Q/'SELF.json').read_text());assert selfgen['passed']and selfgen['selfSHA256']==sha(C)
studies=[]
for name,folder,count in [('v2',V2,6),('v3',V3,4)]:
 frozen=json.loads((folder/'FROZEN.json').read_text());raw=json.loads((folder/'RESULTS.json').read_text());assert len(raw['trialResults'])==count
 trials=[]
 for row in raw['trialResults']:
  W=folder/(str(row['attempt'])+'-'+row['arm']);assert sha(W/'TRACE.jsonl')==row['traceSHA256'];assert sha(W/'PROMPT.txt')==row['promptSHA256'];assert sha(folder/'grade.py')==frozen['graderSHA256']
  assert json.loads((W/'GRADE.json').read_text())==row['grade']
  for rel,wanted in row['sdkFiles'].items():assert sha(W/rel)==wanted,(W.name,rel)
  events=[json.loads(line)for line in(W/'TRACE.jsonl').read_text().splitlines()];usage=[e['usage']for e in events if isinstance(e.get('usage'),dict)];assert usage==row['reportedUsage']
  assert usage,'Never substitute token estimates'
  total={key:sum(x.get(key,0)for x in usage)for key in('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')};total['uncached_input_tokens']=total['input_tokens']-total['cached_input_tokens']
  commands=[e['item']for e in events if e['type']=='item.completed'and e.get('item',{}).get('type')=='command_execution'];assert len(commands)==row['completedCommands']
  runtime='python-source'
  if row['arm']!='python':
   expected=frozen['oldCompilerSHA256']if row['arm']=='oldRF2'else frozen['newCompilerSHA256'];assert sha(W/'rf2c')==expected,'Provided compiler was modified';runtime=sha(W/'app')
  trials.append(dict(attempt=row['attempt'],arm=row['arm'],seconds=row['seconds'],usage=total,commands=len(commands),exit=row['exit'],timedOut=row['timedOut'],checks=row['grade']['checks'],passed=row['grade']['passed'],allPassed=row['grade']['allPassed'],failures=[x for x in row['grade']['results']if not x['passed']],humanRepairsDuringAttempt=row['humanRepairs'],traceSHA256=row['traceSHA256'],promptSHA256=row['promptSHA256'],gradeSHA256=sha(W/'GRADE.json'),taskSHA256=sha(W/'TASK.md'),sourceFiles=row['sdkFiles'],runtimeIdentity=runtime))
 groups={}
 for arm in frozen['order']:
  if arm in groups:continue
  a=[x for x in trials if x['arm']==arm];groups[arm]=dict(attempts=len(a),fullyPassed=sum(x['allPassed']for x in a),medianSeconds=statistics.median(x['seconds']for x in a),medianCommands=statistics.median(x['commands']for x in a),medianUsage={k:statistics.median(x['usage'][k]for x in a)for k in trials[0]['usage']})
 studies.append(dict(name=name,protocol=frozen['protocol'],requestedModel=frozen['requestedModel'],requestedReasoningEffort=frozen['requestedReasoningEffort'],servedIdentity='Not inferred; no resolved served identity emitted in retained trace',cli=frozen['cli'],host=frozen['host'],frozenSHA256=sha(folder/'FROZEN.json'),rawResultsSHA256=sha(folder/'RESULTS.json'),graderSHA256=frozen['graderSHA256'],frozenInputs=frozen,results=trials,groups=groups))
assert studies[0]['graderSHA256']==studies[1]['graderSHA256']
qualification=[]
for row in q['results']:
 p=R/'tests/standalone'/row['name'];assert sha(p)==row['sourceSHA256'];stdout=Q/(row['name']+'.stdout');stderr=Q/(row['name']+'.stderr');assert sha(stdout)==row['stdoutSHA256']and sha(stderr)==row['stderrSHA256'];path=None
 for line in reversed(stdout.read_text().splitlines()):
  try:
   item=json.loads(line)
   if type(item)is dict:
    if 'report'in item:path=Path(item['report']);break
    if 'directory'in item:path=Path(item['directory'])/'RESULTS.json';break
  except ValueError:
   if line.startswith('/')and line.endswith('/report.json'):path=Path(line);break
 if path is None:path=Q/(row['name']+'.report.json')
 report=json.loads(path.read_text());count=report.get('checks',report.get('cases'))
 if isinstance(count,list):count=len(count)
 if type(count)is not int:count=None
 qualification.append(dict(name=row['name'],exit=row['exit'],sourceSHA256=row['sourceSHA256'],checksOrCases=count,reportSHA256=sha(path),localReport=str(path.relative_to(R)),report=report if row['name']=='verify.py'else None))
receipt=dict(schema='rf2.app-effort.qualification.v1',edition='0.47-source-candidate-B',recordedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),baselineCommit='8d440214aeef70c901d09649af55ac6bdb62cc13',compilerSourceSHA256=sha(CS),compilerSHA256=sha(C),selfGeneration=selfgen,qualification=qualification,studies=studies,limitations=['Warm SDK assembly: compiler/library/documentation development is setup excluded from trial construction time.','Two attempts per arm, one Mac and one requested model/effort: exploratory, no universal productivity or performance claim.','Reported input includes cached input; uncached/output are separate. No billing, runtime speed, energy or hardware claim.','V2 task omitted exact error statuses while its grader required400/403; original stricter grades stay. V3 clarifies this for both languages without changing grader.','A200 refusal is not proof of data modification; combined checks do not by themselves distinguish status and effect.','Heavy native qualification finished beforev3 timed calls. V2 parent setup/light checks overlapped remote authoring.','Stable/public0.46 downloads and original nine-tool runtime unchanged. Candidate source is not a newly qualified downloadable package.','R12 Linguist remains pending, nonblocking; broader platform gates remain unfinished.'],sources={str(p.relative_to(R)):sha(p)for p in sorted((R/'experiments/app-effort').rglob('*'))if p.is_file()and'__pycache__'not in str(p)})
(D/'APP-EFFORT-0.47.json').write_text(json.dumps(receipt,indent=2)+'\n')
# Retain exact frozen setup bytes; reconstructedv2 files were SHA-checked earlier.
source_root=D/'source-evidence';source_root.mkdir()
for study,folder in [('v2',V2),('v3',V3)]:
 snap=R/'artifacts/app-effort-public-setups'/study;frozen=json.loads((folder/'FROZEN.json').read_text())
 for rel,wanted in frozen['sourceFiles'].items():
  src=snap/rel;assert sha(src)==wanted;dest=source_root/study/'setup'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 for lib in('frozen-new-lib','frozen-old-lib'):shutil.copytree(folder/lib,source_root/study/lib)
 for extra in('FROZEN.json','grade.py','API.md','mcp_sdk.py'):
  if(folder/extra).exists():shutil.copy2(folder/extra,source_root/study/extra)
 for row in json.loads((folder/'RESULTS.json').read_text())['trialResults']:
  W=folder/(str(row['attempt'])+'-'+row['arm']);dest=source_root/study/'attempts'/W.name;dest.mkdir(parents=True)
  # Copy only final reviewed source/documents, not session traces, native images or DBs.
  for rel,wanted in row['sdkFiles'].items():
   src=W/rel;assert src.is_file()and not src.is_symlink();assert src.resolve().is_relative_to(W)
   if any(x in('__pycache__','.git','artifacts')for x in Path(rel).parts):continue
   target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
  for extra in('launch.json','PROMPT.txt','GRADE.json'):shutil.copy2(W/extra,dest/extra)
for name,src in [('compiler-A.flow',R/'artifacts/app-effort-047-a/compiler.flow'),('compiler-B.flow',CS)]:shutil.copy2(src,source_root/name)
shutil.copy2(D/'APP-EFFORT-0.47.json',source_root/'MEASUREMENTS.json');shutil.copy2(R/'LICENSE',source_root/'LICENSE')
(source_root/'README.txt').write_text('Source-only RF2 SDK construction evidence. All original failed grades are retained. No raw account/session traces, native binaries or databases are included. V2/newRF2 used compiler-A;v3/newRF2 used compiler-B. Rebuild those compiler sources with the qualified0.46 Mac compiler and ad-hoc sign. V2/oldRF2 used0.44 (see source-bound docs/NESTED-OWNERS-0.44.md). Model-generated final app entries and their modified SDK sources are in attempts/. Read each README and exact grade before using a sample. Missing fixture artifacts can be regenerated by their self-tests; do not call failed examples production templates. Python entries use stdlib only. Construction times exclude setup and external grading. Full report is MEASUREMENTS.json.\n')
manifest={str(p.relative_to(source_root)):dict(bytes=p.stat().st_size,sha256=sha(p))for p in sorted(source_root.rglob('*'))if p.is_file()};(source_root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=D/'APP-EFFORT-0.47-SOURCES.tar.gz'
with tarfile.open(archive,'w:gz')as t:
 for p in sorted(source_root.rglob('*')):
  if not p.is_file():continue
  data=p.read_bytes();info=tarfile.TarInfo('rf2-app-effort-0.47/'+str(p.relative_to(source_root)));info.size=len(data);info.mode=0o644;info.mtime=0;t.addfile(info,io.BytesIO(data))
(archive.with_name(archive.name+'.sha256')).write_text(sha(archive)+'  '+archive.name+'\n');print(json.dumps(dict(receipt=str(D/'APP-EFFORT-0.47.json'),archive=str(archive),archiveSHA256=sha(archive),files=len(manifest))))
