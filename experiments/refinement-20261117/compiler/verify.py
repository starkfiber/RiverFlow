"""Exact source-derived diagnostic controls; no provider and no changed syntax."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,tempfile
H='profile RF2_SYSTEM_A64_V1\n'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);slot=Path(tempfile.mkdtemp(prefix='rf2-hints-tests-',dir=os.environ['TMPDIR']));rows=[]
 cases=[('else-if','fn main(argc,argv)\n if argc\n  return 0\n else if argc\n  return 1\n end\nend\n','RF2E_ELSE_IF','expected newline','nested if'),('bare-try-IO','result IO(u64,u64)\nfn task():IO\n return ok(0)\nend\nfn work():IO\n try task()\n return ok(0)\nend\nfn main(argc,argv)\n return 0\nend\n','RF2E_TRY_STATEMENT','unsupported statement','do try'),('bare-try-scalar','fn main(argc,argv)\n try missing()\n return 0\nend\n','RF2E_TRY_STATEMENT','unsupported statement','Outside IO'),('ordinary-unsupported','fn main(argc,argv)\n nonsense\n return 0\nend\n','RF2E_COMPILE','unsupported statement',''),('ordinary-newline','fn main(argc,argv)\n let x=0 return 0\nend\n','RF2E_COMPILE','expected newline','')]
 def add(label,passed,details):
  rows.append({'case':label,'passed':bool(passed),'details':details});(d/'RESULTS.json').write_text(json.dumps({'rows':rows,'allPassed':all(x['passed']for x in rows),'candidateSHA256':sha(a.compiler)},indent=2)+'\n');assert passed,label
 for opt in [False,True]:
  for name,body,code,message,hint in cases:
   source=d/(name+'.flow');source.write_text(H+body);binary=slot/(name+str(opt));args=[str(source),str(binary),'--compact',*(['--opt']if opt else[])]
   q=subprocess.run([str(a.compiler),*args,'--diagnostic-json'],capture_output=True,timeout=10);v=json.loads(q.stderr);add(name+' structured '+str(opt),q.returncode==1 and not q.stdout and not binary.exists()and v['code']==code and v['message']==message and (hint in v['hint']if hint else v['hint']==''),v)
   q=subprocess.run([str(a.compiler),*args],capture_output=True,timeout=10);add(name+' human '+str(opt),q.returncode==1 and message.encode()in q.stderr and(not hint or b'hint:'in q.stderr),q.stderr.decode(errors='replace'))
 # Corrected spelling compiles and produces byte-identical app image to baseline.
 good=[('nested','fn main(argc,argv)\n if argc\n  return 7\n else\n  if argc\n   return 8\n  end\n end\n return 9\nend\n',7),('do-try','result IO(u64,u64)\nfn task():IO\n return ok(0)\nend\nfn work():IO\n do try task()\n return ok(7)\nend\nfn main(argc,argv)\n handle work()\n ok done\n  return done\n err problem\n  return 3\n end\n return 4\nend\n',7)]
 for opt in [False,True]:
  for name,body,want in good:
   source=d/(name+'.flow');source.write_text(H+body);outputs=[]
   for label,c in [('old',a.baseline),('new',a.compiler)]:
    binary=slot/(name+label+str(opt));q=subprocess.run([str(c),str(source),str(binary),'--compact',*(['--opt']if opt else[]),'--diagnostic-json'],capture_output=True,timeout=10);add(name+' builds '+label+str(opt),q.returncode==0,q.stderr.decode(errors='replace'));outputs.append(binary.read_bytes());subprocess.run(['codesign','-s','-',str(binary)],check=True,capture_output=True);q=subprocess.run([str(binary)],capture_output=True,timeout=5);add(name+' executes '+label+str(opt),q.returncode==want,q.returncode)
   add(name+' exact app bytes '+str(opt),outputs[0]==outputs[1],[hashlib.sha256(x).hexdigest()for x in outputs])
 print(json.dumps({'passed':len(rows),'allPassed':True}))
if __name__=='__main__':main()
