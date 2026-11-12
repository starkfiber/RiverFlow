"""Second-host native qualification. Public sources, disposable local test keys only."""
from pathlib import Path
import sys,subprocess,os,json,hashlib,platform,time
R=Path(__file__).resolve().parents[1];D=R/'artifacts/second-host';D.mkdir(parents=True,exist_ok=True)
assert platform.system()=='Darwin'and platform.machine()=='arm64','This qualification requires another macOS ARM64 environment.'
report={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'system':platform.platform(),'architecture':platform.machine(),'runnerEnvironment':os.environ.get('RUNNER_ENVIRONMENT','local'),'runnerOS':os.environ.get('RUNNER_OS'),'compilerSHA256':hashlib.sha256((R/'output/native-compiler/rf2c').read_bytes()).hexdigest(),'commands':[]}
assert report['compilerSHA256']=='8cac670c59421bfb83b92e5d12efda7e7951bd01b7c177c116d7f7c430deeb5e'
repair=subprocess.run(['python3','tools/macho-empty-dyld.py',str(R/'output/native-compiler/rf2c')],capture_output=True,check=True);report['bootstrapRepair']=json.loads(repair.stdout)
compiler=R/'output/native-compiler/rf2c';seed=compiler.with_name('rf2c-bootstrap');compiler.rename(seed)
subprocess.run([seed,R/'native/compiler/compiler.rf2',compiler,'--opt'],check=True)
# The old seed also emits the old container. Repair first-generation container.
subprocess.run(['python3','tools/macho-empty-dyld.py',str(compiler)],check=True)
report['candidateCompilerSHA256']=hashlib.sha256(compiler.read_bytes()).hexdigest()
commands=[['python3','tools/sync-contract-json.py','--check'],['python3','tools/build-trust.py','output/trust-0.18'],['python3','tests/standalone/trust_hmac_verify.py'],['python3','tests/standalone/verifier_exhaustive.py'],['python3','tests/standalone/contract_engine_verify.py'],['python3','tests/standalone/contract_exhaustive_verify.py'],['python3','tests/standalone/trust_shared_fault.py'],['python3','tests/standalone/trust_verify.py'],['python3','tests/standalone/trust_protocol_keys.py'],['python3','tools/qualify-packaged-candidate.py'],['python3','tools/qualify-foundation.py']]
env=dict(os.environ,RF2_TRUST_DIR=str(R/'output/trust-0.18'))
try:
 for i,cmd in enumerate(commands):
  start=time.monotonic();p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,timeout=240);(D/f'{i}.stdout.txt').write_bytes(p.stdout);(D/f'{i}.stderr.txt').write_bytes(p.stderr);report['commands'].append({'command':cmd,'exit':p.returncode,'seconds':time.monotonic()-start});(D/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');
  if p.returncode:
   debug=subprocess.run(['/usr/bin/lldb','--batch','-o','run','-o','bt','-o','register read','--',str(R/'output/native-compiler/rf2c'),str(R/'examples/evidence-contract/trust.rf2'),str(R/'output/debug-trust'),'--opt'],capture_output=True,timeout=45)
   (D/'compiler-debug.txt').write_bytes(debug.stdout+debug.stderr)
   raise AssertionError((cmd,p.stderr[-2000:]))
  print('PASS',cmd[-1],flush=True)
 report['passed']=True
finally:
 (D/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');collected=D/'reports';collected.mkdir(exist_ok=True)
 for root in ['artifacts/trust-0.18','artifacts/contract-next','artifacts/top-ten-five-hypotheses']:
  for p in (R/root).rglob('report.json'):
   relative=p.relative_to(R);dest=collected/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 if(R/'output/trust-0.18/BUILD.json').exists():(D/'BUILD.json').write_bytes((R/'output/trust-0.18/BUILD.json').read_bytes())
 for p in (R/'output/trust-0.18').glob('*.build.log'):(D/p.name).write_bytes(p.read_bytes())
 # Only reports/stdout/stderr above are uploaded. Key files, executables and VM disks are excluded.
