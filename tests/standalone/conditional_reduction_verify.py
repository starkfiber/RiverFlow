"""Conditional periodic reduction: direct iteration, big integers, prior compiler and fallbacks."""
from pathlib import Path
import subprocess,os,random,json,hashlib,tempfile
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-0.12-corrected'));OLD=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/rf2c-0.11-final'));U=(1<<64)-1
io=(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1]
parse='fn parse(p)\nlet n=0\nlet i=0\nwhile load8(p+i)!=0\nset n=n*10+load8(p+i)-48\nset i=i+1\nend\nreturn n\nend\n'
pairs=[(0,0),(0,31),(1,3),(3,31),(31,31),(255,65535),(65535,U>>32),(U>>32,U>>32)];values=[0,7,1<<63,U];configs=[(a,b,k)for a,b in pairs for k in values]
def body(a,b,k,bound='bound',change=0):
 op='<='if change==1 else'<';eq='!='if change==2 else'=='
 return f'let i=start\nlet total=seed\nwhile i{op}{bound}\nif (i&{a}){eq}0\nset total=total+{k}\nelse\nset total=total+(i&{b})\nend\nset i=i+1\n'+('set witness=witness+1\n'if change==3 else'')+'end\ndo io_number(total)\ndo io_print(" ")\ndo io_number(i)\ndo io_print("\\n")\nreturn 0\n'
def build(src,path,compiler=C):
 path.with_suffix('.rf2').write_text(src);p=subprocess.run([compiler,path.with_suffix('.rf2'),path,'--opt'],capture_output=True);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',path],check=True,capture_output=True);return p.stderr.decode()
def run(path,a,b,k,index=0):
 p=subprocess.run([path,str(a),str(b),str(k),str(index)],capture_output=True,timeout=5);assert p.returncode==0,(p.returncode,p.stderr);return tuple(map(int,p.stdout.split()))
def prefix(n,a,b,k):
 P=b+1;Q=a+1;m=(n+Q-1)//Q
 def base(n,p):q,r=divmod(n,p);return q*p*(p-1)//2+r*(r-1)//2
 return base(n,P)+m*k-Q*base(m,P//Q)
report={'passed':False,'smallIterationCases':0,'largeIntegerCases':0,'old11Comparisons':0,'fallbackCases':0,'literalBoundsCases':0,'preservedSpillCases':0}
with tempfile.TemporaryDirectory(prefix='rf2-conditional12-')as tmp:
 d=Path(tmp);funcs=''.join(f'fn reduce{j}(start,bound,seed)\n'+body(*c)+'end\n'for j,c in enumerate(configs));main='fn main(argc,argv)\nlet start=parse(load64(argv+8))\nlet bound=parse(load64(argv+16))\nlet seed=parse(load64(argv+24))\nlet index=parse(load64(argv+32))\n'
 # More caller locals than the selected register set; check preservation across calls.
 main+=''.join(f'let keep{j}={j+9123}\n'for j in range(12))
 main+=''.join(f'if index=={j}\ndo reduce{j}(start,bound,seed)\nend\n'for j in range(len(configs)))
 main+='return '+' | '.join(f'(keep{j}!={j+9123})'for j in range(12))+'\nend\n';src='profile RF2_SYSTEM_A64_V1\n'+io+parse+funcs+main;new=d/'new';old=d/'old';assert 'guarded periodic'in build(src,new);assert 'guarded periodic'not in build(src,old,OLD)
 rng=random.Random(120261112)
 for j,c in enumerate(configs):
  a,b,k=c
  for rep in range(12):
   start=rng.randrange(512);bound=rng.randrange(2049);seed=rng.choice([0,U,U-17,rng.randrange(1<<64)]);expected=((seed+sum(k if (i&a)==0 else i&b for i in range(start,bound)))&U,max(start,bound));assert run(new,start,bound,seed,j)==expected,(c,start,bound,seed,expected);assert run(old,start,bound,seed,j)==expected;report['smallIterationCases']+=1;report['old11Comparisons']+=1;report['preservedSpillCases']+=1
  for start,bound in [(0,U),(U-1,U),((1<<63)+17,U),(U,0)]:
   seed=rng.randrange(1<<64);expected=((seed+(prefix(bound,a,b,k)-prefix(start,a,b,k)if start<bound else 0))&U,max(start,bound));got=run(new,start,bound,seed,j);assert got==expected,(c,start,bound,got,expected);report['largeIntegerCases']+=1
 for j,bound in enumerate([0,1,31,32,33,U]):
  src='profile RF2_SYSTEM_A64_V1\n'+io+parse+'fn main(argc,argv)\nlet start=parse(load64(argv+8))\nlet seed=parse(load64(argv+24))\n'+body(3,31,7,str(bound))+'end\n';path=d/f'literal{j}';assert 'guarded periodic'in build(src,path)
  for start in [0,17,U]:
   expected=((U+(prefix(bound,3,31,7)-prefix(start,3,31,7)if start<bound else 0))&U,max(start,bound));assert run(path,start,0,U)==expected;report['literalBoundsCases']+=1
 for j,(a,b,change)in enumerate([(4,31,0),(3,30,0),(63,31,0),(3,31,1),(3,31,2),(3,31,3)]):
  src='profile RF2_SYSTEM_A64_V1\n'+io+parse+'fn main(argc,argv)\nlet start=parse(load64(argv+8))\nlet bound=parse(load64(argv+16))\nlet seed=parse(load64(argv+24))\nlet witness=0\n'+body(a,b,7,change=change)+'end\n';path=d/f'fallback{j}';assert 'guarded periodic'not in build(src,path)
  for rep in range(12):
   start=rng.randrange(100);bound=rng.randrange(100);seed=rng.randrange(1<<64);end=bound+1 if change==1 else bound;expected=((seed+sum(7 if ((i&a)!=0 if change==2 else(i&a)==0)else i&b for i in range(start,end)))&U,max(start,end));assert run(path,start,bound,seed)==expected;report['fallbackCases']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),sourceSHA256=hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),baselineCompilerSHA256=hashlib.sha256(OLD.read_bytes()).hexdigest(),scope='Exact pure conditional masked sum, power-of-two nested periods through 2^32, unsigned wrapping u64, zero/false entry and final induction state. No arbitrary conditional loop optimization, whole compiler proof or physical hardware result.')
(R/'docs/CONDITIONAL-REDUCTION-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
