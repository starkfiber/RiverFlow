from pathlib import Path
import subprocess,json,hashlib,tempfile,os
R=Path(__file__).resolve().parents[2];C=R/'output/native-compiler/rf2c';report={'passed':False,'cases':[],'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest()}
with tempfile.TemporaryDirectory(prefix='rf2-compiler-bounds-')as name:
 root=Path(name)
 for n in [128,129,255,256,257]:
  s='profile RF2_SYSTEM_A64_V1\n'+''.join('fn f'+str(i)+'()\n return '+str(i%200)+'\nend\n'for i in range(n-1))+'fn main(argc, argv)\n'+''.join(' let v'+str(i)+' = '+str(i%200)+'\n'for i in range(254))+' return f'+str(n-2)+'() + v253\nend\n';p=root/f'bound{n}.rf2';p.write_text(s);out=root/f'bound{n}';r=subprocess.run([C,p,out],capture_output=True,env={'PATH':'/nonexistent'});ok=n<=256;assert (r.returncode==0)==ok,(n,r.stderr)
  if ok:
   subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);assert subprocess.run([out]).returncode==((n-2)%200+53)%256
  else:assert not out.exists()and b'function bound'in r.stderr
  report['cases'].append({'functions':n,'lastFunctionLocals':256,'accepted':ok})
report['passed']=True;Path(os.environ.get('RF2_TEST_REPORT',str(R/'docs/COMPILER-BOUNDS-0.8.json'))).write_text(json.dumps(report,indent=2)+'\n');print(report)
