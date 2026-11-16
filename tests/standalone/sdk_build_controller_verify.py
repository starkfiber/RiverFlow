"""Mocked build-controller fault tests, not native execution or a real timeout."""
from pathlib import Path
import hashlib,importlib.util,json,os,tempfile
R=Path(__file__).resolve().parents[2]
BASE=Path(os.environ['RF2_PUBLIC046_COMPILER']).resolve()
D=Path(tempfile.mkdtemp(prefix='sdk-build-controller-',dir=R/'artifacts'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,passed,detail=None):
 checks.append(dict(name=name,passed=bool(passed),detail=detail))
 (D/'RESULTS.json').write_text(json.dumps(dict(schema='rf2.sdk-build-controller-mock.v1',kind='Mocked subprocess.TimeoutExpired: no build child command executed, no actual native compiler or60second timeout run',baselineSHA256=sha(BASE),checks=checks,allPassed=all(x['passed']for x in checks)),indent=2)+'\n')
 if not passed:raise AssertionError((name,detail,D))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.R=R;return m
partial_stdout=b'partial bridge output\n\xff';partial_stderr=b'partial diagnostic\n';calls=[]
def exercise(module,out):
 module.platform.platform()  # Prime host metadata before intercepting build children.
 original=module.subprocess.run
 def fail(command,**options):
  if not any(str(value).endswith("bootstrap.py")for value in command):
   return original(command,**options)
  calls.append(dict(command=command,options={k:str(v)for k,v in options.items()}))
  raise module.subprocess.TimeoutExpired(command,options['timeout'],output=partial_stdout,stderr=partial_stderr)
 module.subprocess.run=fail
 try:
  try:module.build(BASE,out)
  except module.subprocess.TimeoutExpired:pass
  else:raise AssertionError('Expected mocked timeout')
 finally:module.subprocess.run=original
 return json.loads((out/'BUILD.json').read_text())
old=os.environ.get('RF2_SDK_BUILD_BEFORE')
if old:
 before=Path(old).resolve();m=load('old_build_controller',before);report=exercise(m,D/'before')
 check('old timeout logging gap reproduced',report['status']=='failed'and report['steps']==[]and not(D/'before/bridge.stdout').exists(),dict(sourceSHA256=sha(before),report=report))
current=R/'experiments/sdk-packages/build.py';m=load('current_build_controller',current);report=exercise(m,D/'after');row=report['steps'][0]
check('timeout retains partial stdout bytes',(D/'after/bridge.stdout').read_bytes()==partial_stdout)
check('timeout retains partial stderr bytes',(D/'after/bridge.stderr').read_bytes()==partial_stderr)
check('timeout records command/elapsed/status',report['status']=='failed'and row['label']=='bridge'and row['exit']=='timeout'and row['timedOut']is True and row['timeoutSeconds']==60 and row['seconds']>=0 and row['command']==calls[-1]['command'],row)
check('timeout records partial stream identities',row['stdoutSHA256']==sha(D/'after/bridge.stdout')and row['stderrSHA256']==sha(D/'after/bridge.stderr'),row)
check('failure receipt binds current build source',report['buildToolSHA256']==sha(current),report['buildToolSHA256'])
check('mock executed only first child command',len(calls)==(2 if old else 1)and all('bootstrap.py'in' '.join(x['command'])for x in calls))
print(json.dumps(dict(directory=str(D),checks=len(checks),allPassed=True,kind='Mocked controller failure only')))
