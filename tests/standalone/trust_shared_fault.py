"""Negative controls: a third algorithm catches two-path fault, not universal faults."""
from pathlib import Path
import shutil,subprocess,json,time,hashlib,os
R=Path(__file__).resolve().parents[2];D=R/'artifacts/trust-0.18'/('shared-fault-'+str(time.time_ns()));D.mkdir(parents=True)
key=D/'public-test-key';key.write_bytes(bytes(range(32)));key.chmod(0o600);plan=D/'xor.plan';plan.write_text('RF2E1 allow 7 budget 2 input 1 3 steps 1 xor 1\n');rows=[]
for allpaths in [False,True]:
 root=D/('all-three-wrong'if allpaths else'two-wrong-one-correct');(root/'examples').mkdir(parents=True);shutil.copytree(R/'examples/evidence-contract',root/'examples/evidence-contract');(root/'tools').mkdir();shutil.copyfile(R/'tools/build-trust.py',root/'tools/build-trust.py');(root/'output/native-compiler').mkdir(parents=True);shutil.copyfile(R/'output/native-compiler/rf2c',root/'output/native-compiler/rf2c');(root/'output/native-compiler/rf2c').chmod(0o755)
 p=root/'examples/evidence-contract/lib/engine.rf2';s=p.read_text().replace('set value=value^operand','set value=value|operand').replace('set value=value^args[j]','set value=value|args[j]').replace('set fast_mask=fast_mask^operand','set fast_mask=fast_mask|operand').replace('set value=value^fast_mask','set value=value|fast_mask');p.write_text(s)
 if allpaths:
  p=root/'examples/evidence-contract/lib/verifier.rf2';s=p.read_text();assert 'set value=value^arg'in s;p.write_text(s.replace('set value=value^arg','set value=value|arg'))
 out=root/'build';b=subprocess.run(['python3',root/'tools/build-trust.py',out],capture_output=True,timeout=60);assert b.returncode==0,b.stderr
 issued=subprocess.run([out/'rf2-trust','issue',key,plan],capture_output=True,timeout=10);cap=root/'capsule';cap.write_bytes(issued.stdout)
 if allpaths:
  assert issued.returncode==0 and issued.stdout.startswith(b'RF2A1');verified=subprocess.run([out/'rf2-verify',key,cap],capture_output=True,timeout=10);assert verified.returncode==0
  result={'variant':'all three implementations wrong','issueAccepted':True,'offlineVerifierAccepted':True,'independentPythonExpectedByte':3^1,'injectedORByte':3|1,'limitationObserved':True}
 else:
  assert issued.returncode!=0 and not issued.stdout.startswith(b'RF2A1');result={'variant':'both engine paths wrong, separate verifier correct','issueAccepted':False,'thirdAlgorithmDetectedInjectedFault':True}
 result['build']=json.loads((out/'BUILD.json').read_text());rows.append(result)
report={'date':'2026-11-13','experimentCompleted':True,'controls':rows,'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Private compiled source mutants and public test key only. Third verifier detects this two-path shared fault; a deliberately common three-path defect still escapes. Algorithms share compiler/crypto. No universal fault immunity or independent toolchain claim.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'experimentCompleted':True,'controls':len(rows),'report':str(D/'report.json')},indent=2))
