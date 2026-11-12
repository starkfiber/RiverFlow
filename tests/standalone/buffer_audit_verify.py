"""Native growable-byte/record-result application tests; independent Python byte oracle."""
from pathlib import Path
import hashlib,json,os,random,subprocess,tempfile
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c')).resolve()
SOURCE_HASH=hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest()
report={'passed':False,'appComparisons':0,'fileAndUsageChecks':0,'cleanupChecks':0,'limitChecks':0,'outputFailureChecks':0}
def compile(src,out,opt):
 p=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True,timeout=30);assert p.returncode==0,p.stderr
 subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
def oracle(data):
 h=14695981039346656037
 for b in data:h=((h^b)*1099511628211)&((1<<64)-1)
 return {'bytes':len(data),'lines':data.count(b'\n')+int(bool(data)and not data.endswith(b'\n')),'zeros':data.count(b'\0'),'fingerprint':h}
rng=random.Random(170017)
cases=[b'',b'\0',b'\n',b'\n\n',b'a\n',b'a\nb',b'\r\n',bytes(range(256)),'தமிழ்\nA🌍\0'.encode()]
cases += [bytes(rng.randrange(256)for _ in range(n))for n in [1,2,15,16,17,31,32,33,254,255,256,257,509,510,511,1023,1024,1025,4095,4096,4097,16383,16384,16385,65537]]
cases += [bytes(rng.randrange(256)for _ in range(rng.randrange(2000)))for _ in range(60)]
with tempfile.TemporaryDirectory(prefix='rf2-buffer-audit-')as td:
 d=Path(td)
 for opt in [False,True]:
  exe=d/f'app-{opt}';compile(R/'examples/buffer-audit/main.rf2',exe,opt)
  for i,data in enumerate(cases):
   file=d/f'input {i} தமிழ்.bin';file.write_bytes(data);p=subprocess.run([exe,file],capture_output=True,timeout=30);assert p.returncode==0 and json.loads(p.stdout)==oracle(data) and not p.stderr,(opt,i,p.returncode,p.stdout,p.stderr);assert file.read_bytes()==data;report['appComparisons']+=1
  for args in [[],['a','b']]:
   p=subprocess.run([exe]+args,capture_output=True);assert p.returncode==1 and p.stderr==b'Usage: rf2-buffer-audit file\n' and not p.stdout;report['fileAndUsageChecks']+=1
  for file,error in [(d/'missing',2),(d,21)]:
   p=subprocess.run([exe,file],capture_output=True);assert p.returncode==1 and json.loads(p.stdout)=={'error':error} and not p.stderr,(file,p.stdout,p.stderr);report['fileAndUsageChecks']+=1
  file=d/'original';file.write_bytes(b'A\0Z\n');link=d/f'link-{opt}';link.symlink_to(file);p=subprocess.run([exe,link],capture_output=True);assert p.returncode==0 and json.loads(p.stdout)==oracle(file.read_bytes());assert file.read_bytes()==b'A\0Z\n';report['fileAndUsageChecks']+=1
  for extra in [0,1]:
   large=d/'large';data=b'Z'*1048576+b'Q'*extra;large.write_bytes(data);p=subprocess.run([exe,large],capture_output=True,timeout=45);assert p.returncode==extra and json.loads(p.stdout)==({'error':22}if extra else oracle(data)) and not p.stderr,(opt,extra,p.returncode,p.stdout,p.stderr);assert large.read_bytes()==data;report['limitChecks']+=1
  # Ordinary return completed before any output. EBADF stdout produces status1.
  p=subprocess.run([exe,file],capture_output=True,preexec_fn=lambda:os.close(1),timeout=30);assert p.returncode==1 and not p.stdout and not p.stderr;report['outputFailureChecks']+=1
  for label,path,expected_tag,expected_value in [('normal',file,0,4),('directory',d,1,21),('over-limit',large,1,22)]:
   src=d/(label+'.rf2');src.write_text('profile RF2_SYSTEM_A64_V1\n'+(R/'examples/buffer-audit/lib/audit.rf2').read_text().replace('module audit\n','')+'''fn main(argc,argv)
 let path=load64(argv+8)
 let before=open(path,0,0)
 do close(before)
 let totals=Stats(0,0,0,0)
 let tag=9
 let value=0
 handle collect(path,totals)
 ok count
  set tag=0
  set value=count
 err cause
  set tag=1
  set value=cause
 end
 let after=open(path,0,0)
 do close(after)
 return (before!=after)|(tag!='''+str(expected_tag)+')|(value!='+str(expected_value)+')\nend\n');probe=d/(label+str(opt));compile(src,probe,opt);p=subprocess.run([probe,path],capture_output=True,timeout=45);assert p.returncode==0,(label,opt,p.returncode,p.stderr);report['cleanupChecks']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),compilerSourceSHA256=SOURCE_HASH,sourceHashScope='Compiler source snapshot at test start; candidate binary hash separately recorded',sourceHashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted((R/'examples/buffer-audit').rglob('*.rf2'))},scope='Finite native app comparisons against independent Python FNV1a64/byte/line oracles in default/optimized modes. Read-only namedinput,1MiB limit. FD checks observe ordinary cleanup in process; no direct mapping-free observation, forced positive shortwrite, physical-memory/performance/cryptographic claim.')
out=Path(os.environ.get('RF2_TEST_REPORT',R/'artifacts/buffer-audit-verification.json'));out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
