"""Generated native RF2 checks. Synthetic programs/workloads, not human users."""
from pathlib import Path
import bisect,hashlib,json,os,random,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2];HOME=Path(os.environ['RF2_TEST_HOME']).resolve();CAND=Path(os.environ['RF2_NESTED_COMPILER']).resolve();OUT=Path(tempfile.mkdtemp(prefix='platform-sprint-',dir=ROOT/'artifacts'));rows=[];rng=random.Random(400151126)
def call(args,**kw):return subprocess.run(list(map(str,args)),capture_output=True,timeout=20,**kw)
def check(name,ok,detail=None):
 rows.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:
  (OUT/'FAILED.json').write_text(json.dumps(rows[-1],indent=2));raise AssertionError((name,detail))
def build(c,src,path,opt):
 q=call([c,src,path,*(['--opt'] if opt else [])]);check('compile '+path.name,q.returncode==0,(q.stdout+q.stderr).decode()[:500]);q=call(['/usr/bin/codesign','-s','-',path]);assert q.returncode==0
for opt in (False,True):
 exe=OUT/('lookup-'+str(opt));build(HOME/'rf2c',ROOT/'examples/collection-tools/lookup.flow',exe,opt)
 for i in range(1000):
  values=[rng.choice([0,1,7,99,(1<<64)-1,rng.randrange(10000)]) for _ in range(rng.randrange(160))];needle=rng.choice([0,1,7,99,(1<<64)-1,rng.randrange(10000)]);ordered=sorted(values);expected=dict(first=bisect.bisect_left(ordered,needle),after=bisect.bisect_right(ordered,needle));expected['matches']=expected['after']-expected['first']
  q=call([exe,str(needle)],input=','.join(map(str,values)).encode());check('lookup '+str(opt)+' '+str(i),q.returncode==0 and json.loads(q.stdout)==expected,dict(query=needle,input=values,expected=expected,stderr=q.stderr.decode()[:100]))
 for bad in (b'1,,2',b'01',b'-1',b'18446744073709551616',b'1,'):
  q=call([exe,'1'],input=bad);check('malformed '+str(opt)+' '+repr(bad),q.returncode!=0)
 print('collection mode',opt,'passed',flush=True)
# Each unique program is compiled in both modes and executed with its own oracle.
for i in range(256):
 depth=1+i%6;left=rng.randrange(100000);right=rng.randrange(100000);value=rng.randrange(100000);alias=i%3==0
 src='profile RF2_SYSTEM_A64_V1\nrecord Leaf(value:u64)\nrecord Pair(left:Leaf,right:Leaf)\n'
 for n in range(depth):src+=f'record Layer{n}(child:{"Pair" if n==0 else "Layer"+str(n-1)})\n'
 src+='fn update(n)\n let p=buffer("call_counter",8)\n do store64(p,load64(p)+1)\n return n\nend\nfn main(argc,argv)\n'
 src+=f' let a=Leaf({left})\n let b=Leaf({right})\n let pair=Pair(a,{"a" if alias else "b"})\n'
 for n in range(depth):src+=f' let layer{n}=Layer{n}({"pair" if n==0 else "layer"+str(n-1)})\n'
 path='layer'+str(depth-1)+'.child'*depth
 src+=f' set {path}.left.value=update({value})\n if ({path}.left.value!={value})|({path}.right.value!={value if alias else right})|(a.value!={value})|(b.value!={right})|(load64(buffer("call_counter",8))!=1)\n  return 1\n end\n return 0\nend\n'
 source=OUT/f'nested-{i}.flow';source.write_text(src)
 for opt in (False,True):
  exe=OUT/(f'nested-{i}-{opt}');build(CAND,source,exe,opt);q=call([exe]);check('nested execution '+str(i)+' '+str(opt),q.returncode==0,q.stderr.decode()[:100])
 if i%32==0:print('nested programs',i,'passed',flush=True)
base='profile RF2_SYSTEM_A64_V1\nrecord Leaf(value:u64)\nrecord Pair(child:Leaf)\n'
invalid={
 'scalar-as-child':base+'fn main(argc,argv)\n let p=Pair(9)\n return 0\nend\n',
 'replace-child':base+'fn main(argc,argv)\n let l=Leaf(1)\n let p=Pair(l)\n set p.child=l\n return 0\nend\n',
 'scalar-chain':base+'fn main(argc,argv)\n let l=Leaf(1)\n let p=Pair(l)\n set p.child.value.bad=2\n return 0\nend\n',
 'missing-field':base+'fn main(argc,argv)\n let l=Leaf(1)\n let p=Pair(l)\n set p.child.missing=2\n return 0\nend\n',
 'return-borrow':base+'result Escape(Pair,u64)\nfn main(argc,argv)\n return 0\nend\n',
 'owned-collection-child':'profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ncollection Values(IO,10)\nrecord Bad(v:Values)\nfn main(argc,argv)\n return 0\nend\n'}
for name,src in invalid.items():
 p=OUT/(name+'.flow');p.write_text(src)
 for opt in (False,True):
  q=call([CAND,p,OUT/(name+str(opt)),*(['--opt'] if opt else [])]);check('refusal '+name+str(opt),q.returncode!=0,(q.stdout+q.stderr).decode()[:400])
report={'baseline':call(['git','rev-parse','HEAD'],cwd=ROOT).stdout.decode().strip(),'seed':400151126,'compilerSha256':hashlib.sha256((HOME/'rf2c').read_bytes()).hexdigest(),'candidateSha256':hashlib.sha256(CAND.read_bytes()).hexdigest(),'collectionWorkloads':2000,'uniqueNestedPrograms':256,'nestedExecutions':512,'checks':rows,'scope':'Generated local Mac native workloads and compiler cases, not thousands of developers, platform qualification, independent model agents, security certification or speed comparison.'}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(rows),'report':str(OUT/'report.json')}),flush=True)
