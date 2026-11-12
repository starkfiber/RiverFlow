#!/usr/bin/env python3
"""Developer builder. Resulting trust/verifier programs execute only native RF2."""
from pathlib import Path
import sys,subprocess,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'examples/evidence-contract';out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False);compiler=R/'output/native-compiler/rf2c'
h=hashlib.sha256(b'RF2-CONTRACT-SOURCE-1\0');sources=[]
for p in sorted(D.rglob('*.rf2')):
 if p.name=='build_identity.rf2':continue
 name=p.relative_to(D).as_posix().encode();raw=p.read_bytes();h.update(len(name).to_bytes(8,'little')+name+len(raw).to_bytes(8,'little')+raw);sources.append({'path':name.decode(),'sha256':hashlib.sha256(raw).hexdigest()})
identity=h.hexdigest();(D/'lib/build_identity.rf2').write_text('module identity\n# Generated source identity, not authenticated execution.\nfn build_identity()\n return "'+identity+'"\nend\n')
rows=[]
for entry,name in [('trust.rf2','rf2-trust'),('verify.rf2','rf2-verify')]:
 p=subprocess.run([compiler,D/entry,out/name,'--opt'],capture_output=True);(out/(name+'.build.log')).write_bytes(p.stdout+p.stderr)
 if p.returncode:raise SystemExit(f'compiler exit={p.returncode} stdout={p.stdout.decode(errors="replace")} stderr={p.stderr.decode(errors="replace")}')
 subprocess.run(['/usr/bin/codesign','-s','-',out/name],check=True);rows.append({'file':name,'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()})
report={'edition':'0.18-dev','sourceIdentity':identity,'compilerSHA256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'sources':sources,'binaries':rows};(out/'BUILD.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
