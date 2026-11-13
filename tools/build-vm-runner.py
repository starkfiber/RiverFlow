"""Build the CLI-only native RF2 bounded image runner, without QEMU or a C compiler."""
from pathlib import Path
import subprocess,hashlib,json,sys,os
R=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
seed=Path(os.environ.get('RF2_BOOTSTRAP_COMPILER',R/'output/foundation-0.19-regression/rf2c-self')).resolve()
for compiler,source,name in [(seed,R/'native/compiler/compiler.rf2','rf2c'),(out/'rf2c',R/'native/compiler/compiler.rf2','rf2c-self'),(out/'rf2c-self',R/'examples/vm-runner/main.rf2','rf2-vm-runner')]:
 subprocess.run([compiler,source,out/name,'--opt'],check=True,capture_output=True)
 args=['/usr/bin/codesign','-s','-']
 if name=='rf2-vm-runner':args+=['--entitlements',str(R/'examples/hypervisor/entitlements.plist')]
 subprocess.run([*args,out/name],check=True,capture_output=True)
paths=['native/compiler/compiler.rf2','examples/vm-runner/main.rf2','examples/hypervisor/entitlements.plist']
report={'edition':'0.20-dev','seedSHA256':hashlib.sha256(seed.read_bytes()).hexdigest(),'sources':{s:hashlib.sha256((R/s).read_bytes()).hexdigest()for s in paths},'binaries':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in out.iterdir()if p.is_file()},'scope':'Trusted native CLI; bounded ARM64 images; no Linux boot or new MCP effects'}
(out/'BUILD.json').write_text(json.dumps(report,indent=2)+'\n');print(out)
