"""Developer builder. Native RF2 server/controller have no interpreter dependency."""
from pathlib import Path
import json,hashlib,subprocess,sys,os
R=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c'))
src=R/'examples/stack-lab/server.rf2';text=src.read_text();line=next(x for x in text.splitlines()if x.strip().startswith('let site='));assert json.loads(line.split('=',1)[1])==(R/'examples/stack-lab/index.html').read_text(),'Reconcile embedded page with index.html before building.'
rows=[]
for source,name in [('server.rf2','rf2-site'),('vm.rf2','rf2-vm')]:
 subprocess.run([C,R/'examples/stack-lab'/source,out/name,'--opt'],check=True);subprocess.run(['/usr/bin/codesign','-s','-',out/name],check=True);rows.append({'name':name,'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()})
(out/'BUILD.json').write_text(json.dumps({'target':'macos-arm64','compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'binaries':rows,'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (R/'examples/stack-lab').glob('*')if p.is_file()},'backend':'VM controller executes installed QEMU/HVF, not an RF2 hypervisor'},indent=2)+'\n')
