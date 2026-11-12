"""Build native platform/VMM candidate from pinned0.18; no C/C++ compiler or QEMU."""
from pathlib import Path
import subprocess,hashlib,json,sys,os
R=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False);seed=Path(os.environ.get('RF2_BOOTSTRAP_COMPILER',R/'output/native-compiler/rf2c-dyld-final'))
for c,s,n in [(seed,R/'native/compiler/compiler.rf2','rf2c'),(out/'rf2c',R/'native/compiler/compiler.rf2','rf2c-self'),(out/'rf2c-self',R/'examples/hypervisor/main.rf2','rf2-hypervisor')]:
 subprocess.run([c,s,out/n,'--opt'],check=True,capture_output=True);args=['/usr/bin/codesign','-s','-'];args+=['--entitlements',str(R/'examples/hypervisor/entitlements.plist')]if n=='rf2-hypervisor'else[];subprocess.run([*args,out/n],check=True,capture_output=True)
files=[R/'native/compiler/compiler.rf2',R/'examples/hypervisor/main.rf2',R/'examples/hypervisor/entitlements.plist'];(out/'BUILD.json').write_text(json.dumps({'edition':'0.19-dev','compilerSeedSHA256':hashlib.sha256(seed.read_bytes()).hexdigest(),'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},'binaries':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in out.iterdir()if p.is_file()},'scope':'CLI-only fixed Hypervisor framework scalar ABI imports. Native VMM foundation, not a Linux VM.'},indent=2)+'\n');print(out)
