"""Document auditor checks against Python strict UTF8, independently computed metrics."""
from pathlib import Path
import hashlib,json,os,random,shutil,subprocess,tempfile
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c'))
def compile(src,out,opt):
 p=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True,timeout=30);assert p.returncode==0,p.stderr
 subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
def run(out,data=b'',args=()):return subprocess.run([out,*map(str,args)],input=data,capture_output=True,timeout=20)
def oracle(data):
 d=dict(valid_lines=0,rejected_lines=0,unicode_scalars=0,non_ascii_scalars=0,tamil_scalars=0,first_error_line=0,first_error_code=0,bytes=len(data),io_error=0)
 rows=data.split(b'\n')
 if not data or data.endswith(b'\n'):rows=rows[:-1]
 for i,row in enumerate(rows,1):
  code=0;text=''
  if len(row)>255:code=2
  else:
   try:text=row.decode('utf-8','strict')
   except UnicodeDecodeError:code=1
  if code:
   if not d['rejected_lines']:d.update(first_error_line=i,first_error_code=code)
   d['rejected_lines']+=1
  else:
   d['valid_lines']+=1;d['unicode_scalars']+=len(text);d['non_ascii_scalars']+=sum(ord(c)>=128 for c in text);d['tamil_scalars']+=sum(0xb80<=ord(c)<=0xbff for c in text)
 return d
rng=random.Random(20261112014)
inputs=[b'',b'\n',b'\n\n',b'A\nB',b'A\r\nB\r\n',b'\0\nX\0', 'தமிழ்\nவணக்கம்\nHello\n'.encode(),'e\u0301\n👩🏽\u200d💻\n🇲🇾\n'.encode(),b'\xff\nNext\n',b'bad\xc0\x80\ngood',b'\xed\xa0\x80\nOK',b'\xf4\x90\x80\x80\nOK',b'\xe2\x82',b'x'*255,b'x'*256,b'x'*256+'\nதமிழ்\n'.encode(),b'A'*254+b'\n'+b'\xf0\x9f\x8c\x8d\n',b'\xef\xbb\xbf\xef\xbf\xbf\0']
inputs.extend([b'A'*249+b'\n'+b'A'*3+'🌍'.encode()+b'\n',b'A'*251+'🌍'.encode(),b'\xe2\x82\nNext\n'])
for _ in range(120):
 rows=[]
 for j in range(rng.randrange(1,18)):
  if rng.randrange(3)==0:rows.append(bytes(rng.randrange(256)for k in range(rng.randrange(0,280))).replace(b'\n',b'X'))
  else:rows.append(''.join(chr(rng.choice([0,32,127,128,0xb85,0xbc0,0x301,0x1f600,0x10ffff]))for k in range(rng.randrange(0,75))).encode())
 data=b'\n'.join(rows)+(b'\n'if rng.randrange(2)else b'');inputs.append(data)
report=dict(passed=False,appCases=0,fileCases=0,cleanupChecks=0,limitCases=0,modes=['default','opt'])
with tempfile.TemporaryDirectory(prefix='rf2-unicode-lines-')as tmp:
 d=Path(tmp);shutil.copytree(R/'examples/unicode-lines/lib',d/'lib')
 for opt in [False,True]:
  out=d/f'app{opt}';compile(R/'examples/unicode-lines/main.rf2',out,opt)
  for data in inputs:
   p=run(out,data);expected=oracle(data);assert p.returncode==(2 if expected['rejected_lines']else 0),(p.returncode,p.stderr);assert json.loads(p.stdout)==expected,(data[:80],p.stdout,expected);report['appCases']+=1
  for i,data in enumerate(inputs[:18]):
   path=d/f'input{i}';path.write_bytes(data);p=run(out,args=[path]);assert p.returncode==(2 if oracle(data)['rejected_lines']else 0);assert json.loads(p.stdout)==oracle(data);assert path.read_bytes()==data;report['fileCases']+=1
  p=run(out,args=[d/'absent']);assert p.returncode==1 and json.loads(p.stdout)['io_error']==2;report['fileCases']+=1
  p=run(out,args=[d]);assert p.returncode==1 and json.loads(p.stdout)['io_error']==21;report['fileCases']+=1
  p=run(out,args=[d,d]);assert p.returncode==1 and b'Usage:'in p.stdout;report['fileCases']+=1
  p=run(out,b'A'*(1048576+1));q=json.loads(p.stdout);assert p.returncode==1 and q['io_error']==1000 and q['bytes']==1048576;report['limitCases']+=1
  # In-process closure, including a failed read; process teardown cannot satisfy this oracle.
  src=d/f'cleanup{opt}.rf2';exe=d/f'cleanup{opt}'
  src.write_text('''profile RF2_SYSTEM_A64_V1
use "lib/audit.rf2"
fn main(argc,argv)
 let s=Totals(0,0,0,0,0,0,0,0,0)
 let fd=open(load64(argv+8),0,0)
 if fd>=9223372036854775808
  return 10
 end
 do run_owned(fd,s)
 if close(fd)!=18446744073709551607
  return 11
 end
 return 0
end
''');compile(src,exe,opt)
  path=d/'empty';path.write_bytes(b'')
  for target in [path,d]:
   p=run(exe,args=[target]);assert p.returncode==0,(p.returncode,p.stderr);report['cleanupChecks']+=1
  # Borrowed stdin is still open after the reader returns, even at EOF.
  src=d/f'stdin{opt}.rf2';exe=d/f'stdin{opt}';src.write_text('''profile RF2_SYSTEM_A64_V1
use "lib/audit.rf2"
fn main(argc,argv)
 let s=Totals(0,0,0,0,0,0,0,0,0)
 do run_fd(0,s)
 return close(0)!=0
end
''');compile(src,exe,opt);p=run(exe,b'Hi\n');assert p.returncode==0;report['cleanupChecks']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),compilerSourceSHA256=hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),sourceHashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted((R/'examples/unicode-lines').rglob('*.rf2'))},scope='Finite native document app comparisons in default/optimized modes. Python strict UTF8 oracle. Explicit read-only input, bounded rows/input. No normalization/grapheme/performance/security certification.')
out=Path(os.environ.get('RF2_TEST_REPORT',R/'artifacts/unicode-lines-verification.json'));out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
