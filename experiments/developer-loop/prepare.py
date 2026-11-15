"""Prepare an isolated 0.48 candidate; preserve the published 0.47 source."""
from pathlib import Path
import hashlib, subprocess, sys, tempfile

R = Path(__file__).resolve().parents[2]
if len(sys.argv) != 2:
    raise SystemExit('Usage: prepare.py NEW-DIRECTORY')
D = Path(sys.argv[1]).resolve()
if D.exists():
    raise SystemExit('Use a new directory')
with tempfile.TemporaryDirectory(prefix='rf2-dev-loop-') as temporary:
    p = Path(temporary) / 'base'
    subprocess.run([sys.executable, str(R/'experiments/app-effort/prepare.py'), str(p)], check=True, capture_output=True)
    s = (p/'compiler.flow').read_text()
assert hashlib.sha256(s.encode()).hexdigest() == 'f09c6795beffe7084eb39b140ec33f52594cc1bddb0a52f77ddadd3ad138b80d'

def replace(old, new):
    global s
    assert s.count(old) == 1, (old[:100], s.count(old))
    s = s.replace(old, new, 1)

# Exactly one saved destination address is pending on these assignment routes.
# Failed propagation must retire it before the ordinary function cleanup path.
replace('fn try_value()\n', 'fn try_value()\n return try_value_pending(0)\nend\nfn try_value_pending(pending)\n do require((pending==0)|(pending==16),"internal propagation stack contract")\n')
replace(' # x0/x1 keep the primary error; ordinary common-return cleanup still runs.\n do jump(load64(state()+88),16)', ' # Drop only the known saved field address; keep primary x0/x1 unchanged.\n if pending\n  do emit(2432713727)\n end\n do jump(load64(state()+88),16)')
replace('     do expect("=")\n     do scalar_expression(1,0)\n     do pop1()\n     do emit(4177526816 | (field<<10))', '     do expect("=")\n     if try_prefix()\n      do try_value_pending(16)\n     else\n      do scalar_expression(1,0)\n     end\n     do pop1()\n     do emit(4177526816 | (field<<10))')
replace('   do expect("=")\n   do scalar_expression(1,0)\n   do pop1()\n   return emit(4177526816)', '   do expect("=")\n   if try_prefix()\n    do try_value_pending(16)\n   else\n    do scalar_expression(1,0)\n   end\n   do pop1()\n   return emit(4177526816)')

# The source map is generated while the existing expander copies each raw line.
# 20 bits cover its 512 KiB aggregate source bound, upper bits name 32 modules.
replace('    do module_append(p + i, end - i)\n', '    do source_map_line(index,i,end-i+1)\n    do module_append(p + i, end - i)\n')
replace(' let line = 1\n let column = 1\n', ' if source_map_diagnostic(offset)\n  return 0\n end\n let line = 1\n let column = 1\n')
for old, new in [
    ('"parameter bound"', '"parameter bound: at most 8 parameters; group related fields in a record parameter"'),
    ('"argument bound"', '"argument bound: at most 8 arguments; pass a record for related values"'),
    ('"record declarations must be function-level"', '"record declarations must be function-level: declare before if/while/handle, then update fields"'),
    ('"result function requires final explicit return"', '"result function requires final explicit return: add a root-level return ok(value) or return err(code), even after returning branches"'),
]:
    assert old in s
    s = s.replace(old, new)
s += '\n' + (R/'experiments/developer-loop/diagnostics.flow').read_text()
D.mkdir(parents=True)
(D/'compiler.flow').write_text(s)
print(hashlib.sha256(s.encode()).hexdigest())
