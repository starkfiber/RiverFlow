"""Build a source-bound native bridge that expands only inventoried function tables."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
R=Path(__file__).resolve().parents[2]
if len(sys.argv)!=3:raise SystemExit('Usage: bootstrap.py BASELINE-NATIVE-COMPILER NEW-DIRECTORY')
binary=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
if out.exists():raise SystemExit('Use a new directory')
spec=importlib.util.spec_from_file_location('rf2_diagnostic_prepare',Path(__file__).with_name('prepare.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
out.mkdir(parents=True)
base=out/'baseline'
subprocess.run([sys.executable,str(R/'experiments/typed-requests/prepare.py'),str(base)],check=True,capture_output=True)
source=out/'compiler.flow';source.write_text(module.apply_bounds((base/'compiler.flow').read_text()))
exe=out/'program';command=[str(binary),str(source),str(exe),'--compact','--opt']
q=subprocess.run(command,capture_output=True);(out/'BUILD.stdout').write_bytes(q.stdout);(out/'BUILD.stderr').write_bytes(q.stderr);q.check_returncode()
q=subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],capture_output=True);(out/'SIGN.stderr').write_bytes(q.stderr);q.check_returncode()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(schema='rf2.function-table-bootstrap.v1',baselineCompilerSHA256=sha(binary),baselineSourceSHA256=sha(base/'compiler.flow'),sourceSHA256=sha(source),programSHA256=sha(exe),functionLimit=512,localLimit=256,recordTypeLimit=32,expandedBuffers={k:v*2 for k,v in module.FUNCTION_BUFFERS.items()},command=command)
(out/'BOOTSTRAP.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(directory=str(out),programSHA256=sha(exe))))
