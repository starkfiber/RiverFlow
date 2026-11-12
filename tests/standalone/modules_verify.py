"""Execute records/modules and compare observed behavior with independent expectations."""
from pathlib import Path
import subprocess,tempfile,json,random,hashlib,os,sys
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c'));OLD=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/package/rf2-0.9.0/rf2c'));report={'passed':False,'recordExecutions':0,'recordRefusals':0,'moduleRefusals':0,'workloadCases':0,'workloadRefusals':0,'old09Comparisons':0,'optimizedComparisons':0}
def compile(src,out,opt=False,good=True):
 p=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True,timeout=30,env={'PATH':'/nonexistent'})
 if good:
  assert p.returncode==0,(src,p.stderr);subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
 else:assert p.returncode!=0 and not out.exists(),(src,p.stderr)
 return p
with tempfile.TemporaryDirectory(prefix='rf2-modules10-')as tmp:
 d=Path(tmp);rng=random.Random(2026111210)
 pre='profile RF2_SYSTEM_A64_V1\nrecord Pair(left: u64, right: u64)\n'
 for i in range(30):
  a=rng.randrange(2**32);b=rng.randrange(2**32);source=pre+'fn score(p: Pair)\n set p.left = p.left + p.right\n return p.left\nend\nfn main(argc, argv)\n let p = Pair('+str(a)+','+str(b)+')\n let got = score(p)\n return (got == '+str(a+b)+') & (p.left == got)\nend\n';src=d/f'r{i}.rf2';src.write_text(source)
  for opt in [False,True]:
   out=d/f'r{i}-{opt}';compile(src,out,opt);assert subprocess.run([out]).returncode==1;report['recordExecutions']+=1
 invalid=[
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n return p.missing\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1)\n return 0\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2,3)\n return 0\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n return p+1\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n return 1+p\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n return p\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n let q = p\n return 0\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n do write(1,p,16)\n return 0\nend\n',
 pre+'fn f(p: Pair)\n return p.left\nend\nfn main(argc,argv)\n return f(0)\nend\n',
 pre+'record Other(left: u64, right: u64)\nfn f(p: Pair)\n return p.left\nend\nfn main(argc,argv)\n let o = Other(1,2)\n return f(o)\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n let q = Pair(p,2)\n return 0\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n set p.left = p\n return 0\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n set p = Pair(3,4)\n return 0\nend\n',
 pre+'fn main(argc,argv)\n return p.left\n let p = Pair(1,2)\nend\n',
 pre+'fn main(argc,argv)\n if argc\n let p = Pair(1,2)\n end\n return 0\nend\n',
 pre+'fn main(argc: Pair,argv)\n return 0\nend\n',
 'profile RF2_SYSTEM_A64_V1\nrecord P(x: u64,x: u64)\nfn main(a,b)\nreturn 0\nend\n',
 'profile RF2_SYSTEM_A64_V1\nrecord P(x: bool)\nfn main(a,b)\nreturn 0\nend\n',
 'profile RF2_SYSTEM_A64_V1\nrecord P()\nfn main(a,b)\nreturn 0\nend\n',
 'profile RF2_SYSTEM_A64_V1\nrecord buffer(x: u64)\nfn main(a,b)\nreturn 0\nend\n',
 pre+'fn main(argc,argv)\n let p = Pair(1,2)\n if p\n return 1\n end\n return 0\nend\n',
 pre+'fn f(p: Pair)\n set p = Pair(1,2)\n return 0\nend\nfn main(a,b)\nreturn 0\nend\n',
 ]
 for i,s in enumerate(invalid):
  src=d/f'bad{i}.rf2';src.write_text(s)
  for opt in [False,True]:compile(src,d/f'bad{i}-{opt}',opt,False);report['recordRefusals']+=1
 # Same legacy semantics with default and optimized new compiler and frozen 0.9.
 ops=['+','-','*','&','|','^','<<','>>','//','==','!=','<','<=','>','>=']
 for i in range(75):
  a=rng.randrange(100000);b=rng.randrange(0,65);op=ops[i%len(ops)];expr=f'({a} {op} {b})';expr+=' + helper(3)'if i%2 else''
  src=d/f'legacy{i}.rf2';src.write_text('profile RF2_SYSTEM_A64_V1\nfn helper(a)\n return a*7\nend\nfn main(argc,argv)\n return '+expr+'\nend\n');old=d/f'old{i}';subprocess.run([OLD,src,old],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',old],check=True,capture_output=True);expected=subprocess.run([old]).returncode
  for opt in [False,True]:
   out=d/f'new{i}-{opt}';compile(src,out,opt);assert subprocess.run([out]).returncode==expected,(i,opt);report['old09Comparisons']+=1
   if opt:report['optimizedComparisons']+=1
 # Import DAG, duplicate dependency, cycle, paths, header/declaration and count guards.
 root=d/'project';root.mkdir();(root/'lib').mkdir();entry=root/'main.rf2';lib=root/'lib/a.rf2';other=root/'lib/b.rf2'
 base='profile RF2_SYSTEM_A64_V1\nuse "lib/a.rf2"\nfn main(a,b)\n return value()\nend\n';entry.write_text(base);lib.write_text('module a\nuse "lib/b.rf2"\nfn value()\nreturn deeper()\nend\n');other.write_text('module b\nfn deeper()\nreturn 17\nend\n');compile(entry,root/'good');assert subprocess.run([root/'good']).returncode==17
 entry.write_text(base.replace('fn main','use "lib/b.rf2"\nfn main'));compile(entry,root/'dedup');assert subprocess.run([root/'dedup']).returncode==17
 cases=[('cycle','module a\nuse "lib/b.rf2"\n', 'module b\nuse "lib/a.rf2"\n'),('missingheader','fn value()\nreturn 1\nend\n','module b\n'),('lateimport','module a\nfn value()\nreturn 1\nend\nuse "lib/b.rf2"\n','module b\n'),('duplicatefn','module a\nuse "lib/b.rf2"\nfn value()\nreturn 1\nend\n','module b\nfn value()\nreturn 2\nend\n')]
 for name,a,b in cases:entry.write_text(base);lib.write_text(a);other.write_text(b);compile(entry,root/name,good=False);report['moduleRefusals']+=1
 for i,path in enumerate(['../a.rf2','/tmp/a.rf2','lib//a.rf2','./lib/a.rf2','lib/../a.rf2','lib/a.txt','lib/missing.rf2','lib/a.rf2x']):
  entry.write_text(base.replace('lib/a.rf2',path));compile(entry,root/f'path{i}',good=False);report['moduleRefusals']+=1
 lib.write_text('module a\nfn value()\nreturn 1\nend\n');(root/'lib/link.rf2').symlink_to(lib);entry.write_text(base.replace('lib/a.rf2','lib/link.rf2'));compile(entry,root/'symlink',good=False);report['moduleRefusals']+=1
 # Complete useful CSV workload analyser, independently computed expectations.
 app=d/'workload';compile(R/'examples/workload/main.rf2',app,True)
 for i in range(60):
  rows=[(k+1,rng.randrange(1,100000),rng.randrange(1,1000000))for k in range([0,1,3,20,1000][i%5])];src=d/f'work{i}.csv';sep='\r\n'if i%2 else'\n';src.write_bytes(sep.join(','.join(map(str,x))for x in rows).encode()+(sep.encode()if rows and i%3 else b''));elapsed=0;late=0
  for _,ticks,deadline in rows:elapsed+=ticks;late+=elapsed>deadline
  got=subprocess.run([app,src],capture_output=True);assert got.returncode==0,got.stderr;assert json.loads(got.stdout)=={'policy':'input-order','jobs':len(rows),'late':late,'elapsed_ticks':elapsed,'peak_job_ticks':max([0]+[x[1]for x in rows])};report['workloadCases']+=1
 bad=[b'1,0,2\n',b'1,2,0\n',b'0,1,2\n',b'1,2\n',b'1,2,3,4\n',b'01,2,3\n',b'1,-2,3\n',b'1,4294967296,3\n',b'1,2,3\r',b'1,2,3\n\n',b'1,2,3\x00',b'1,1,2\n'*1001,b'X'*65537]
 for i,data in enumerate(bad):
  src=d/f'invalid{i}.csv';src.write_bytes(data);got=subprocess.run([app,src],capture_output=True);assert got.returncode==1 and not got.stdout,(i,got.stdout);report['workloadRefusals']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),scope='Bounded local source imports, nominal u64 records and trusted CSV analyser. No independent memory-safety audit or universal language compatibility claim.');(R/'docs/MODULES-TYPES-0.10-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
