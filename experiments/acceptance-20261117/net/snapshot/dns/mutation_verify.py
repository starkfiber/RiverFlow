"""Detect known wrong DNS variants against frozen exact-response oracle."""
from pathlib import Path
import subprocess,json,hashlib
V=Path('experiments/rf2net/dns');D=Path('artifacts/rf2net-dns-final');M=D/'mutations';M.mkdir(exist_ok=False);C=Path('artifacts/rf2decision-sustained/compiler-opt').resolve();source=(V/'dns.flow').read_text();rows=[]
for name,before,after in [('outside-zone-not-refused','zone==0','zone==9'),('reply-loop-admitted','(p[2]&128)!=0','(p[2]&128)==999'),('badvers-hidden','set bad=1','set bad=0')]:
 assert source.count(before)==1
 d=M/name;d.mkdir();(d/'dns.flow').write_text(source.replace(before,after,1));(d/'main.flow').write_bytes((V/'main.flow').read_bytes());exe=d/'wrong-native';x=subprocess.run([str(C),str(d/'main.flow'),str(exe),'--compact','--opt'],capture_output=True,text=True,timeout=40);assert x.returncode==0,x.stdout+x.stderr;subprocess.run(['codesign','-s','-',str(exe)],capture_output=True,check=True)
 x=subprocess.run([str(exe.resolve())],input=(D/'INPUT.bin').read_bytes(),capture_output=True,timeout=10);assert x.returncode==0 and x.stdout!=(D/'EXPECTED.bin').read_bytes(),name
 rows.append({'name':name,'detected':True,'exit':x.returncode,'outputSHA256':hashlib.sha256(x.stdout).hexdigest()})
(D/'MUTATION-RESULTS.json').write_text(json.dumps({'passed':True,'count':len(rows),'cases':rows,'scope':'Known wrong local native variants, not a security proof'},indent=2)+'\n');print(len(rows),'wrong DNS variants detected')
