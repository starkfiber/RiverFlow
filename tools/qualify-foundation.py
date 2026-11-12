"""Free hosted source qualification; nested hardware virtualization is explicitly untested."""
from pathlib import Path
import subprocess,os,json,shutil,time,hashlib
R=Path(__file__).resolve().parents[1];D=R/'artifacts/second-host';out=R/'output/foundation-hosted';wasm=R/'output/wasm-hosted';env=dict(os.environ,RF2_BOOTSTRAP_COMPILER=str(R/'output/native-compiler/rf2c'),RF2_TEST_COMPILER=str(out/'rf2c-self'),RF2_WASM_COMPILER=str(wasm/'rf2-wasm'),RF2_CORE_BASELINE=str(R/'output/bootstrap/rf2-0.17.0/rf2'),RF2_NODE=shutil.which('node')or'node');report={'passed':False,'hardwareVirtualization':'NOT_RUN: hosted runner is itself a VM; no nested-HV claim','commands':[]}
for cmd in [['python3','tools/build-foundation.py',str(out)],['python3','tools/build-wasm.py',str(wasm)],['python3','tests/standalone/wasm_verify.py'],[env['RF2_NODE'],'tests/standalone/browser_worker_verify.mjs']]:
 p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,timeout=120);report['commands'].append({'command':cmd,'exit':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')});(D/'foundation-qualification.json').write_text(json.dumps(report,indent=2)+'\n');assert p.returncode==0,report['commands'][-1]
report['passed']=True;(D/'foundation-qualification.json').write_text(json.dumps(report,indent=2)+'\n')
for root in [R/'artifacts/foundation-0.19']:
 for p in root.rglob('report.json'):
  dest=D/'foundation-reports'/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
print('Foundation compiler/WASM/Worker isolation checks passed; hardware virtualization not run on hosted VM.')
