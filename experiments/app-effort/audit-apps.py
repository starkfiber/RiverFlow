"""After authoring, bind final RF2 source to graded images and replay fresh applications.
Never repairs an attempt, changes original grades, or charges replay time to model construction.
"""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys
R=Path(__file__).resolve().parents[2]
if len(sys.argv)!=4:raise SystemExit('Usage: audit-apps.py V2-DIRECTORY V3-DIRECTORY NEW-DIRECTORY')
V2,V3,D=[Path(x).resolve()for x in sys.argv[1:]];D.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for label,folder,expected in [('v2',V2,6),('v3',V3,4)]:
 results=json.loads((folder/'RESULTS.json').read_text());assert len(results['trialResults'])==expected
 for trial in results['trialResults']:
  W=folder/(str(trial['attempt'])+'-'+trial['arm']);work=D/(label+'-'+W.name);work.mkdir();replay=work/'replay';replay.mkdir()
  for rel,wanted in trial['sdkFiles'].items():
   src=W/rel;assert src.is_file()and not src.is_symlink()and sha(src)==wanted;target=replay/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
  shutil.copy2(W/'launch.json',replay/'launch.json');rebuild=None;probes=[]
  if trial['arm']!='python':
   original=W/'app';sign=subprocess.run(['/usr/bin/codesign','-d','-vv',str(original)],capture_output=True,text=True,check=True);identity=re.search(r'^Identifier=(.+)$',sign.stderr,re.M).group(1)
   for number,flags in enumerate([['--compact','--opt'],['--opt'],['--compact'],[]]):
    build=work/('build-'+str(number));build.mkdir();out=build/'app'
    q=subprocess.run([str(W/'rf2c'),str(W/'main.flow'),str(out),*flags],cwd=W,capture_output=True,timeout=30)
    probe=dict(flags=flags,exit=q.returncode,diagnostic=(q.stdout+q.stderr).decode(errors='replace')[:500]);probes.append(probe)
    if q.returncode:continue
    subprocess.run(['/usr/bin/codesign','-s','-','--identifier',identity,str(out)],check=True,capture_output=True)
    probe['sha256']=sha(out);probe['matchesGradedImage']=sha(out)==sha(original)
    if probe['matchesGradedImage']:
     rebuild=dict(entry='main.flow',compilerSHA256=sha(W/'rf2c'),flags=flags,imageSHA256=sha(out),signatureIdentifier=identity,matched=True);shutil.copy2(out,replay/'app');break
   if rebuild is None:
    (work/'REBUILD-FAILURE.json').write_text(json.dumps(probes,indent=2)+'\n');raise AssertionError(('Final source does not reproduce graded image',W))
  # Fresh Python directories omit bytecode caches; RF2 uses exact freshly rebuilt image.
  grader=folder/'grade.py';out=work/'GRADE.json';p=subprocess.run([sys.executable,str(grader),str(replay),str(out)],cwd=R,capture_output=True,timeout=120);(work/'grader.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
  grade=json.loads(out.read_text());row=dict(study=label,attempt=trial['attempt'],arm=trial['arm'],rebuild=rebuild,rebuildProbes=probes,originalGradeSHA256=sha(W/'GRADE.json'),replayGradeSHA256=sha(out),originalAllPassed=trial['grade']['allPassed'],replayAllPassed=grade['allPassed'],checks=grade['checks'],passed=grade['passed'],failures=[x for x in grade['results']if not x['passed']],sourceChanges=0)
  if label=='v2'and trial['arm']=='newRF2':
   # Diagnostic details only: identical checks, no score relaxation or source repair.
   text=grader.read_text()
   for name in('wrong CSRF','duplicate field','unknown field'):
    old="check('GUI "+name+" no effect',code in(400,403)and db.read_bytes()==before)";new=old[:-1]+",dict(status=code,dataUnchanged=db.read_bytes()==before))";assert text.count(old)==1;text=text.replace(old,new)
   diagnostic=work/'grade-diagnostic.py';diagnostic.write_text(text);detail=work/'DIAGNOSTIC.json';p=subprocess.run([sys.executable,str(diagnostic),str(replay),str(detail)],cwd=R,capture_output=True,timeout=120);assert p.returncode==0
   d=json.loads(detail.read_text());row['statusDiagnostics']=[x for x in d['results']if x['name']in('GUI wrong CSRF no effect','GUI duplicate field no effect','GUI unknown field no effect')];row['diagnosticGraderSHA256']=sha(diagnostic);row['diagnosticReportSHA256']=sha(detail)
  rows.append(row);(D/'RESULTS.json').write_text(json.dumps(dict(controllerSHA256=sha(Path(__file__)),kind='post-construction source/image binding and fresh replay, not additional model attempts',results=rows),indent=2)+'\n');print(json.dumps(dict(study=label,attempt=row['attempt'],arm=row['arm'],byteIdenticalRebuild=bool(rebuild),allPassed=grade['allPassed'],checks=grade['checks'],passed=grade['passed'])),flush=True)
print(json.dumps(dict(report=str(D/'RESULTS.json'))),flush=True)
