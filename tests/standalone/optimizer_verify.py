"""Native guarded reductions, ordinary fallback and register lifetime with independent results."""
from pathlib import Path
import os,json,random,subprocess,tempfile,hashlib
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c'));OLD=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/package/rf2-0.10.0/rf2c'));report={'passed':False,'smallBruteForceCases':0,'largeIntegerCases':0,'fallbackCases':0,'old10Comparisons':0,'guards':[]};masks=[0,1,3,7,15,255,65535,4294967295]
io=(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1]
parse='''fn parse(text)
 let value=0
 let i=0
 while load8(text+i)!=0
 set value=value*10+load8(text+i)-48
 set i=i+1
 end
 return value
end
'''
def body(mask,variant=0):
 op='<='if variant==1 else'<';extra='\n set witness=witness+1'if variant==2 else''
 return 'let i=start\nlet total=acc\nlet witness=0\nwhile i '+op+' bound\nset total=total+(i & '+str(mask)+')\nset i=i+1'+extra+'\nend\ndo io_number(total)\ndo io_print(" ")\ndo io_number(i)\ndo io_print("\\n")\nreturn 0\n'
def build(source,path,compiler):
 src=path.with_suffix('.rf2');src.write_text(source);p=subprocess.run([compiler,src,path,'--opt'],capture_output=True);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',path],check=True,capture_output=True);return p.stderr.decode()
def run(p,start,bound,acc,index):
 r=subprocess.run([p,str(start),str(bound),str(acc),str(index)],capture_output=True,timeout=10);assert r.returncode==0,(r.returncode,r.stderr);return tuple(map(int,r.stdout.split()))
with tempfile.TemporaryDirectory(prefix='rf2-optimizer11-')as tmp:
 d=Path(tmp);functions=''.join('fn reduce'+str(i)+'(start,bound,acc)\n'+body(mask)+'end\n'for i,mask in enumerate(masks))
 main='fn main(argc,argv)\nlet start=parse(load64(argv+8))\nlet bound=parse(load64(argv+16))\nlet acc=parse(load64(argv+24))\nlet index=parse(load64(argv+32))\nlet preserved=123456789\n'
 for i in range(len(masks)):main+='if index=='+str(i)+'\ndo reduce'+str(i)+'(start,bound,acc)\nend\n'
 main+='return preserved != 123456789\nend\n';source='profile RF2_SYSTEM_A64_V1\n'+io+parse+functions+main
 new=d/'new';old=d/'old';trace=build(source,new,C);build(source,old,OLD);assert 'guarded periodic sum reduction applied'in trace;report['guards'].append('eligible family selected')
 rng=random.Random(2026111211);MASK=(1<<64)-1
 for i in range(240):
  index=i%len(masks);start=rng.randrange(0,513);bound=rng.randrange(0,2049);acc=rng.choice([0,1,MASK,MASK-17,rng.randrange(1<<64)]);expected=((acc+sum(x&masks[index]for x in range(start,bound)))&MASK,max(start,bound));got=run(new,start,bound,acc,index);assert got==expected,(start,bound,acc,index,got,expected);assert run(old,start,bound,acc,index)==expected;report['smallBruteForceCases']+=1;report['old10Comparisons']+=1
 def prefix(n,m):
  p=m+1;q,r=divmod(n,p);return q*(p*(p-1)//2)+r*(r-1)//2
 for i in range(80):
  index=i%len(masks);start=rng.choice([0,1,1<<32,(1<<63)+11,MASK-1]);bound=rng.choice([0,1,10**12,1<<63,MASK]);acc=rng.randrange(1<<64);expected=((acc+(prefix(bound,masks[index])-prefix(start,masks[index])if start<bound else 0))&MASK,max(start,bound));assert run(new,start,bound,acc,index)==expected;report['largeIntegerCases']+=1
 for variant,mask in [(0,5),(1,255),(2,255)]:
  source='profile RF2_SYSTEM_A64_V1\n'+io+parse+'fn reduce0(start,bound,acc)\n'+body(mask,variant)+'end\nfn main(argc,argv)\nreturn reduce0(parse(load64(argv+8)),parse(load64(argv+16)),parse(load64(argv+24)))\nend\n';new=d/f'fallback{variant}';old=d/f'oldfallback{variant}';assert 'guarded periodic'not in build(source,new,C);build(source,old,OLD)
  for j in range(20):
   a=rng.randrange(100);b=rng.randrange(100);v=rng.randrange(1<<64);got=run(new,a,b,v,0);assert got==run(old,a,b,v,0);end=b+1 if variant==1 else b;assert got==((v+sum(x&mask for x in range(a,end)))&MASK,max(a,end));report['fallbackCases']+=1;report['old10Comparisons']+=1
 report['guards']+=['non-power-of-two mask retained loop','inclusive comparison retained loop','extra body effect retained loop']
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),scope='Exact serial unsigned-u64 recurrence; small cases brute-force, large cases arbitrary-precision formula. No full compiler proof, arbitrary loop optimisation or hardware result.');(R/'docs/OPTIMIZER-0.11-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
