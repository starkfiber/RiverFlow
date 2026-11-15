"""Run first learning edition examples using explicit native tools."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2];HOME=Path(os.environ['RF2_TEST_HOME']).resolve();BOOK=ROOT/'book/learning-edition-1';OUT=Path(tempfile.mkdtemp(prefix='learning-edition-',dir=ROOT/'artifacts'));rows=[]
def check(label,yes):
 rows.append(dict(name=label,passed=bool(yes)));assert yes,label
def call(args):return subprocess.run(list(map(str,args)),capture_output=True,timeout=20)
for name,data,value in [('sum',[1,2,3],6),('sum',[2,4,6],12),('squares',[1,2,3],14),('bits',[0,1,3,255],11),('bits',[7,8],4),('nonzero',[0,8,0,2],2),('wrap',[4294967295,1],0)]:
 source=BOOK/'examples'/f'{name}.flow';p=call([HOME/'rf2','check',source]);check(name+' check',p.returncode==0)
 p=call([HOME/'rf2','run',source,json.dumps(data)]);check(name+' runtime '+str(data),p.returncode==0 and json.loads(p.stdout)['value']==value)
 if not (OUT/name).exists():
  p=call(['sh',ROOT/'tools/build-core.sh',HOME/'rf2',HOME/'rf2c',source,OUT/name]);check(name+' build',p.returncode==0)
 p=call([OUT/name/'program',json.dumps(data)]);check(name+' native '+str(data),p.returncode==0 and json.loads(p.stdout)['value']==value)
for data in ('[4294967295,1]','["three"]','[-1]'):
 p=call([HOME/'rf2','run',BOOK/'examples/sum.flow',data]);check('refuse '+data,p.returncode!=0)
for name in ('functions','loop','results'):
 for opt in (False,True):
  dest=OUT/(name+str(opt));p=call(['sh',ROOT/'tools/build-program.sh',HOME/'rf2c',BOOK/'examples'/f'{name}.flow',dest,*(['--opt'] if opt else [])]);check(name+' build '+str(opt),p.returncode==0)
  p=call([dest/'program']);check(name+' run '+str(opt),p.returncode==0)
report={'baseline':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'compilerSha256':hashlib.sha256((HOME/'rf2c').read_bytes()).hexdigest(),'runtimeSha256':hashlib.sha256((HOME/'rf2').read_bytes()).hexdigest(),'checks':rows,'sourceHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BOOK/'examples').glob('*.flow'))},'limits':'Local finite examples; fragment-only snippets are labelled; no learner usability study, speed/token benchmark or independent academic approval.'}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');(BOOK/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(rows),'report':str(OUT/'report.json')}))
