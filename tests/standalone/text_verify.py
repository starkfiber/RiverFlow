"""Byte typing, recoverable library errors, UTF-8 oracle and real file cleanup."""
from pathlib import Path
import os,subprocess,tempfile,shutil,random,json,hashlib,re
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-text'));U=(1<<64)-1
io=(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1]
report={'passed':False,'byteCases':0,'byteTraps':0,'compileRefusals':0,'recoverableCases':0,'numericCases':0,'utf8ValidCases':0,'utf8InvalidCases':0,'fileCases':0,'cleanupCases':0,'modes':['default','opt']}
def build(src,out,opt=False,good=True):
 srcpath=out.with_suffix('.rf2');srcpath.write_text(src);p=subprocess.run([C,srcpath,out]+(['--opt']if opt else[]),capture_output=True,timeout=30)
 if not good:assert p.returncode==1 and not out.exists(),p.stderr;return
 assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
def run(path,data=b'',args=()):return subprocess.run([path,*map(str,args)],input=data,capture_output=True,timeout=10)
def expectation(data):
 text=data.decode('utf8');return {'bytes':len(data),'unicode_scalars':len(text),'lf_newlines':text.count('\n'),'ascii_whitespace_words':len(re.findall(r'[^\x00\t\n\v\f\r ]+',text)),'invalid_sequences':0,'first_invalid_byte':None,'nul_scalars':text.count('\0'),'io_status':0,'detail':0}
with tempfile.TemporaryDirectory(prefix='rf2-text-')as tmp:
 d=Path(tmp);shutil.copytree(R/'examples/text-audit/lib',d/'lib');rng=random.Random(202611123)
 for opt in [False,True]:
  # Round-trip every byte, packing, zero initialization and maximum byte-array capacity.
  src='profile RF2_SYSTEM_A64_V1\narray Bytes(u8,255)\nfn main(argc,argv)\nlet data=Bytes()\nlet n=read_bytes(0,data,data.length)\nif n>data.length\nreturn 1\nend\nreturn write_bytes(1,data,n)!=n\nend\n';p=d/f'echo{opt}';build(src,p,opt)
  for data in [bytes(range(255)),bytes([255]),b'',b'\0'*255,bytes(rng.randrange(256)for _ in range(255))]:
   v=run(p,data);assert v.returncode==0 and v.stdout==data and not v.stderr;report['byteCases']+=1
  for value,index in [(256,0),(U,0),(1,8)]:
   src=f'profile RF2_SYSTEM_A64_V1\narray Bytes(u8,8)\nfn main(argc,argv)\nlet data=Bytes()\nset data[{index}]={value}\nreturn 0\nend\n';p=d/f'trap-{value}-{index}-{opt}';build(src,p,opt);v=run(p);assert v.returncode==2 and v.stderr==b'RF2 bounds\n';report['byteTraps']+=1
  # Invalid requests return -22 without consuming stdin or writing output.
  src='profile RF2_SYSTEM_A64_V1\narray Bytes(u8,8)\nfn main(argc,argv)\nlet data=Bytes()\nlet a=read_bytes(0,data,9)\nlet b=write_bytes(1,data,9)\nlet c=read_bytes(0,data,1)\nreturn (a!=18446744073709551594)|(b!=a)|(c!=1)|(data[0]!=65)\nend\n';p=d/f'io-recover{opt}';build(src,p,opt);v=run(p,b'A');assert v.returncode==0 and not v.stdout;report['recoverableCases']+=1
  bad=['read_bytes(0,3,1)','read_bytes(0,data,1,2)','read_bytes(0,data)','read_bytes(data,data,1)','write_bytes(1,words,1)']
  for j,expr in enumerate(bad):
   src='profile RF2_SYSTEM_A64_V1\narray Bytes(u8,8)\narray Words(u64,8)\nfn main(argc,argv)\nlet data=Bytes()\nlet words=Words()\nreturn '+expr+'\nend\n';build(src,d/f'bad-io{j}-{opt}',opt,False);report['compileRefusals']+=1
  for j,decl in enumerate(['fn read_bytes(a,b,c)\nreturn 0\nend\n','array write_bytes(u8,8)\n']):
   build('profile RF2_SYSTEM_A64_V1\n'+decl+'fn main(argc,argv)\nreturn 0\nend\n',d/f'reserved{j}-{opt}',opt,False);report['compileRefusals']+=1
  # Recovery must reset the result record and permit a later successful operation.
  src='profile RF2_SYSTEM_A64_V1\nuse "lib/bytes.rf2"\nfn main(argc,argv)\nlet data=Bytes()\nlet out=Outcome(9,9,9)\ndo bytes_set(data,128,65,out)\nif (out.code!=1)|(out.value!=0)|(out.offset!=128)\nreturn 1\nend\ndo bytes_set(data,0,256,out)\nif out.code!=2\nreturn 2\nend\ndo bytes_set(data,0,65,out)\ndo bytes_get(data,0,out)\nif (out.code!=0)|(out.value!=65)\nreturn 3\nend\ndo bytes_read(999999,data,1,out)\nif (out.code!=5)|(out.offset!=9)\nreturn 4\nend\ndo bytes_get(data,0,out)\nreturn (out.code!=0)|(out.value!=65)\nend\n';p=d/f'recovery{opt}';build(src,p,opt);assert run(p).returncode==0;report['recoverableCases']+=1
  src='profile RF2_SYSTEM_A64_V1\nuse "lib/bytes.rf2"\n'+io+'fn main(argc,argv)\nlet data=Bytes()\nlet out=Outcome(0,0,0)\ndo bytes_read(0,data,data.length,out)\nlet count=out.value\ndo bytes_parse_u64(data,0,count,out)\ndo io_number(out.code)\ndo io_print(" ")\ndo io_number(out.value)\ndo io_print(" ")\ndo io_number(out.offset)\nreturn 0\nend\n';p=d/f'number{opt}';build(src,p,opt)
  values=[b'',b'0',b'00',b'9',str(U).encode(),str(U+1).encode(),b'-1',b'1x',b'\xff',b'9'*128]+[str(rng.randrange(1<<64)).encode()for _ in range(50)]
  for data in values:
   v=run(p,data);code,value,offset=map(int,v.stdout.split());expected=0;n=0;at=0
   if not data:expected=3
   for i,c in enumerate(data):
    if c<48 or c>57:expected=3;at=i;break
    if n>(U-(c-48))//10:expected=4;at=i;break
    n=n*10+c-48
   assert (code,value,offset)==(expected,n if expected==0 else 0,at),(data,v.stdout);report['numericCases']+=1
  app=d/f'audit{opt}';q=subprocess.run([C,R/'examples/text-audit/main.rf2',app]+(['--opt']if opt else[]),capture_output=True);assert q.returncode==0,q.stderr;subprocess.run(['/usr/bin/codesign','-s','-',app],check=True,capture_output=True)
  texts=['','Hello தமிழ் 🌍\n','a\0b\r\nc','e\u0301\u00a0b','\U0010ffff\u0800\u007f\u0080']
  for n in range(124,131):
   for tail in ['¢','€','🌍','தமிழ்']:texts.append('a'*n+tail+'\nend')
  for _ in range(80):
   chars=[]
   for j in range(rng.randrange(1,100)):
    cp=rng.randrange(0x110000)
    if 0xd800<=cp<=0xdfff:cp=32
    chars.append(chr(cp))
   texts.append(''.join(chars))
  for text in texts:
   data=text.encode('utf8');v=run(app,data);assert v.returncode==0 and json.loads(v.stdout)==expectation(data),(data[:30],v.returncode,v.stdout);report['utf8ValidCases']+=1
  invalid=[bytes([i])for i in range(128,256)]+[b'\xc0\xaf',b'\xe0\x80\x80',b'\xed\xa0\x80',b'\xf4\x90\x80\x80',b'\xe2A',b'\xe2\x82',b'abc\xffdef',b'\xffABC\xfe DEF']
  invalid +=[bytes(rng.randrange(256)for _ in range(rng.randrange(1,100)))for _ in range(100)]
  for data in invalid:
   try:data.decode('utf8');continue
   except UnicodeDecodeError as e:first=e.start
   v=run(app,data);x=json.loads(v.stdout);assert v.returncode==2 and x['bytes']==len(data) and x['invalid_sequences']>0 and x['first_invalid_byte']==first and x['io_status']==0,(data,v.returncode,x,first);report['utf8InvalidCases']+=1
  # Owned files close on success, read failure and input-limit failure. Check in the same process.
  src='profile RF2_SYSTEM_A64_V1\nuse "lib/audit.rf2"\nfn main(argc,argv)\nlet state=TextState(0,0,0,0,0,0,0,0,0,0,18446744073709551615,0)\nlet out=Outcome(0,0,0)\nlet probe=open(load64(argv+8),0,0)\nif probe>=9223372036854775808\nreturn 3\nend\ndo close(probe)\ndo audit_file(load64(argv+8),state,out)\nlet data=Bytes()\nlet closed=read_bytes(probe,data,1)\nreturn closed!=18446744073709551607\nend\n';cleanup=d/f'cleanup{opt}';build(src,cleanup,opt)
  f=d/'text.txt';f.write_bytes('தமிழ்\n'.encode());large=d/'large.txt';large.write_bytes(b'A'*(1048576+1))
  for path in [f,d,large]:
   v=run(cleanup,args=[path]);assert v.returncode==0,(path,v.returncode,v.stderr);report['cleanupCases']+=1
  for path,code,status in [(f,0,0),(d,1,5),(large,1,6),(d/'absent',1,5)]:
   v=run(app,args=[path]);x=json.loads(v.stdout);assert v.returncode==code and x['io_status']==status,(path,v.returncode,x);report['fileCases']+=1
  v=run(app,args=[f,f]);assert v.returncode==1;report['fileCases']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),compilerSourceSHA256=hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(R/'examples/text-audit').rglob('*.rf2')},scope='Local default/optimized typed bytes, explicit recoverable status libraries, strict UTF-8 validity/first-error versus Python; invalid grouping is the documented audit policy, not Unicode replacement conformance. File close checked in process. No general exception/ownership proof, thread model, new MCP authority, speed/token claim or phone qualification.')
(R/'docs/TEXT-BYTES-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
