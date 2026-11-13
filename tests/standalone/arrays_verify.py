"""Native fixed u64 arrays: types, lifetime restrictions, bounds and app oracle."""
from pathlib import Path
import os,subprocess,tempfile,random,json,hashlib,math
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-arrays'));U=(1<<64)-1
io=(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1]
parse='fn parse(p)\nlet n=0\nlet i=0\nwhile load8(p+i)!=0\nset n=n*10+load8(p+i)-48\nset i=i+1\nend\nreturn n\nend\n'
report={'passed':False,'nativeValueCases':0,'boundsFailures':0,'compileRefusals':0,'lifetimeCases':0,'applicationCases':0,'applicationRefusals':0,'sideEffectCases':0,'modes':['default','opt']}
def build(src,path,opt=False,good=True):
 path.with_suffix('.rf2').write_text(src);p=subprocess.run([C,path.with_suffix('.rf2'),path]+(['--opt']if opt else[]),capture_output=True,timeout=20)
 if good:
  assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',path],check=True,capture_output=True)
 else:assert p.returncode==1 and not path.exists(),(p.returncode,p.stderr)
 return p
def run(path,args=()):return subprocess.run([path,*map(str,args)],capture_output=True,timeout=5)
base='profile RF2_SYSTEM_A64_V1\narray Values(u64, 8)\n'
negatives=[
 'array Empty(u64, 0)\n','array Huge(u64, 4097)\n','array Leading(u64, 08)\n','array Hex(u64, 0x8)\n','array Wrap(u64, 18446744073709551617)\n','array X(u32, 8)\n','array X(u64, n)\n','array X(u64, 8, 9)\n','array Values(u64, 8)\n','record Values(x:u64)\n','array u64(u64, 8)\n']
invalid_bodies=['let a=Values(1)\n','let a=Values()\nset a=Values()\n','let a=Values()\nlet b=a\n','let a=Values()\nreturn a\n','let a=Values()\ndo write(1,a,8)\n','let a=Values()\nreturn a+1\n','let a=Values()\nset a.length=1\n','let a=Values()\nreturn a.missing\n','let a=Values()\nreturn a[0][0]\n','let a=Values()\nreturn a[a]\n','let a=Values()\nset a[0]=a\n','return a[0]\nlet a=Values()\n','set a[0]=1\nlet a=Values()\n','if argc\nlet a=Values()\nend\n','let x=0\nreturn x[0]\n','let a=Values()\nlet b=Other()\ndo accept(b)\n','let a=Values()\ndo raw(a)\n']
with tempfile.TemporaryDirectory(prefix='rf2-arrays-')as tmp:
 d=Path(tmp);rng=random.Random(202611122)
 for opt in [False,True]:
  for cap in [1,2,8,64,128]:
   src='profile RF2_SYSTEM_A64_V1\n'+io+parse+f'array Values(u64, {cap})\n'+'''fn put(a: Values, i, value)
 set a[i]=value
 return a[i]
end
fn main(argc,argv)
 let a=Values()
 let index=parse(load64(argv+8))
 let value=parse(load64(argv+16))
 do put(a,index,value)
 do io_number(a[index])
 do io_print(" ")
 do io_number(a[(index+1)%CAP])
 do io_print(" ")
 do io_number(a.length)
 do io_print("\\n")
 return 0
end
'''.replace('%CAP',f'& {cap-1}') # capacities powers of two; next-slot zero except cap1
   path=d/f'values-{cap}-{opt}';build(src,path,opt)
   for j in range(20):
    index=rng.randrange(cap);value=rng.choice([0,U,1<<63,rng.randrange(1<<64)]);p=run(path,[index,value]);expected=[value,value if cap==1 else 0,cap];assert p.returncode==0 and list(map(int,p.stdout.split()))==expected,(opt,cap,index,p.stdout,expected);report['nativeValueCases']+=1
   for index in [cap,cap+1,U]:
    p=run(path,[index,7]);assert p.returncode==2 and p.stderr==b'RF2 bounds\n' and not p.stdout,(index,p.returncode,p.stderr);report['boundsFailures']+=1
  # Direct reads fail with the same status and cannot expose an adjacent stack cell.
  src=base+parse+"fn main(argc,argv)\nlet a=Values()\nreturn a[parse(load64(argv+8))]\nend\n";path=d/f'read-bounds{opt}';build(src,path,opt)
  for index in [8,9,U]:
   p=run(path,[index]);assert p.returncode==2 and p.stderr==b'RF2 bounds\n' and not p.stdout;report['boundsFailures']+=1
  # Recursive owned arrays are disjoint; typed aliases and same-object calls are allowed.
  src=base+'''fn recurse(n)
 let a=Values()
 set a[0]=n
 let child=0
 if n>0
  set child=recurse(n-1)
 end
 return child+a[0]
end
fn same(a:Values,b:Values)
 set a[0]=9
 return b[0]
end
fn main(argc,argv)
 let a=Values()
 let b=Values()
 do same(a,a)
 return (recurse(30)!=465)|(a[0]!=9)|(b[0]!=0)
end
''';path=d/f'life{opt}';build(src,path,opt);assert run(path).returncode==0;report['lifetimeCases']+=1
  # Historical 255-word allocation remains valid; payload is now separate from scalar slots.
  src='profile RF2_SYSTEM_A64_V1\narray Big(u64,255)\nfn big()\nlet a=Big()\nset a[254]=77\nreturn a[254]\nend\nfn main(argc,argv)\nreturn big()!=77\nend\n';path=d/f'big{opt}';build(src,path,opt);assert run(path).returncode==0;report['lifetimeCases']+=1
  # On a failing write, RHS side effects must not execute.
  src=base+io+'''fn effect()
 do io_print("unexpected")
 return 5
end
fn main(argc,argv)
 let a=Values()
 set a[8]=effect()
 return 0
end
''';path=d/f'effect{opt}';build(src,path,opt);p=run(path);assert p.returncode==2 and not p.stdout and p.stderr==b'RF2 bounds\n';report['sideEffectCases']+=1
  for j,decl in enumerate(negatives):
   src=base+decl+'fn main(argc,argv)\nreturn 0\nend\n';build(src,d/f'decl-{j}-{opt}',opt,False);report['compileRefusals']+=1
  for j,body in enumerate(invalid_bodies):
   src=base+'array Other(u64,8)\nfn accept(a:Values)\nreturn a[0]\nend\nfn raw(p)\nreturn p\nend\nfn main(argc,argv)\n'+body+'return 0\nend\n';build(src,d/f'refuse-{j}-{opt}',opt,False);report['compileRefusals']+=1
  src=base+'array Big(u64,255)\nfn main(argc,argv)\nlet a=Big()\nreturn 0\nend\n';path=d/f'frame-{opt}';build(src,path,opt);assert run(path).returncode==0;report['lifetimeCases']+=1
  # Named scalar slots remain bounded even though array payload no longer consumes them.
  src=base+'fn main(argc,argv)\n'+''.join('let scalar'+str(i)+'=0\n'for i in range(255))+'return 0\nend\n';build(src,d/f'scalar-slots-{opt}',opt,False);report['compileRefusals']+=1
  # Import graph and real latency app. File contents, rather than a synthetic wrapper, are compiled.
  app=d/f'latency-{opt}';p=subprocess.run([C,R/'examples/latency/main.rf2',app]+(['--opt']if opt else[]),capture_output=True);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',app],check=True,capture_output=True)
  for j in range(80):
   values=[rng.choice([0,4294967295,rng.randrange(10000)])for _ in range(rng.choice([1,2,7,32,127,128]))];p=run(app,values);ordered=sorted(values);expected={'count':len(values),'min':min(values),'max':max(values),'sum':sum(values),'median_lower':ordered[(len(values)-1)//2],'p95_nearest_rank':ordered[(len(values)*95+99)//100-1]};assert p.returncode==0 and json.loads(p.stdout)==expected,(p.returncode,p.stdout,expected);report['applicationCases']+=1
  for args in [[],[''],['-1'],['1.5'],['12x'],['4294967296'],['00000000000'],['1']*129,['1\n'],[' 1'],['1e2']]:
   p=run(app,args);assert p.returncode==1 and not p.stdout and p.stderr,(args,p.returncode,p.stdout);report['applicationRefusals']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),compilerSourceSHA256=hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),applicationSourceHashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(R/'examples/latency').rglob('*.rf2')},scope='Fixed nominal u64 arrays in trusted systems profile, finite host tests in default/opt. Not growable vectors, whole-program memory safety, concurrency or Core/MCP effect expansion.')
Path(os.environ.get('RF2_TEST_REPORT',str(R/'docs/ARRAYS-VERIFICATION.json'))).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
