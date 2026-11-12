"""Independent expected outcomes for the real typed-result/read-only-view app."""
from pathlib import Path
import os,subprocess,tempfile,shutil,random,json,hashlib
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-results-views'));U=(1<<64)-1
report={'passed':False,'appCases':0,'fileCases':0,'cleanupCases':0,'parseCases':0,'additionalInitRefusals':0,'modes':['default','opt']}
def compile(src,out,opt):
 p=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True,timeout=30);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
def run(p,data=b'',args=()):return subprocess.run([p,*map(str,args)],input=data,capture_output=True,timeout=20)
def oracle(data):
 x={'accepted':0,'rejected':0,'sum':0,'first_error_line':0,'first_error_code':0,'bytes':len(data),'io_error':0}
 lines=data.split(b'\n')
 if data.endswith(b'\n')or not data:lines=lines[:-1]
 for i,row in enumerate(lines,1):
  clean=row.strip(b' \t\r');code=0;value=0
  if len(row)>128:code=4
  elif not clean:code=1
  elif any(c<48 or c>57 for c in clean):code=2
  else:
   value=int(clean)
   if value>U:code=3
   elif value>U-x['sum']:code=5
  if code:
   if x['rejected']==0:x.update(first_error_line=i,first_error_code=code)
   x['rejected']+=1
  else:x['accepted']+=1;x['sum']+=value
 return x
with tempfile.TemporaryDirectory(prefix='rf2-result-app-')as tmp:
 d=Path(tmp);shutil.copytree(R/'examples/number-audit/lib',d/'lib');rng=random.Random(202611124)
 for opt in [False,True]:
  app=d/f'app{opt}';compile(R/'examples/number-audit/main.rf2',app,opt)
  inputs=[b'',b'12\nbad\n30\n',b'\n',b' 42\t\r\n0',str(U).encode()+b'\n1\n0\n',b'0'*128,b'0'*129,b'9'*129+b'\n7\n',b'\xff\n3',b'1\r\n2\r\n',b'\x00\n7\n']
  for _ in range(100):
   rows=[]
   for j in range(rng.randrange(1,25)):
    rows.append(rng.choice([str(rng.randrange(10**12)).encode(),b'bad',b'',b'\t 17\r',b'18446744073709551616',b'x'*129,b'\0']))
   data=b'\n'.join(rows)+(b'\n'if rng.randrange(2)else b'');inputs.append(data)
  for data in inputs:
   p=run(app,data);want=oracle(data);assert p.returncode==(2 if want['rejected']else 0)and json.loads(p.stdout)==want,(data[:100],p.returncode,p.stdout,want);report['appCases']+=1
  # Direct typed parser, exercising runtime chosen view length and typed result branches.
  source='''profile RF2_SYSTEM_A64_V1
use "lib/parse.rf2"
use "lib/io.rf2"
fn main(argc,argv)
 let data=Bytes()
 let count=read_bytes(0,data,data.length)
 let code=0
 let answer=0
 handle parse_line(data,count)
 ok value
  set answer=value
 err cause
  set code=cause
 end
 do io_number(code)
 do io_print(" ")
 do io_number(answer)
 return 0
end
''';src=d/f'parse{opt}.rf2';src.write_text(source);path=d/f'parse{opt}';compile(src,path,opt)
  for data in [b'',b' ',b'0',b'42',str(U).encode(),str(U+1).encode(),b'\xff',b'-1',b'1x',b'\t42\r']:
   p=run(path,data);code,n=map(int,p.stdout.split());clean=data.strip(b' \t\r');expected=1 if not clean else 2 if any(c<48 or c>57 for c in clean)else 3 if int(clean)>U else 0;assert (code,n)==(expected,int(clean)if expected==0 else 0);report['parseCases']+=1
  # Root self-initialization must fail through all constant/register lowering paths.
  for j,body in enumerate(['let x=x+1','let x=x-1','let y=7\nlet x=x+y','let x=x*33','let x=(x+1)&4294967295']):
   src=d/f'init{j}-{opt}.rf2';src.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n'+body+'\nreturn x\nend\n');out=d/f'init{j}-{opt}';p=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True);assert p.returncode==1 and not out.exists();report['additionalInitRefusals']+=1
  source='''profile RF2_SYSTEM_A64_V1
use "lib/audit.rf2"
fn main(argc,argv)
 let totals=Totals(0,0,0,0,0,0,0)
 let probe=open(load64(argv+8),0,0)
 if probe>=9223372036854775808
  return 3
 end
 do close(probe)
 do run_file(load64(argv+8),totals)
 let data=Bytes()
 let closed=read_bytes(probe,data,1)
 return closed!=18446744073709551607
end
''';src=d/f'close{opt}.rf2';src.write_text(source);path=d/f'close{opt}';compile(src,path,opt)
  valid=d/'numbers.txt';valid.write_bytes(b'12\nbad\n30\n');large=d/'large.txt';large.write_bytes(b'x'*(1048576+1))
  for name in [valid,d,large]:
   p=run(path,args=[name]);assert p.returncode==0,(name,p.returncode,p.stderr);report['cleanupCases']+=1
  for name,status,io in [(valid,2,0),(d,1,21),(large,1,1000),(d/'absent',1,2)]:
   p=run(app,args=[name]);x=json.loads(p.stdout);assert p.returncode==status and x['io_error']==io,(name,p.returncode,x);report['fileCases']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),compilerSourceSHA256=hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),sourceHashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(R/'examples/number-audit').rglob('*.rf2')},scope='Finite host app/oracle comparisons and compile refusals in both modes. Typed results have scalar payloads; views are byte-indexed and read-only, not implicit Unicode validation. No performance or whole-program safety claim.')
(R/'docs/RESULTS-VIEWS-APP-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
