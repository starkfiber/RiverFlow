"""Replay independently authored semantic probes from a hash-pinned fixture set."""
from pathlib import Path
import tempfile,subprocess,json,hashlib,os
R=Path(__file__).resolve().parents[2];D=R/'tests/standalone/fixtures/results-views-critic';C=Path(os.environ['RF2_TEST_COMPILER']);manifest=json.loads((D/'manifest.json').read_text());rows=[]
with tempfile.TemporaryDirectory(prefix='rf2-review-')as tmp:
 for case in manifest['cases']:
  src=D/case['source'];assert hashlib.sha256(src.read_bytes()).hexdigest()==case['sha256']
  for opt in [False,True]:
   out=Path(tmp)/(case['name']+str(opt));p=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True,timeout=20)
   if case['compile']:
    assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);q=subprocess.run([out],input=b'',capture_output=True,timeout=5);assert q.returncode==case['runExit'],(case,q.returncode,q.stderr)
   else:assert p.returncode==1 and not out.exists(),case
   rows.append({'case':case['name'],'optimized':opt,'passed':True})
v={'passed':True,'cases':rows,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'scope':'44 finite default/optimized probes from independently authored reviewed fixtures; no security certification or formal ownership proof.'};(R/'docs/RESULTS-VIEWS-CRITIC-VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n');print({'passed':True,'checks':len(rows)})
