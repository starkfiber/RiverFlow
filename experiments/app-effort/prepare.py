"""Prepare scalar propagation and direct result forwarding atop pinned0.46."""
from pathlib import Path
import hashlib,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[2]
if len(sys.argv)!=2:raise SystemExit('Usage: prepare.py NEW-DIRECTORY')
D=Path(sys.argv[1]).resolve()
if D.exists():raise SystemExit('Use a new output directory')
with tempfile.TemporaryDirectory(prefix='rf2-app-effort-')as temporary:
 p=Path(temporary)/'base';subprocess.run([sys.executable,str(R/'experiments/owned-rows/prepare.py'),p],cwd=R,check=True,capture_output=True);s=(p/'compiler.flow').read_text()
if hashlib.sha256(s.encode()).hexdigest()!='514b95528cef244f9255801075f5ad333c36eb7a17101cf20a7e32f97332edf8':raise ValueError('Review changed0.46 compiler source')
def replace(old,new):
 global s
 if s.count(old)!=1:raise ValueError(('patch drift',old[:100],s.count(old)))
 s=s.replace(old,new,1)
replace('''      if try_inplace(target) == 0
       set coalesced''','''      if try_prefix()
       do try_value()
       do access_local(0,target,1)
      else
      if try_inplace(target) == 0
       set coalesced''')
replace('''       if coalesced == 0
        do access_local(0, target, 1)
       end
      end
     end''','''       if coalesced == 0
        do access_local(0, target, 1)
       end
      end
      end
     end''')
replace('''    if match("do")
     do advance()
     do expression(1, 0)''','''    if match("do")
     do advance()
     if try_prefix()
      do try_value()
     else
      do expression(1, 0)
     end''')
replace(' do require(match("ok") | match("err"), "typed result return needs ok or err")\n set tag = match("err")',' if (match("ok") | match("err"))==0\n  let at=load64(state()+24)\n  do require((load64(token(at))==1)&tmatch(at+1,"("),"typed result return needs ok or err, or a matching scalar result call")\n  do require(load64(record_info(id)+152)==0,"forwarding is limited to scalar typed results")\n  let name=advance()\n  do expect("(")\n  do invoke(name,1)\n  do require(load64(state()+136)==id,"forwarded result must match the enclosing nominal scalar result")\n  do require(load64(token(load64(state()+24)))==5,"forwarding is a complete call; use explicit ok/err for other expressions")\n  do store64(state()+136,0)\n  do store64(state()+232,0)\n  return 0\n end\n do require(match("ok") | match("err"), "typed result return needs ok or err")\n set tag = match("err")')
s+='\n'+(R/'experiments/app-effort/compiler-extension.flow').read_text()
D.mkdir(parents=True);(D/'compiler.flow').write_text(s);print(hashlib.sha256(s.encode()).hexdigest())
