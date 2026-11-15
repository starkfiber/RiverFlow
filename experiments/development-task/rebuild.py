"""Reconstruct a published trial into a NEW directory from pinned local sources; build never runs it."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
S=Path(__file__).resolve().parent;R=S.parents[1];a=argparse.ArgumentParser();a.add_argument('sample',choices=['1-rf2','2-python','3-python','4-rf2']);a.add_argument('new_directory');a.add_argument('--compiler');a.add_argument('--repair',action='store_true');args=a.parse_args();index=json.loads((S/'samples/INDEX.json').read_text());info=index['samples'][args.sample];W=Path(args.new_directory).resolve();W.mkdir(parents=True,exist_ok=False);P=S/'samples'/args.sample;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in info['files'].items():
 assert not Path(name).is_absolute() and '..'not in Path(name).parts
 assert sha(P/name)==h
 (W/name).parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(P/name,W/name)
 if name.endswith('.sh'):(W/name).chmod(0o755)
def patch(path,expected):
 assert sha(path)==expected
 for line in path.read_text().splitlines():
  if line.startswith(('--- ','+++ ')):
   p=Path(line[4:]);assert p.parts[0]in('a','b')and not p.is_absolute()and'..'not in p.parts
 subprocess.run(['/usr/bin/patch','--batch','--forward','-p1','-i',str(path.resolve())],cwd=W,check=True,capture_output=True)
if info['language']=='rf2':
 assert args.compiler,'Select the qualified 0.44 native compiler explicitly';C=Path(args.compiler).resolve();assert sha(C)==index['compilerSHA256'],'Compiler identity mismatch';shutil.copy2(C,W/'rf2c');(W/'lib').mkdir()
 for name,h in index['SDKLibrarySHA256'].items():
  if name in('io.flow','storage.flow','text.flow','datetime.flow'):relative='examples/documents/lib/'+name
  elif name=='sha256.rf2':relative='examples/evidence-contract/lib/'+name
  elif name=='output.rf2':relative='examples/collection-tools/lib/'+name
  else:relative='experiments/typed-booking/lib/'+name
  data=subprocess.check_output(['git','show',index['SDKCommit']+':'+relative],cwd=R);assert hashlib.sha256(data).hexdigest()==h; (W/'lib'/name).write_bytes(data)
 if info['sdkChangesSHA256']:patch(P/'sdk-changes.diff',info['sdkChangesSHA256'])
else:
 assert sha(S/'booking_sdk.py')==index['pythonSDK_SHA256'];shutil.copy2(S/'booking_sdk.py',W/'booking_sdk.py')
if args.repair and info['repairSHA256']:patch(P/'protocol-repair.diff',info['repairSHA256'])
if info['language']=='rf2':
 subprocess.run([str(C),str(W/'main.flow'),str(W/'app'),'--opt'],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',str(W/'app')],capture_output=True,check=True)
 if not args.repair:assert sha(W/'app')==info['originalBinarySHA256'],'Rebuild differs from the original signed trial image'
print(json.dumps(dict(directory=str(W),sample=args.sample,repaired=args.repair,executed=False)))
