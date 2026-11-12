"""Adversarial expression aliasing, calls, spill slots, loops and recursion."""
from pathlib import Path
import subprocess,tempfile,random,json,os,hashlib
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c'));OLD=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/package/rf2-0.10.0/rf2c'));io=(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1];M=(1<<64)-1
parse='fn parse(p)\nlet n=0\nlet i=0\nwhile load8(p+i)!=0\nset n=n*10+load8(p+i)-48\nset i=i+1\nend\nreturn n\nend\n'
helpers='fn plus(x)\nreturn x+1\nend\nfn recur(n,x)\nif n==0\nreturn x\nend\nlet before=x\nlet inner=recur(n-1,x+1)\nreturn inner+before\nend\n'
cases=[('set x=((x^y)*33+17)&4294967295\nreturn x',lambda x,y:((x^y)*33+17)&4294967295),('set x=(x+1)+x\nreturn x',lambda x,y:(x*2+1)&M),('set x=y+x\nreturn x',lambda x,y:(x+y)&M),('set x=-x+3\nreturn x',lambda x,y:(3-x)&M),('set x=x+plus(y)\nreturn x',lambda x,y:(x+y+1)&M),('set x=(x<y)+3\nreturn x',lambda x,y:int(x<y)+3),('let a=1\nlet b=2\nlet c=3\nlet d=4\nlet e=5\nlet f=6\nlet spilled=x\nset spilled=((spilled^y)*33+17)&4294967295\nreturn spilled+a+b+c+d+e+f',lambda x,y:((((x^y)*33+17)&4294967295)+21)&M),('let total=0\nlet i=0\nwhile i<(x&15)\nlet j=0\nwhile j<(y&15)\nset total=total+1\nset j=j+1\nend\nset i=i+1\nend\nreturn total',lambda x,y:(x&15)*(y&15)),('return recur(x&7,y)',lambda x,y:sum((y+i)&M for i in range((x&7)+1))&M)]
functions=''.join('fn f'+str(i)+'(x,y)\n'+body+'\nend\n'for i,(body,_)in enumerate(cases));main='fn main(argc,argv)\nlet x=parse(load64(argv+8))\nlet y=parse(load64(argv+16))\nlet index=parse(load64(argv+24))\nlet preserved=99887766\n'
for i in range(len(cases)):main+=f'if index=={i}\ndo io_number(f{i}(x,y))\ndo io_print("\\n")\nend\n'
main+='return preserved != 99887766\nend\n';report={'passed':False,'oracleCases':0,'old10Comparisons':0,'conditionSideEffectCases':0}
def build(src,out,c):
 p=subprocess.run([c,src,out,'--opt'],capture_output=True);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
with tempfile.TemporaryDirectory(prefix='rf2-control11-')as tmp:
 d=Path(tmp);src=d/'source.rf2';src.write_text('profile RF2_SYSTEM_A64_V1\n'+io+parse+helpers+functions+main);old=d/'old';new=d/'new';build(src,old,OLD);build(src,new,C);rng=random.Random(20261112011)
 for i in range(180):
  x=rng.choice([0,1,M,M-1,rng.randrange(1<<64)]);y=rng.choice([0,1,M,rng.randrange(1<<64)]);index=i%len(cases);e=cases[index][1](x,y)
  for p in [old,new]:
   q=subprocess.run([p,str(x),str(y),str(index)],capture_output=True,timeout=5);assert q.returncode==0 and int(q.stdout)==e,(index,x,y,e,q.stdout,q.stderr)
  report['oracleCases']+=1;report['old10Comparisons']+=1
 # A condition call must execute once on entry and once per completed iteration.
 src=d/'effects.rf2';src.write_text('profile RF2_SYSTEM_A64_V1\n'+io+parse+'fn consume()\nlet p=buffer("counter",8)\nlet n=load64(p)\ndo store64(p,n+1)\nreturn n\nend\nfn main(argc,argv)\nlet bound=parse(load64(argv+8))\nlet total=0\nwhile consume()<bound\nset total=total+3\nend\ndo io_number(total)\ndo io_print(" ")\ndo io_number(load64(buffer("counter",8)))\ndo io_print("\\n")\nreturn 0\nend\n');old=d/'old-effects';new=d/'new-effects';build(src,old,OLD);build(src,new,C)
 for n in [0,1,2,7,1000]:
  for p in [old,new]:
   q=subprocess.run([p,str(n)],capture_output=True,timeout=5);assert q.returncode==0 and tuple(map(int,q.stdout.split()))==(n*3,n+1),(n,q.stdout)
  report['conditionSideEffectCases']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),scope='Specific alias/call/spill/control-flow/recursive lifetime cases with integer expectations. Not a whole-program correctness proof.');(R/'docs/CONTROL-OPTIMIZER-0.11-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
