"""Explicit post-trial project repair on copies. Original model sources/grades/usage remain intact."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[2];D=Path(sys.argv[1]).resolve();C=R/'artifacts/nested-owned-044-f/build/program';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();results=[]
assert len(json.loads((D/'RESULTS.json').read_text())['trialResults'])==4
patches={
 '1-rf2':('study.flow','       do writer_text(out,",\\"result\\":{\\"isError\\":true,\\"content\\":[{\\"type\\":\\"text\\",\\"text\\":\\"Expected booking_list with explicit empty arguments\\"}]}}\\n")','       do rpc_error(out,"-32602","Unknown tool or invalid arguments")'),
 '4-rf2':('application.flow','     do writer_text(out,",\\"result\\":{\\"isError\\":true,\\"content\\":[{\\"type\\":\\"text\\",\\"text\\":\\"Only booking_list with explicit empty arguments is allowed\\"}]}}\\n")','     do mcp_error(out,"-32602","Unknown tool or invalid arguments")'),
 '2-python':('app.py',"                    result = {'isError':True,'content':[{'type':'text','text':'Only booking_list with explicit empty arguments is supported.'}]}","                    raise ValueError('Unknown tool or invalid arguments')")}
for name,(relative,old,new)in patches.items():
 W=D/name;P=D/'repairs'/name;P.mkdir(parents=True,exist_ok=False)
 for p in W.rglob('*'):
  rel=p.relative_to(W)
  if p.is_file()and p.suffix in('.flow','.rf2','.py','.md','.json')and not any(part in('artifacts','__pycache__')for part in rel.parts)and not p.name.startswith(('GRADE','TRACE')):
   dest=P/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 p=P/relative;s=p.read_text();assert s.count(old)==1,(name,relative);before=sha(p);started=time.monotonic();p.write_text(s.replace(old,new,1))
 if name.endswith('rf2'):
  q=subprocess.run([str(C),str(P/'main.flow'),str(P/'app'),'--opt'],capture_output=True,timeout=30);assert q.returncode==0,q.stderr.decode();subprocess.run(['/usr/bin/codesign','-s','-',str(P/'app')],capture_output=True,check=True)
 out=P/'GRADE-REPAIRED.json';q=subprocess.run([sys.executable,str(D/'grade-reviewed.py'),str(P),str(out)],cwd=R,capture_output=True,timeout=120);assert q.returncode==0,q.stderr.decode();g=json.loads(out.read_text());assert g['allPassed'],g;results.append(dict(attempt=name,source=relative,sourceBeforeSHA256=before,sourceAfterSHA256=sha(p),repair='One-site protocol refusal classification fix; domain/storage and file authority unchanged',executionSeconds=time.monotonic()-started,checks=g['checks'],passed=g['passed'],originalAttemptsUnchanged=True,parentReviewTokens='Not separately metered; no repaired-success total usage comparison',gradeSHA256=sha(out)))
(D/'REPAIRS.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
