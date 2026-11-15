"""Prevent narrow sprint badges, changed scope and unsupported delivery completion."""
import copy,importlib.util,json,subprocess,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('progress',R/'tools/project-progress.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
data=json.loads((R/'docs/PIPELINE.json').read_text());rows=[]
def check(name,passed):
 rows.append(dict(name=name,passed=bool(passed)))
 if not passed:raise AssertionError(name)
actual=m.render(data);done=sum(r['state']=='done'for r in data['deliveryScope']['requirements'])
check('fixed delivery count',f'{done}/12 requested requirements complete' in actual)
check('one percentage only',actual.count('%')==1)
check('historical sprint labels excluded','Owned text and collection fields, isolated candidate'not in actual)
for name,mutate in [
 ('schema',lambda d:d.update(schema='rf2.pipeline.v1')),
 ('denominator',lambda d:d['deliveryScope'].update(lockedRequirementCount=6)),
 ('missing requirement',lambda d:d['deliveryScope']['requirements'].pop()),
 ('order',lambda d:d['deliveryScope']['requirements'].reverse()),
 ('unknown state',lambda d:d['deliveryScope']['requirements'][0].update(state='complete')),
 ('unsupported done',lambda d:d['deliveryScope']['requirements'][2].update(state='done',evidence=[])),
 ('missing evidence',lambda d:d['deliveryScope']['requirements'][0].update(evidence=['docs/DOES-NOT-EXIST'])),
 ('outside evidence',lambda d:d['deliveryScope']['requirements'][0].update(evidence=['/etc/hosts'])),
]:
 fixture=copy.deepcopy(data);mutate(fixture)
 try:m.render(fixture)
 except ValueError:check('refuses '+name,True)
 else:check('refuses '+name,False)
q=subprocess.run(['python3',str(R/'tools/project-progress.py'),'--check'],capture_output=True);check('current rendering',q.returncode==0)
with tempfile.TemporaryDirectory(prefix='rf2-progress-')as out:
 root=Path(out).resolve();(root/'docs').mkdir();(root/'docs/PIPELINE.json').write_text(json.dumps(data));(root/'docs/PROGRESS.md').write_text('obsolete sprint 100%\n');old=m.ROOT;m.ROOT=root
 # Review rendering against an explicit fixture root with only the declared evidence files.
 for row in data['deliveryScope']['requirements']:
  for file in row.get('evidence',[]):
   p=root/file;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((R/file).read_bytes())
 check('stale bytes detected',m.render(data).encode()!=(root/'docs/PROGRESS.md').read_bytes());m.ROOT=old
print(json.dumps(dict(checks=len(rows),results=rows)))
