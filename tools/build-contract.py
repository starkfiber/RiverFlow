#!/usr/bin/env python3
"""Development builder for the RF2-only research contract executable."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1]; D=R/'examples/evidence-contract'
C=R/'output/native-compiler/rf2c'
files=sorted(p for p in D.rglob('*.rf2') if p.name!='build_identity.rf2')
h=hashlib.sha256(b'RF2-CONTRACT-SOURCE-1\0'); manifest=[]
for p in files:
 name=p.relative_to(D).as_posix().encode(); raw=p.read_bytes()
 h.update(len(name).to_bytes(8,'little')+name+len(raw).to_bytes(8,'little')+raw)
 manifest.append({'path':name.decode(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
identity=h.hexdigest()
(D/'lib/build_identity.rf2').write_text('module identity\n# Generated source-bundle identity, not a signature or self-attestation.\nfn build_identity()\n return "'+identity+'"\nend\n')
out=Path(sys.argv[1] if len(sys.argv)>1 else R/'output/bin/rf2-contract').resolve()
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():raise SystemExit('Refusing existing output: '+str(out))
subprocess.run([str(C),str(D/'main.rf2'),str(out)]+sys.argv[2:],check=True,cwd=R)
subprocess.run(['/usr/bin/codesign','-s','-',str(out)],check=True)
receipt={'source_identity':identity,'source_files':manifest,'compiler_sha256':hashlib.sha256(C.read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'binary':str(out),'options':sys.argv[2:]}
out.with_suffix('.build.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
