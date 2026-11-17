from pathlib import Path
import subprocess,json,hashlib,struct
H=Path(__file__).resolve().parent;O=H.parents[2]/'artifacts/evolution-20261117/net/tail-scan/mutation';O.mkdir(exist_ok=True)
s=(H/'candidate.flow').read_text();assert s.count('if p[i]!=0')==1;(O/'dhcp.flow').write_text(s.replace('if p[i]!=0','if p[i]==999'))
(O/'main.flow').write_bytes((H/'original-main.flow').read_bytes());src=(H/'original-verify.py').read_text();ns=dict(struct=struct,hashlib=hashlib);exec('SERVER=0x0a4d0002;BASE=0x0a4d0064\ncases=[]\n'+src[src.index('def packet('):src.index('for c in range(1,6):')],ns)
b=ns['packet']()[:-1]+b'\1';code,reply,snap=ns['Oracle']().run(1,b);expected=struct.pack('<HH',code,len(reply))+reply+snap
results=[]
for mode in ['plain','opt']:
 exe=O/('wrong-'+mode);subprocess.run(['/Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program',str(O/'main.flow'),str(exe),'--compact']+(['--opt']if mode=='opt' else []),check=True,capture_output=True);subprocess.run(['codesign','-s','-',str(exe)],check=True,capture_output=True)
 p=subprocess.run([str(exe)],input=struct.pack('<HI',len(b),1)+b,capture_output=True,timeout=5);assert p.returncode==0 and p.stdout!=expected;results.append(dict(mode=mode,expectedCode=code,wrongNativeCode=struct.unpack_from('<H',p.stdout)[0],detected=True))
(O/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
