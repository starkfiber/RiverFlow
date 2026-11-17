"""Build an isolated diagnostics compiler; source/logs persistent, images disposable."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,tempfile,time
PIN='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert sha(a.compiler)==PIN;assert '/Volumes/Mac Work Cache/'in os.environ.get('TMPDIR','')
 d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);slot=Path(tempfile.mkdtemp(prefix='rf2-hints-',dir=os.environ['TMPDIR']));binary=slot/'program';(slot/'self').mkdir();other=slot/'self/program';rows=[]
 r={'schema':'rf2.hints-build.v1','source':str(a.source.resolve()),'sourceSHA256':sha(a.source),'baselineCompilerSHA256':PIN,'candidate':str(binary),'steps':rows,'stableChanged':False}
 def save():(d/'BUILD.json').write_text(json.dumps(r,indent=2)+'\n')
 def run(label,args):
  t=time.monotonic();q=subprocess.run(list(map(str,args)),capture_output=True,timeout=60);(d/(label+'.stdout')).write_bytes(q.stdout);(d/(label+'.stderr')).write_bytes(q.stderr);rows.append({'label':label,'command':list(map(str,args)),'exit':q.returncode,'seconds':time.monotonic()-t});save();assert q.returncode==0,(label,q.stderr.decode(errors='replace'))
 run('build',[a.compiler,a.source,binary,'--compact','--opt','--diagnostic-json']);run('sign',['codesign','-s','-',binary]);run('self',[binary,a.source,other,'--compact','--opt','--diagnostic-json']);run('self-sign',['codesign','-s','-',other]);r['candidateSHA256']=sha(binary);r['selfSHA256']=sha(other);r['selfGenerationMatched']=sha(binary)==sha(other);save();assert r['selfGenerationMatched'];r['allPassed']=True;save();print(json.dumps(r))
if __name__=='__main__':main()
