#!/usr/bin/env python3
"""Verify drop-in source candidate against alias states and unchanged Passage Desk."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess
from stage_sdk import ROOT,HERE,stage
COMPILER_HASH='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('compiler',type=Path);p.add_argument('destination',type=Path);a=p.parse_args()
 if sha(a.compiler)!=COMPILER_HASH:raise ValueError('Compiler identity mismatch')
 a.destination.mkdir(parents=True,exist_ok=False);d=a.destination.resolve();sdk=stage(d/'sdk')
 receipt=dict(schema='rf2.sdk-json-spans-integration.v1',compilerSHA256=sha(a.compiler),candidateTextSHA256=sha(sdk/'text.flow'),commands=[],checks=[])
 def save():(d/'INTEGRATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
 def run(command):
  q=subprocess.run(list(map(str,command)),capture_output=True,timeout=60)
  receipt['commands'].append(dict(command=list(map(str,command)),exit=q.returncode,stdout=q.stdout.decode(errors='replace'),stderr=q.stderr.decode(errors='replace')));save()
  if q.returncode:raise RuntimeError(receipt['commands'][-1])
  return q
 spec=importlib.util.spec_from_file_location('grade_passage',ROOT/'experiments/sdk-task/grade.py');grade=importlib.util.module_from_spec(spec);spec.loader.exec_module(grade)
 for optimization in ['plain','opt']:
  flags=['--opt'] if optimization=='opt' else []
  alias=d/('alias-'+optimization);alias.mkdir()
  source=(HERE/'alias.flow.in').read_text().replace('use "json_spans.flow"\n','').replace('do writer_json(a,','do writer_json_scalar(a,').replace('do writer_json_spans(b,','do writer_json(b,')
  (alias/'main.flow').write_text(source)
  run([a.compiler.resolve(),alias/'main.flow',alias/'program','--sdk-root',sdk,*flags]);run(['/usr/bin/codesign','-s','-',alias/'program']);q=run([alias/'program'])
  receipt['checks'].append(dict(name=optimization+' exact alias states',passed=q.stdout==b'73728',states=73728));save()
  passage=d/('passage-'+optimization);passage.mkdir();(passage/'main.flow').write_bytes((ROOT/'examples/passage-desk/main.flow').read_bytes());(passage/'README.md').write_bytes((ROOT/'examples/passage-desk/README.md').read_bytes());(passage/'launch.json').write_text('["./app"]\n')
  run([a.compiler.resolve(),passage/'main.flow',passage/'app','--sdk-root',sdk,*flags]);run(['/usr/bin/codesign','-s','-',passage/'app'])
  result=grade.grade(passage,passage/'GRADE.json');receipt['checks'].append(dict(name=optimization+' unchanged Passage Desk',passed=result['allPassed'],checks=result['checks']));save()
 receipt['allPassed']=all(x['passed'] for x in receipt['checks']);receipt['complete']=True;save();print(d/'INTEGRATION.json')
if __name__=='__main__':main()
