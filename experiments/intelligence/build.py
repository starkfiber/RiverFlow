"""Explicit local candidate build; requires exact qualified 0.50 compiler, no download."""
from pathlib import Path
import hashlib, json, platform, subprocess, sys, time
from prepare import prepare
BASE_BINARY='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def build(compiler,destination):
 compiler=Path(compiler).resolve(strict=True); destination=Path(destination).resolve()
 if sys.platform!='darwin' or platform.machine()!='arm64': raise ValueError('macOS ARM64 required')
 if sha(compiler)!=BASE_BINARY: raise ValueError('Select the exact qualified 0.50 compiler; no fallback')
 if destination.exists(): raise ValueError('Use a new output directory')
 destination.mkdir(parents=True)
 record=dict(schema='rf2.import-guard.build.v1',status='building',baselineCompilerSHA256=sha(compiler),flags=['--compact','--opt'],steps=[],stableReleaseChanged=False)
 def save(): (destination/'BUILD.json').write_text(json.dumps(record,indent=2)+'\n')
 def run(label,args):
  start=time.monotonic()
  try: q=subprocess.run(list(map(str,args)),capture_output=True,timeout=60)
  except subprocess.TimeoutExpired as e:
   (destination/(label+'.stdout')).write_bytes(e.stdout or b'');(destination/(label+'.stderr')).write_bytes(e.stderr or b'')
   record['steps'].append(dict(label=label,exit='timeout',seconds=time.monotonic()-start));save();raise
  (destination/(label+'.stdout')).write_bytes(q.stdout);(destination/(label+'.stderr')).write_bytes(q.stderr)
  record['steps'].append(dict(label=label,exit=q.returncode,seconds=time.monotonic()-start));save()
  if q.returncode: raise RuntimeError('Failed '+label+'; retained logs')
 try:
  source=prepare(destination/'source')/'compiler.flow'; program=destination/'program'
  record['sourceSHA256']=sha(source);save()
  run('compile',[compiler,source,program,'--compact','--opt'])
  run('sign',['/usr/bin/codesign','-s','-',program])
  run('verify-signature',['/usr/bin/codesign','--verify',program])
  (destination/'self').mkdir()
  other=destination/'self/program'
  run('self-compile',[program,source,other,'--compact','--opt'])
  run('self-sign',['/usr/bin/codesign','-s','-',other])
  record['programSHA256']=sha(program);record['selfSHA256']=sha(other)
  if record['programSHA256']!=record['selfSHA256']: raise ValueError('Signed self-generation differs')
  record.update(status='passed',selfGenerationMatched=True);save();return destination
 except BaseException as e:
  record.update(status='failed',failure=type(e).__name__+': '+str(e));save();raise
if __name__=='__main__':
 if len(sys.argv)!=3: raise SystemExit('build.py QUALIFIED-050-COMPILER NEW-DIRECTORY')
 print(build(sys.argv[1],sys.argv[2]))
