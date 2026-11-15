"""Verify declarative VSIX contents against reviewed editor sources; never install it."""
from pathlib import Path
import hashlib,json,sys,zipfile
R=Path(__file__).resolve().parents[1];P=R/'editors/vscode';archive=Path(sys.argv[1]).resolve();report=Path(sys.argv[2]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();checks=[]
with zipfile.ZipFile(archive)as z:
 names=z.namelist();assert len(names)==8 and len(set(names))==8;assert not any(n.endswith(('.js','.wasm','.node','.exe'))for n in names)
 for a,b in [('package.json','package.json'),('README.md','readme.md'),('LICENSE','LICENSE.txt'),('language-configuration.json','language-configuration.json'),('snippets/riverflow.json','snippets/riverflow.json'),('syntaxes/riverflow.tmLanguage.json','syntaxes/riverflow.tmLanguage.json')]:
  assert (P/a).read_bytes()==z.read('extension/'+b);checks.append(dict(path=a,sha256=sha(P/a),archiveBytesMatch=True))
 d=dict(archiveSHA256=sha(archive),bytes=archive.stat().st_size,entries=names,sourceChecks=checks,codeEntry=False,installed=False)
 report.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(report=str(report),sourceChecks=len(checks),noExecutableEntry=True)))
