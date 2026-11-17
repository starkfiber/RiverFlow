"""Owned native fixtures; explicit baseline/candidate; bounded FIFO and byte oracles."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(baseline,candidate,destination):
 B,C=Path(baseline).resolve(strict=True),Path(candidate).resolve(strict=True);D=Path(destination).resolve()
 if D.exists():raise ValueError('Use a new evidence directory')
 D.mkdir(parents=True);rows=[]
 def record(name,good,detail):
  rows.append(dict(case=name,passed=bool(good),detail=detail));save()
  if not good:raise AssertionError((name,detail))
 def save():
  (D/'RESULTS.json').write_text(json.dumps(dict(schema='rf2.import-liveness.v1',baselineSHA256=sha(B),candidateSHA256=sha(C),controllerSHA256=sha(__file__),checks=rows,passed=bool(rows)and all(x['passed']for x in rows)),indent=2)+'\n')
 def run(binary,source,out,opt=False,diagnostic=False):
  command=[str(binary),str(source),str(out),'--compact']+(['--opt']if opt else[])+(['--diagnostic-json']if diagnostic else[])
  t=time.monotonic()
  try:
   q=subprocess.run(command,capture_output=True,timeout=1)
   return dict(timeout=False,seconds=time.monotonic()-t,exit=q.returncode,stdout=q.stdout.decode(errors='replace'),stderr=q.stderr.decode(errors='replace'))
  except subprocess.TimeoutExpired:return dict(timeout=True,seconds=time.monotonic()-t,exit=None,note='Only owned child killed at controller deadline')
 for opt in(False,True):
  for kind in('regular','nested','fifo','directory','leaf-symlink','oversized'):
   folder=D/(kind+str(opt));folder.mkdir();name='lib/helper.flow'if kind=='nested'else'helper.flow';lib=folder/name;lib.parent.mkdir(exist_ok=True)
   module='module helper\nfn helper()\n return 42\nend\n'
   if kind=='fifo':os.mkfifo(lib)
   elif kind=='directory':lib.mkdir()
   elif kind=='leaf-symlink':(folder/'real.flow').write_text(module);lib.symlink_to(folder/'real.flow')
   else:lib.write_text(module+('#'+'x'*524288 if kind=='oversized'else''))
   source=folder/'main.flow';source.write_text('profile RF2_SYSTEM_A64_V1\nuse "'+name+'"\nfn main(argc,argv)\n return helper()\nend\n');out=folder/'program'
   q=run(C,source,out,opt);good=kind in('regular','nested')
   record(kind+' candidate '+str(opt),not q['timeout'] and(q['exit']==0)==good and(out.exists()==good),q)
   if good:
    other=folder/'baseline';old=run(B,source,other,opt)
    record(kind+' byte equivalence '+str(opt),old['exit']==0 and other.read_bytes()==out.read_bytes(),old)
    subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
    result=subprocess.run([out],capture_output=True,timeout=1)
    record(kind+' execution '+str(opt),result.returncode==42,dict(exit=result.returncode))
   elif kind=='fifo':
    old=run(B,source,folder/'old',opt);record('baseline FIFO reproduction '+str(opt),old['timeout'] and not(folder/'old').exists(),old)
    q=run(C,source,folder/'json-output',opt,True)
    try:event=json.loads(q.get('stderr',''))
    except ValueError:event={}
    record('FIFO JSON diagnostic '+str(opt),not q['timeout']and q['exit']==1 and event.get('schema')=='rf2.diagnostic.v1'and'regular file'in event.get('message',''),q)
 return D
if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('import_verify.py BASELINE CANDIDATE NEW-DIRECTORY')
 print(verify(*sys.argv[1:]))
