"""Independent native hexdump application oracles. Local disposable files only.

Full output is compared with a Python byte-formatting oracle, not the RF2 formatter.
No performance, token, fieldwork or universal ownership claim.
"""
from pathlib import Path
import hashlib,json,os,random,subprocess,tempfile
R=Path(__file__).resolve().parents[2]
C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c')).resolve()
report={'passed':False,'appComparisons':0,'fileAndUsageChecks':0,'inProcessCleanupChecks':0,'inputLimitChecks':0}
def compile(src,out,opt):
 p=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True,timeout=30);assert p.returncode==0,p.stderr
 subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True)
def expected(data):
 rows=[]
 for offset in range(0,len(data),16):
  part=data[offset:offset+16]
  hexcells=''.join(f'{b:02X} 'for b in part)+'   '*(16-len(part))
  ascii=''.join(chr(b)if 32<=b<=126 else'.'for b in part)+' '*(16-len(part))
  rows.append(f'{offset:016X}  {hexcells} |{ascii}|\n')
 return ''.join(rows).encode()
def run(exe,path=None,**kw):return subprocess.run([exe]+([]if path is None else[path]),capture_output=True,timeout=30,**kw)
randomizer=random.Random(15001)
cases=[b'',b'\0',bytes(range(256)),b'0123456789ABCDEF',b'0123456789ABCDEFG',b'\r\n\t\x7f\xff','தமிழ் 🌍\n'.encode()]
cases +=[bytes(randomizer.randrange(256)for _ in range(n))for n in [1,2,7,15,16,17,31,32,33,127,128,129,255,256,257,1023,1024,1025,4097]]
cases +=[bytes(randomizer.randrange(256)for _ in range(randomizer.randrange(300)))for _ in range(55)]
with tempfile.TemporaryDirectory(prefix='rf2-hex-app-')as td:
 d=Path(td)
 for opt in [False,True]:
  exe=d/f'hex-{opt}';compile(R/'examples/hex/main.rf2',exe,opt)
  for i,data in enumerate(cases):
   file=d/f'input {i} தமிழ்.bin';file.write_bytes(data);p=run(exe,file);assert p.returncode==0 and p.stdout==expected(data) and not p.stderr,(opt,i,p.returncode,p.stderr,p.stdout[:100]);assert file.read_bytes()==data;report['appComparisons']+=1
  p=run(exe);assert p.returncode==1 and p.stderr==b'Usage: rf2-hex file\n' and not p.stdout;report['fileAndUsageChecks']+=1
  p=subprocess.run([exe,'one','two'],capture_output=True);assert p.returncode==1 and p.stderr==b'Usage: rf2-hex file\n';report['fileAndUsageChecks']+=1
  for bad in [d/'does-not-exist',d]:
   p=run(exe,bad);assert p.returncode==1 and p.stderr==b'RF2 hex input/output failure\n' and not p.stdout;report['fileAndUsageChecks']+=1
  target=d/'symlink-target';target.write_bytes(b'A\0Z');link=d/f'link-{opt}';link.symlink_to(target);p=run(exe,link);assert p.returncode==0 and p.stdout==expected(target.read_bytes());report['fileAndUsageChecks']+=1
  # A cap is processed-input policy, not a silent truncation success.
  for extra in [0,1]:
   file=d/'large.bin';file.write_bytes(b'Z'*(1048576+extra));p=run(exe,file);assert p.returncode==(1 if extra else 0);assert p.stdout==expected(b'Z'*1048576);assert p.stderr==(b'RF2 hex input/output failure\n'if extra else b'');report['inputLimitChecks']+=1
  for label,body in [
   ('normal','''let before=open(path,0,0)
 do close(before)
 let status=0
 handle hex_file(path)
 ok count
  set status=count!=3
 err e
  set status=1
 end
 let after=open(path,0,0)
 do close(after)
 return status|(before!=after)'''),
   ('read-error','''let before=open(path,0,0)
 do close(before)
 let status=1
 handle hex_file(path)
 ok count
  set status=1
 err e
  set status=e!=21
 end
 let after=open(path,0,0)
 do close(after)
 return status|(before!=after)'''),
   ('output-error','''do close(1)
 let before=open(path,0,0)
 do close(before)
 let status=1
 handle hex_file(path)
 ok count
  set status=1
 err e
  set status=e!=9
 end
 let after=open(path,0,0)
 do close(after)
 return status|(before!=after)''')]:
   # Main wrapper source resides inside the app entry directory so immutable imports resolve.
   src=d/f'{label}-{opt}.rf2';module=(R/'examples/hex/lib/hex.rf2').read_text().replace('module hex\n','');src.write_text('profile RF2_SYSTEM_A64_V1\n'+module+'\nfn main(argc,argv)\n let path=load64(argv+8)\n '+body+'\nend\n');probe=d/f'{label}-{opt}';compile(src,probe,opt)
   file=d/'probe.bin';file.write_bytes(b'abc');p=run(probe,d if label=='read-error' else file);assert p.returncode==0,(label,opt,p.returncode,p.stderr);assert p.stdout==(expected(b'abc')if label=='normal'else b'');report['inProcessCleanupChecks']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),compilerSourceSHA256=hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),sourceHashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted((R/'examples/hex').rglob('*.rf2'))},scope='Finite default/optimized full-byte-output comparisons, unchanged inputs and in-process descriptor reuse after normal/read/output failure. Symlinks follow ordinary read-only open semantics. No forced short-write injection, trap cleanup, ownership proof or performance claim.')
out=Path(os.environ.get('RF2_TEST_REPORT',R/'artifacts/hex-app-verification.json'));out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
