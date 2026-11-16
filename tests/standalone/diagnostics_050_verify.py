"""Native diagnostic wire and expanded function-table qualification; no provider calls."""
from pathlib import Path
import hashlib,json,os,re,subprocess,tempfile
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_DIAGNOSTIC_COMPILER']).resolve()
B=Path(os.environ.get('RF2_DIAGNOSTIC_BASELINE',R/'artifacts/application-epochs-049-xscp6q0s/candidate-049-a/build/program')).resolve()
SOURCE=Path(os.environ['RF2_DIAGNOSTIC_SOURCE']).resolve()
D=Path(tempfile.mkdtemp(prefix='diagnostics-050-checks-',dir=R/'artifacts'));checks=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,passed,detail=None):
 checks.append(dict(name=name,passed=bool(passed),detail=detail))
 (D/'RESULTS.json').write_text(json.dumps(dict(compilerSHA256=sha(C),compilerSourceSHA256=sha(SOURCE),baselineSHA256=sha(B),checks=checks,allPassed=all(x['passed']for x in checks)),indent=2)+'\n')
 if not passed:raise AssertionError((name,detail,D))
def run(args):return subprocess.run([str(C),*map(str,args)],capture_output=True,timeout=30)
def signed(exe):subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],check=True,capture_output=True)
header='profile RF2_SYSTEM_A64_V1\n'
cases=[
 ('unknown-local','fn main(argc,argv)\n return absent\nend\n','RF2E_LOCAL','unknown local'),
 ('unknown-function','fn main(argc,argv)\n return absent()\nend\n','RF2E_FUNCTION','unknown function'),
 ('too-few-arguments','fn add(a,b)\n return a+b\nend\nfn main(argc,argv)\n return add(1)\nend\n','RF2E_ARITY','function arity'),
 ('too-many-arguments','fn add(a,b)\n return a+b\nend\nfn main(argc,argv)\n return add(1,2,3)\nend\n','RF2E_ARITY','function arity'),
 ('nominal-argument','record One(value:u64)\nrecord Two(value:u64)\nfn get(row:One)\n return row.value\nend\nfn main(argc,argv)\n let row=Two(4)\n return get(row)\nend\n','RF2E_ARGUMENT_TYPE','argument type mismatch'),
 ('parameter-type','fn get(row:Absent)\n return 0\nend\nfn main(argc,argv)\n return 0\nend\n','RF2E_TYPE','unknown parameter type'),
 ('unknown-field','record Row(value:u64)\nfn main(argc,argv)\n let row=Row(4)\n return row.absent\nend\n','RF2E_FIELD','unknown record field'),
 ('escaped-scope','fn main(argc,argv)\n if argc\n  let inside=1\n end\n return inside\nend\n','RF2E_LIFETIME','local used before initialization or outside scope'),
 ('fallback','fn main(argc,argv)\n nonsense\n return 0\nend\n','RF2E_COMPILE','unsupported statement'),
]
for opt in(False,True):
 for name,body,code,message in cases:
  p=D/(name+str(opt)+'.flow');p.write_text(header+body);exe=p.with_suffix('')
  args=[p,exe,'--compact',*(['--opt']if opt else[])]
  q=run(args+['--diagnostic-json']);raw=q.stderr
  check(name+' rejects '+str(opt),q.returncode==1 and not q.stdout and not exe.exists(),[q.returncode,q.stdout.decode(errors='replace'),raw.decode(errors='replace')])
  check(name+' one JSON line '+str(opt),raw.endswith(b'\n')and len(raw.splitlines())==1,raw.decode(errors='replace'))
  event=json.loads(raw)
  check(name+' stable category '+str(opt),event['schema']=='rf2.diagnostic.v1'and event['code']==code and event['message']==message,event)
  loc=event['location'];check(name+' source cursor '+str(opt),loc and loc['line']>=2 and loc['byteColumn']>=1 and Path(loc['path'])==p,event)
  if code!='RF2E_COMPILE':check(name+' actionable hint '+str(opt),len(event['hint'])>30,event['hint'])
  q=run(args);check(name+' human compatibility '+str(opt),q.returncode==1 and message.encode()in q.stderr and(q.stderr.startswith(b'{')is False),q.stderr.decode(errors='replace'))
# Exact byte-escaped path, control bytes, UTF-8 comments and CRLF origins.
for suffix in('quote"slash\\line\n-é','normal'):
 sub=D/suffix;(sub/'lib').mkdir(parents=True)
 main=sub/'main.flow';bad=sub/'lib'/'bad\t-é.flow'
 main.write_text(header+'use "lib/bad\t-é.flow"\nfn main(argc,argv)\n return bad()\nend\n')
 # Module names only allow the established safe import path alphabet; use a safe
 # module path and exercise arbitrary entry directory bytes instead.
 bad=sub/'lib'/'bad.flow';main.write_text(header+'use "lib/bad.flow"\nfn main(argc,argv)\n return bad()\nend\n')
 bad.write_bytes('module bad\r\n# தமிழ்\r\nfn bad()\r\n return absent\r\nend\r\n'.encode())
 q=run([main,sub/'program','--diagnostic-json']);event=json.loads(q.stderr);loc=event['location'];path=loc['path'].encode('latin1')
 check('import exact escaped path '+suffix,path==os.fsencode(bad)and loc['line']==4 and loc['origin']=='source',event)
 check('escaped path is one JSON line '+suffix,len(q.stderr.splitlines())==1 and q.returncode==1,event)
# Fatal admission errors have no fabricated source line. Unknown/duplicate flags
# preserve JSON even before diagnostic state is enabled.
p=D/'valid.flow';p.write_text(header+'fn main(argc,argv)\n return 7\nend\n')
for name,args in [
 ('missing-arguments',['--diagnostic-json']),
 ('unknown-option',[p,D/'bad','--diagnostic-json','--no-such-option']),
 ('duplicate-option',[p,D/'bad','--diagnostic-json','--diagnostic-json']),
 ('missing-import',[D/'missing.flow',D/'bad','--diagnostic-json']),
]:
 q=run(args);e=json.loads(q.stderr);check('early error '+name,q.returncode==1 and e['location']is None and len(q.stderr.splitlines())==1,e)
missing=D/'missing-import.flow';missing.write_text(header+'use "absent.flow"\nfn main(argc,argv)\n return 0\nend\n')
q=run([missing,D/'missing-import-out','--diagnostic-json']);e=json.loads(q.stderr)
check('missing imported source actionable without fabricated location',q.returncode==1 and e['code']=='RF2E_SOURCE_IO' and e['location']is None and '--sdk-root'in e['hint'],e)
for flag in ([],['--diagnostic-json']):
 q=run(['--check',p,*flag]);check('check valid no image '+str(flag),q.returncode==0 and b'checked'in q.stdout,q.stderr.decode())
q=run(['--check','--diagnostic-json']);e=json.loads(q.stderr);check('check missing source option refused',q.returncode==1 and e['location']is None,e)
for opt in(False,True):
 outputs=[]
 for compiler,label,jsonflag in[(B,'base',False),(C,'human',False),(C,'json',True)]:
  exe=D/(label+str(opt));q=subprocess.run([str(compiler),str(p),str(exe),'--compact',*(['--opt']if opt else[]),*(['--diagnostic-json']if jsonflag else[])],capture_output=True,timeout=30)
  check('valid compile '+label+str(opt),q.returncode==0,q.stderr.decode());outputs.append(exe.read_bytes());signed(exe)
  check('valid execution '+label+str(opt),subprocess.run([str(exe)],capture_output=True).returncode==7)
 check('diagnostics preserve emitted image '+str(opt),outputs[0]==outputs[1]==outputs[2])
# Bound expansion inventory is explicit, not a global replacement of256.
source=SOURCE.read_text()
expected={'functions':24576,'locals':1048576,'local_scope':1048576,'local_binding':1048576,'function_result':4096,'local_types':1048576,'local_ready':1048576,'array_arena_sizes':4096,'array_payload_offsets':1048576,'function_leaf':4096,'cleanup_count':4096,'cleanup_slots':65536,'cleanup_owned':65536,'cleanup_spans':65536,'function_code_ranges':8192,'reuse_units':65536,'owned_result_slots':4096,'owned_parameters':32768}
for name,size in expected.items():
 sizes=[int(n)for n in re.findall(r'buffer\("'+name+r'",\s*(\d+)\)',source)]
 check('function table capacity '+name,sizes==[size],sizes)
check('local and record limits unchanged','do require(j < 256, "local bound")'in source and '(id <= 32), "record bound"'in source)
# Exercise function index511 with local scalar/record/array/resource/result metadata.
# Each dummy has distinct arithmetic so call-address or table aliasing is visible.
parts=[header,'result IO(u64,u64)\nresource File(IO)\nrecord Row(value:u64)\narray Data(u64,4096)\n']
for i in range(509):parts.append('fn f'+str(i)+'(n)\n return n+'+str(i)+'\nend\n')
parts.append('fn high(a,b,c,d,e,f,g,h):IO\n let row=Row(a+b+c+d+e+f+g+h)\n let data=Data()\n set data[4095]=row.value\n own file=File("/dev/null",0,0)\n return ok(data[4095]+f508(1))\nend\n')
parts.append('fn leaf(n)\n return f0(n)+f508(n)\nend\n')
parts.append('fn main(argc,argv)\n let result=0\n handle high(1,2,3,4,5,6,7,8)\n ok value\n  set result=value\n err cause\n  return 200\n end\n let fd=open("/dev/null",0,0)\n do close(fd)\n if (fd!=3)|(result!=545)|(leaf(1)!=510)\n  return 201\n end\n return 0\nend\n')
many=D/'512.flow';many.write_text(''.join(parts))
for opt in(False,True):
 exe=D/('512-'+str(opt));q=run([many,exe,'--compact',*(['--opt']if opt else[]),'--diagnostic-json']);check('512-function compile '+str(opt),q.returncode==0,q.stderr.decode());clean_image=exe.read_bytes();signed(exe)
 q=subprocess.run([str(exe)],capture_output=True);check('high-index frames/cleanup/results '+str(opt),q.returncode==0,[q.returncode,q.stderr.decode()])
 too=D/('513-'+str(opt)+'.flow');too.write_text(many.read_text()+'fn overflow()\n return 1\nend\n');out=too.with_suffix('')
 q=run([too,out,'--compact',*(['--opt']if opt else[]),'--diagnostic-json']);e=json.loads(q.stderr);check('513-function boundary refusal '+str(opt),q.returncode==1 and e['message']=='function bound'and not out.exists(),e)
 # Scalar leaf cache at high index, same-byte clean and warm pack images.
 cache=D/('cache-'+str(opt));cache.mkdir(mode=0o700);images=[]
 for round in range(2):
  out=D/('reuse-'+str(opt)+'-'+str(round));q=run([many,out,'--compact',*(['--opt']if opt else[]),'--reuse-pack',cache,'--diagnostic-json']);check('high-index reuse compile '+str((opt,round)),q.returncode==0,q.stderr.decode());images.append(out.read_bytes())
 check('high-index reuse equals clean '+str(opt),images[0]==images[1]==clean_image)
# Pointer-bearing result/consuming-parameter metadata must also be disjoint at
# function indexes above the previous256 boundary, not only plain scalar rows.
owned=[header,'result IO(u64,u64)\ntext Name(IO,32)\nresult Held(own Name,u64)\n']
for i in range(300):owned.append('fn pad'+str(i)+'()\n return '+str(i)+'\nend\n')
owned.append('fn make(n):Held\n own name=Name()\n handle text_append(name,65+n)\n ok value\n err cause\n  return err(cause)\n end\n return ok(move(name))\nend\n')
owned.append('fn consume(own name:Name,n):IO\n handle text_get(name,0)\n ok value\n  if value!=65+n\n   return err(202)\n  end\n err cause\n  return err(cause)\n end\n if n\n  return err(71)\n end\n return ok(0)\nend\n')
owned.append('fn work(n):IO\n handle make(n)\n ok own value:Name\n  handle consume(move(value),n)\n  ok done\n  err consumed_error\n   return err(consumed_error)\n  end\n err cause\n  return err(cause)\n end\n return ok(0)\nend\n')
owned.append('fn main(argc,argv)\n handle work(argc-1)\n ok done\n  return 0\n err cause\n  return cause\n end\n return 203\nend\n')
p=D/'high-owned.flow';p.write_text(''.join(owned))
for opt in(False,True):
 exe=D/('high-owned-'+str(opt));q=run([p,exe,'--compact',*(['--opt']if opt else[]),'--diagnostic-json']);check('high-index owned result and consuming parameter compile '+str(opt),q.returncode==0,q.stderr.decode());signed(exe)
 for args,expected in[([],0),(['x'],71)]:
  q=subprocess.run([str(exe),*args],capture_output=True);check('high-index owner transfer/cleanup '+str((opt,args)),q.returncode==expected,[q.returncode,q.stderr.decode()])
print(json.dumps(dict(directory=str(D),finalChecks=len(checks),allPassed=True)))
