"""Bounded randomized native reuse campaign with independent u64 arithmetic oracles.

No network traffic. All outputs are created under one exclusive local campaign.
A failure stops the campaign and preserves its full executable/source evidence.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,random,subprocess,time
R=Path(__file__).resolve().parents[1]
C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
REUSE_FLAG=os.environ.get('RF2_FUNCTION_REUSE_FLAG','--reuse-cache');assert REUSE_FLAG in ['--reuse-cache','--reuse-pack']
LIMIT=int(os.environ.get('RF2_STRESS_PROGRAMS','4000'));assert 1<=LIMIT<=4000
DEADLINE=datetime.fromisoformat(os.environ['RF2_STRESS_DEADLINE']).timestamp()if os.environ.get('RF2_STRESS_DEADLINE')else time.time()+900
D=R/'artifacts/reuse-stress-029'/('run-'+str(time.time_ns()));D.mkdir(parents=True)
MASK=(1<<64)-1;rng=random.Random(29013116)
controller_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();compiler_hash=hashlib.sha256(C.read_bytes()).hexdigest()
rows=[];started=time.time();current=None
OPS=['+','-','*','//','&','|','^','<<','>>','==','!=','<','<=','>','>=']
def atom(env):
 if env and rng.randrange(4):
  name=rng.choice(list(env));return name,env[name]
 value=rng.choice([0,1,2,7,31,32,63,64,65,255,65535,MASK,1<<63,rng.getrandbits(64)])
 return str(value),value
def expression(env,depth=0):
 if depth>=4 or rng.randrange(4)==0:return atom(env)
 if rng.randrange(7)==0:
  text,value=expression(env,depth+1);op=rng.choice(['-','~']);return '('+op+text+')',(-value if op=='-'else~value)&MASK
 left,a=expression(env,depth+1);right,b=expression(env,depth+1);op=rng.choice(OPS)
 if op=='+':v=a+b
 elif op=='-':v=a-b
 elif op=='*':v=a*b
 elif op=='//':v=a//b if b else 0
 elif op=='&':v=a&b
 elif op=='|':v=a|b
 elif op=='^':v=a^b
 elif op=='<<':v=a<<(b&63)
 elif op=='>>':v=a>>(b&63)
 else:v=int({'==':a==b,'!=':a!=b,'<':a<b,'<=':a<=b,'>':a>b,'>=':a>=b}[op])
 return '('+left+' '+op+' '+right+')',v&MASK
def program(index):
 env={name:rng.getrandbits(64)for name in ['a','b','c']};args=env.copy();lines=[]
 count=rng.choice([0,1,2,4,5,7,8,12,24,48,96])
 for i in range(count):
  text,value=expression(env);name='v'+str(i);lines.append(' let '+name+' = '+text);env[name]=value
  if rng.randrange(3)==0:
   target=rng.choice(list(env));text,value=expression(env);lines.append(' set '+target+' = '+text);env[target]=value
 text,value=expression(env);lines.append(' return '+text)
 helper='fn calculate(a,b,c)\n'+'\n'.join(lines)+'\nend\n'
 stable='fn stable(x)\n let t = x*3\n set t = (t+7)&65535\n return t\nend\n'
 # A changed preceding main body shifts helper placement without changing helper tokens.
 main='fn main(argc,argv)\n let prefix = '+str(rng.getrandbits(64))+'\n let answer = calculate('+','.join(str(args[x])for x in ['a','b','c'])+')\n let p = buffer("answer",8)\n do store64(p,answer)\n do write(1,p,8)\n return 0\nend\n'
 source='profile RF2_SYSTEM_A64_V1\n'+(main+helper+stable if index%3==0 else helper+stable+main)
 changed=source.replace('let prefix = ','let prefix = 18446744073709551615 ^ ',1)
 return source,changed,value,count

def invoke(args,timeout=45):return subprocess.run([str(x)for x in args],capture_output=True,timeout=timeout,env={'PATH':'/nonexistent'})
def build(source,out,opt,cache=None):
 q=invoke([C,source,out,'--compact',*(['--opt']if opt else[]),*([REUSE_FLAG,cache]if cache else[])])
 assert q.returncode==0,(out.name,q.returncode,q.stdout[:200],q.stderr[:1000]);raw=out.read_bytes()
 receipt=json.loads(Path(str(out)+'.reuse.json').read_text())if cache else None
 return raw,receipt
def observe(out,expected):
 q=invoke(['/usr/bin/codesign','-s','-',out]);assert q.returncode==0,q.stderr
 q=invoke([out],10);assert q.returncode==0 and q.stdout==expected.to_bytes(8,'little')and not q.stderr,(out.name,q.returncode,q.stdout.hex(),q.stderr[:300],expected)

def checkpoint(status,error=None):
 data=dict(schema='rf2.reuse.stress.v1',status=status,reuseFlag=REUSE_FLAG,passed=status in ['complete','deadline-complete'],programLimit=LIMIT,completedPrograms=len(rows),seed=29013116,compilerSHA256=compiler_hash,controllerSHA256=controller_hash,startedUTC=datetime.fromtimestamp(started,timezone.utc).isoformat(),finishedUTC=datetime.now(timezone.utc).isoformat(),deadlineUTC=datetime.fromtimestamp(DEADLINE,timezone.utc).isoformat(),rows=rows,currentCase=str(current)if current else None,error=error,limits='Finite one-host randomized scalar linear programs. Current-mode clean byte equality and independent u64 result oracle, including wrapping arithmetic, shifts modulo64 and division byzero result0. Compiler execution only, no MCP authority expansion, hardware/energy/token or universal safety claim.')
 (D/'progress.json').write_text(json.dumps(data,indent=2)+'\n');return data
print(json.dumps({'campaign':str(D),'programLimit':LIMIT,'deadlineUTC':datetime.fromtimestamp(DEADLINE,timezone.utc).isoformat()}),flush=True)
try:
 for index in range(LIMIT):
  while (D/'PAUSE').exists() and time.time()<DEADLINE:
   checkpoint('paused');time.sleep(0.2)
  if time.time()>=DEADLINE:break
  if (D/'STOP').exists():break
  current=D/f'case-{index:04}';current.mkdir();cache=current/'units';cache.mkdir(mode=0o700)
  source,changed,expected,locals_count=program(index);src=current/'main.rf2';src.write_text(source);mut=current/'shifted.rf2';mut.write_text(changed);opt=index%2==0
  clean=current/'clean';cold=current/'cold';warm=current/'warm';shifted=current/'shifted';shiftclean=current/'shift-clean'
  oracle,_=build(src,clean,opt);raw,first=build(src,cold,opt,cache);assert raw==oracle and first['reused']==0,(index,'cold')
  raw,second=build(src,warm,opt,cache);assert raw==oracle and 1<=second['reused']<=2,(index,'warm',second)
  changed_oracle,_=build(mut,shiftclean,opt);raw,third=build(mut,shifted,opt,cache);assert raw==changed_oracle and 1<=third['reused']<=2,(index,'shifted',third)
  observe(clean,expected);observe(warm,expected);observe(shifted,expected)
  rows.append(dict(index=index,optimized=opt,scalarLocals=locals_count,expectedU64=str(expected),sourceSHA256=hashlib.sha256(source.encode()).hexdigest(),mutatedSourceSHA256=hashlib.sha256(changed.encode()).hexdigest(),unsignedSHA256=hashlib.sha256(oracle).hexdigest(),shiftedUnsignedSHA256=hashlib.sha256(changed_oracle).hexdigest(),reused=second['reused'],shiftedReused=third['reused']))
  # Retain sources, unit receipts and hashes; successful executable copies are expendable.
  for out in [clean,cold,warm,shifted,shiftclean]:out.unlink()
  if index%10==0:checkpoint('running')
  if index%50==0:print(json.dumps({'completedPrograms':len(rows),'elapsedSeconds':round(time.time()-started,2)}),flush=True)
 status='complete'if len(rows)==LIMIT else('requested-stop'if(D/'STOP').exists()else'deadline-complete');report=checkpoint(status);report['budgetComplete']=len(rows)==LIMIT;report['requestedStop']=(D/'STOP').exists();(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'status':status,'completedPrograms':len(rows)}),flush=True)
except BaseException as e:
 checkpoint('failed',repr(e));print(json.dumps({'failedCase':str(current),'error':repr(e),'completedPrograms':len(rows)}),flush=True);raise
