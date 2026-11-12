"""Qualify the exact checked-in development archive on the executing ARM Mac."""
from pathlib import Path,PurePosixPath
import tarfile,json,hashlib,subprocess,tempfile,os,platform,time,struct,select,urllib.request
R=Path(__file__).resolve().parents[1];D=R/'artifacts/second-host';D.mkdir(exist_ok=True,parents=True);directory=R/'dist/0.18-candidate';archive=directory/'rf2-trust-0.18.0-candidate-macos-arm64.tar.gz';expected=(directory/'SHA256SUMS.txt').read_text().split()[0];assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
report={'archiveSHA256':expected,'system':platform.platform(),'architecture':platform.machine(),'commands':[],'passed':False};assert platform.system()=='Darwin'and platform.machine()=='arm64'
with tempfile.TemporaryDirectory(prefix='rf2-package-')as tmp:
 target=Path(tmp)
 with tarfile.open(archive)as f:
  members=f.getmembers();assert sum(x.size for x in members)<40000000
  for x in members:assert not x.name.startswith('/')and'..'not in PurePosixPath(x.name).parts and(x.isfile()or x.isdir())
  for x in members:
   dest=target/x.name
   if x.isdir():dest.mkdir(parents=True,exist_ok=True)
   else:
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.extractfile(x).read());dest.chmod(x.mode&0o777)
 root=target/'rf2-trust-0.18.0-candidate-macos-arm64';m=json.loads((root/'MANIFEST.json').read_text())
 for p,h in m['files'].items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
 report['manifestVerified']=True;report['binarySHA256']={p:m['files'][p]for p in ['rf2c','rf2-trust','rf2-verify','rf2-site','rf2-vm']}
 source=target/'hello.rf2';source.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return 42\nend\n');exe=target/'hello';p=subprocess.run([root/'rf2c',source,exe,'--opt'],capture_output=True,timeout=15);assert p.returncode==0,(p.returncode,p.stderr)
 subprocess.run(['/usr/bin/codesign','-s','-',exe],check=True,capture_output=True);assert subprocess.run([exe],env={'PATH':'/nonexistent'}).returncode==42;report['packagedCompilerEmitsRunningProgram']=True
 b=exe.read_bytes();off=32;cmds=[]
 for _ in range(struct.unpack_from('<I',b,16)[0]):cmd,n=struct.unpack_from('<II',b,off);cmds.append(cmd);off+=n
 assert 0x80000022 in cmds;report['emittedDyldMetadata']=True
 env=dict(os.environ,RF2_TRUST_DIR=str(root))
 for script in ['trust_verify.py','trust_protocol_keys.py']:
  start=time.monotonic();p=subprocess.run(['python3',str(R/'tests/standalone'/script)],env=env,cwd=R,capture_output=True,timeout=60);report['commands'].append({'script':script,'exit':p.returncode,'seconds':time.monotonic()-start,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()});assert p.returncode==0,report['commands'][-1]
 # Validate exact native website on this host; no Node or Python child runtime.
 site=subprocess.Popen([root/'rf2-site'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/nonexistent'})
 try:
  assert select.select([site.stdout],[],[],5)[0],'native startup timeout'
  assert site.stdout.readline()==b'RF2 loopback server: http://127.0.0.1:18780/\n'
  for path,expected in [('/health',b'{"ok":true}\n'),('/api/compute?iterations=10000',b'{"iterations":10000,"checksum":21361410878536,"state":4089345937}\n'),('/',(root/'examples/stack-lab/index.html').read_bytes())]:
   with urllib.request.urlopen('http://127.0.0.1:18780'+path,timeout=3)as response:assert response.status==200 and response.read()==expected
  report['nativeWebsitePassed']=True
 finally:
  site.terminate();site.wait(timeout=3)
 usage=subprocess.run([root/'rf2-vm'],capture_output=True,timeout=3,env={'PATH':'/nonexistent'});assert usage.returncode==1 and usage.stderr==b'Usage: rf2-vm qemu firmware guest-overlay seed-iso\n';report['controllerUsagePassed']=True;report['VMHardwareTestedHere']=False
 report['passed']=True
(D/'exact-package.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
