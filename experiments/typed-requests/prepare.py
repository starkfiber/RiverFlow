"""0.49 source candidate: refuse an owned assignment consumed by its RHS."""
from pathlib import Path
import hashlib,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[2]
if len(sys.argv)!=2:raise SystemExit('Usage: prepare.py NEW-DIRECTORY')
D=Path(sys.argv[1]).resolve()
if D.exists():raise SystemExit('Use a new directory')
with tempfile.TemporaryDirectory(prefix='rf2-request-base-')as temporary:
    p=Path(temporary)/'base'
    subprocess.run([sys.executable,str(R/'experiments/developer-loop/prepare.py'),str(p)],check=True,capture_output=True)
    s=(p/'compiler.flow').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='7fe4a9ed8c2a2b144d108023d72e3e5a88ab2177b59425990d8c157b1c1072dd'
old='''   do scalar_expression(1,0)
   end
   do pop1()
   return emit(4177526816)'''
new='''   do scalar_expression(1,0)
   end
   do require(load64(local_ready(f,root)),"assignment destination was consumed by its right-hand side")
   do pop1()
   return emit(4177526816)'''
assert s.count(old)==1
s=s.replace(old,new)
D.mkdir(parents=True);(D/'compiler.flow').write_text(s)
print(hashlib.sha256(s.encode()).hexdigest())
