"""Replay unchanged 169-check diagnostic oracle with images/cache explicitly banked."""
from pathlib import Path
import argparse,hashlib,json,os,tempfile
R=Path(__file__).resolve().parents[3]
def main():
 p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);slot=Path(tempfile.mkdtemp(prefix='rf2-diag-regress-',dir=os.environ['TMPDIR']));original=R/'tests/standalone/diagnostics_050_verify.py';text=original.read_text();changes=[]
 def replace(old,new,n=1):
  nonlocal text
  assert text.count(old)==n,(old,text.count(old));text=text.replace(old,new);changes.append({'old':old,'new':new,'occurrences':n})
 replace("D=Path(tempfile.mkdtemp(prefix='diagnostics-050-checks-',dir=R/'artifacts'));checks=[]",'D=Path('+repr(str(d/'oracle'))+');D.mkdir();BIN=Path('+repr(str(slot))+');checks=[]')
 replace("exe=p.with_suffix('')","exe=BIN/p.stem")
 replace("exe=D/(label+str(opt))","exe=BIN/(label+str(opt))")
 replace("exe=D/('512-'+str(opt))","exe=BIN/('512-'+str(opt))")
 replace("out=too.with_suffix('')","out=BIN/too.stem")
 replace("cache=D/('cache-'+str(opt))","cache=BIN/('cache-'+str(opt))")
 replace("out=D/('reuse-'+str(opt)+'-'+str(round))","out=BIN/('reuse-'+str(opt)+'-'+str(round))")
 replace("exe=D/('high-owned-'+str(opt))","exe=BIN/('high-owned-'+str(opt))")
 # Negative output paths are banked too; refusal expectations stay unchanged.
 replace("sub/'program'","BIN/'import-error'")
 replace("D/'bad'","BIN/'bad'",3)
 replace("D/'missing-import-out'","BIN/'missing-import-out'")
 (d/'ORACLE-ADAPTATION.json').write_text(json.dumps({'originalSHA256':hashlib.sha256(original.read_bytes()).hexdigest(),'adaptedSHA256':hashlib.sha256(text.encode()).hexdigest(),'changes':changes,'scope':'Only persistent evidence root and explicit disposable native image/cache paths; assertions and input programs unchanged'},indent=2)+'\n');(d/'ADAPTED-ORACLE.py').write_text(text)
 os.environ.update(RF2_DIAGNOSTIC_COMPILER=str(a.compiler.resolve()),RF2_DIAGNOSTIC_SOURCE=str(a.source.resolve()),RF2_DIAGNOSTIC_BASELINE=str(a.baseline.resolve()))
 exec(compile(text,str(original),'exec'),{'__file__':str(original),'__name__':'__main__'})
if __name__=='__main__':main()
