"""Documented post-run review: preserve frozen grades; apply the same narrow grader correction to every original."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;D=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert len(json.loads((D/'RESULTS.json').read_text())['trialResults'])==4,'Do not revise grading during frozen attempts'
source=(S/'grade.py').read_text();old="'conflict'in body.lower()or'already'in body.lower()";new=old+"or'revision changed'in body.lower()";assert source.count(old)==1
source=source.replace(old,new);old="'error'in rs[4]and'error'in rs[5]";new="('error'in rs[4]or rs[4].get('result',{}).get('isError')is True)and'error'in rs[5]";assert source.count(old)==1;source=source.replace(old,new)
grade=D/'grade-reviewed.py';grade.write_text(source)
reports=[]
for name in ['1-rf2','2-python','3-python','4-rf2']:
 W=D/name;out=W/'GRADE-REVIEWED.json';q=subprocess.run([sys.executable,str(grade),str(W),str(out)],cwd=R,capture_output=True,timeout=120);assert q.returncode==0,q.stderr.decode();d=json.loads(out.read_text());reports.append(dict(attempt=name,checks=d['checks'],passed=d['passed'],allPassed=d['allPassed'],failures=[r for r in d['results']if not r['passed']],reportSHA256=sha(out)))
receipt=dict(originalGraderSHA256=sha(S/'grade.py'),reviewedGraderSHA256=sha(grade),appliedAfterAllAttempts=True,corrections=['Accept the semantically valid revision changed stale-form message','Input argument validation may use an isError tool result; an unknown tool still requires a JSON-RPC protocol error'],reference='https://modelcontextprotocol.io/specification/2025-11-25/server/tools#error-handling',originalGradesPreserved=True,reports=reports)
(D/'REVIEWED-GRADES.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
