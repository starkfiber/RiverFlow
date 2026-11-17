"""Require known wrong native implementations to fail unchanged payload/state oracles."""
from pathlib import Path
import subprocess,json,hashlib,shutil
V=Path('experiments/rf2net/dhcp');D=Path('artifacts/rf2net-dhcp-final');M=D/'mutations';M.mkdir(exist_ok=False);C=Path('artifacts/rf2decision-sustained/compiler-opt').resolve();source=(V/'dhcp.flow').read_text()
changes=[('expired-stays-live','until[i]<=now','until[i]<now'),('duplicate-type-admitted','(seen&1)!=0','seen==999'),('wrong-owner-IP-accepted','if wanted!=172818532+own','if wanted==172818532+own')]
rows=[]
for name,before,after in changes:
 assert source.count(before)==1
 d=M/name;d.mkdir();(d/'dhcp.flow').write_text(source.replace(before,after,1));(d/'main.flow').write_bytes((V/'main.flow').read_bytes());exe=d/'wrong-native'
 x=subprocess.run([str(C),str(d/'main.flow'),str(exe),'--compact','--opt'],capture_output=True,text=True,timeout=40);assert x.returncode==0,x.stdout+x.stderr;subprocess.run(['codesign','-s','-',str(exe)],capture_output=True,check=True)
 blob=(D/'explicit-input.bin').read_bytes();want=(D/'explicit-expected.bin').read_bytes();x=subprocess.run([str(exe.resolve())],input=blob,capture_output=True,timeout=10)
 assert x.returncode==0 and x.stdout!=want,(name,'wrong implementation escaped oracle or failed to execute')
 rows.append({'name':name,'detected':True,'wrongNativeExit':x.returncode,'outputSHA256':hashlib.sha256(x.stdout).hexdigest()})
(D/'MUTATION-RESULTS.json').write_text(json.dumps({'passed':True,'count':len(rows),'cases':rows,'scope':'Known wrong local native mutations only; not a security proof'},indent=2)+'\n');print(len(rows),'deliberately wrong native implementations detected')
