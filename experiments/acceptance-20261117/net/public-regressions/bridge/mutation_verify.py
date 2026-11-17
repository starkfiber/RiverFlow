"""Check whether the actual oracle catches deliberately broken native bridge code."""
from pathlib import Path
import subprocess,json,hashlib
V=Path('experiments/rf2net/bridge');D=Path('artifacts/rf2net-bridge/qualification-4');C=Path('artifacts/rf2decision-sustained/compiler-opt').resolve()
base=(V/'bridge.flow').read_text();main=(V/'main.flow').read_text();data=(D/'INPUT.bin').read_bytes();want=(D/'EXPECTED.bin').read_bytes();rows=[]
for name,old,new in [('late-expiry','now-seen[i]>=30','now-seen[i]>30'),('reserved-forwarded','return 2048','return 770'),('wrong-port','let egress=2','let egress=1'),('same-port-leak','return 1024','return 258')]:
 assert base.count(old)==1
 folder=D/'mutations'/name;folder.mkdir(parents=True,exist_ok=False);(folder/'bridge.flow').write_text(base.replace(old,new,1));(folder/'main.flow').write_text(main)
 exe=folder/'program';p=subprocess.run([str(C),str(folder/'main.flow'),str(exe),'--compact','--opt'],capture_output=True,text=True,timeout=40);assert p.returncode==0,p.stdout+p.stderr
 subprocess.run(['codesign','-s','-',str(exe)],capture_output=True,check=True)
 p=subprocess.run([str(exe.resolve())],input=data,capture_output=True,timeout=30);(folder/'ACTUAL.bin').write_bytes(p.stdout)
 assert p.returncode==0 and p.stdout!=want,(name,'oracle failed to detect a wrong transformation')
 first=next(i for i,(a,b) in enumerate(zip(p.stdout,want)) if a!=b)
 rows.append({'name':name,'caught':True,'firstDifferentOutputByte':first,'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256((folder/'bridge.flow').read_bytes()).hexdigest()})
 print(name,'detected',flush=True)
(D/'MUTATION-VERIFICATION.json').write_text(json.dumps({'passed':True,'count':len(rows),'scope':'Four intentional source mutants rejected by exact-output comparison; not exhaustive mutation testing','results':rows},indent=2)+'\n')
