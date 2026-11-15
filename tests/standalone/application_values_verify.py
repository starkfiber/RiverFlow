"""Bounded native borrowed-value acceptance, not general owned-value qualification."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import random
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = Path(os.environ['RF2_NESTED_COMPILER']).resolve()
BASELINE = Path(os.environ['RF2_TEST_COMPILER']).resolve()
OUT = Path(tempfile.mkdtemp(prefix='application-values-', dir=ROOT/'artifacts'))
ROWS = []
SEED = 41151126
RNG = random.Random(SEED)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, passed, detail=None):
    ROWS.append({'name': name, 'passed': bool(passed), 'detail': detail})
    if not passed:
        (OUT/'FAILED.json').write_text(json.dumps(ROWS, indent=2)+'\n')
        raise AssertionError((name, detail))


def invoke(args, **kw):
    return subprocess.run(list(map(str, args)), capture_output=True, timeout=20, **kw)


def build(name, source, opt, expected=None):
    p = OUT/(name+'.flow')
    p.write_text(source)
    exe = OUT/(name+('-opt' if opt else '-default'))
    q = invoke([CANDIDATE, p, exe, *(['--opt'] if opt else [])])
    diagnostic = (q.stdout+q.stderr).decode(errors='replace')
    if expected:
        check(name+' refuses '+str(opt), q.returncode != 0 and expected in diagnostic, diagnostic[:400])
        check(name+' no rejected output '+str(opt), not exe.exists())
        return None
    check(name+' compiles '+str(opt), q.returncode == 0, diagnostic[:400])
    q = invoke(['/usr/bin/codesign', '-s', '-', exe])
    check(name+' signs '+str(opt), q.returncode == 0, q.stderr.decode(errors='replace'))
    return exe


# Copy only the reviewed physical modules needed by the example. Keep them hashed.
lib = OUT/'lib'
lib.mkdir()
for name in ('io.flow', 'text.flow', 'datetime.flow'):
    shutil.copy2(ROOT/'examples/documents/lib'/name, lib/name)
APP = ROOT/'experiments/nested-records/examples/booking-conflict.flow'
source = APP.read_text()
# The baseline must see actual dependencies, rather than refuse a missing import.
base_app = OUT/'baseline-control.flow'
base_app.write_text(source)
nearby = invoke([BASELINE, base_app, OUT/'baseline-control'])
check('baseline refuses nested type after dependency resolution', nearby.returncode != 0 and b'expected: u64' in nearby.stdout+nearby.stderr, (nearby.stdout+nearby.stderr).decode(errors='replace')[:400])

workloads = []
for i in range(300):
    day = datetime.date(2026, 1, 1)+datetime.timedelta(days=RNG.randrange(365))
    other = day+datetime.timedelta(days=i % 4 == 0)
    a = RNG.randrange(1440)
    b = RNG.randrange(a+1, 1441)
    c = a if i % 7 == 0 else RNG.randrange(1440)
    d = RNG.randrange(c+1, 1441)
    def clock(n):
        return f'{n//60:02}:{n%60:02}'
    args = [day.isoformat(), clock(a), clock(b), other.isoformat(), clock(c), clock(d)]
    expected = int(day == other and a < d and c < b)
    workloads.append((args, expected))
workloads += [
    (['2026-11-15','09:00','10:00','2026-11-15','10:00','11:00'],0),
    (['2028-02-29','23:59','24:00','2028-02-29','23:59','24:00'],1),
    (['0001-01-01','00:00','00:01','9999-12-31','00:00','00:01'],0),
]
invalid = [
    [], ['2026-11-15'],
    ['2026-02-29','09:00','10:00','2026-11-15','09:00','10:00'],
    ['2026-11-15','24:00','24:00','2026-11-15','09:00','10:00'],
    ['2026-11-15','09:00','09:00','2026-11-15','09:00','10:00'],
    ['2026-11-15','10:00','09:00','2026-11-15','09:00','10:00'],
    ['2026-11-15','09:60','10:00','2026-11-15','09:00','10:00'],
    ['2026-11-15','09:00','24:01','2026-11-15','09:00','10:00'],
    ['2026-11-15','09:00','10:00','2026-13-01','09:00','10:00'],
]
for opt in (False, True):
    exe = build('booking-conflict', source, opt)
    for i, (args, expected) in enumerate(workloads):
        q = invoke([exe, *args])
        check(f'booking output {opt} {i}', q.returncode == 0 and q.stdout == ('{"conflict":'+str(expected)+'}\n').encode(), {'args':args,'expected':expected,'exit':q.returncode,'stdout':q.stdout.decode(errors='replace')[:150]})
    for i, args in enumerate(invalid):
        q = invoke([exe, *args])
        check(f'invalid booking {opt} {i}', q.returncode == 2 and q.stdout == b'', {'args':args,'exit':q.returncode,'stdout':q.stdout.decode(errors='replace')[:100]})
    q = invoke([exe, *workloads[0][0]], preexec_fn=lambda: os.close(1))
    check('closed output is failure '+str(opt), q.returncode == 2)
    print('booking mode', opt, 'passed', flush=True)

base = 'profile RF2_SYSTEM_A64_V1\nrecord Leaf(value:u64)\nrecord Other(value:u64)\nrecord Pair(child:Leaf)\n'
refusals = {
    'nominal-child': (base+'fn main(argc,argv)\n let other=Other(4)\n let p=Pair(other)\n return 0\nend\n', 'nested constructor type mismatch'),
    'child-before-init': (base+'fn main(argc,argv)\n let p=Pair(later)\n let later=Leaf(4)\n return 0\nend\n', 'local used before initialization or outside scope'),
    'scalar-escape': (base+'fn main(argc,argv)\n let l=Leaf(4)\n let p=Pair(l)\n return p.child\nend\n', 'scalar expression required'),
    'borrow-copy': (base+'fn main(argc,argv)\n let l=Leaf(4)\n let p=Pair(l)\n let escape=p.child\n return 0\nend\n', 'scalar expression required'),
    'parent-rebind': (base+'fn main(argc,argv)\n let l=Leaf(4)\n let p=Pair(l)\n set p=Pair(l)\n return 0\nend\n', 'record rebinding refused'),
    'constructor-arity': (base+'fn main(argc,argv)\n let l=Leaf(4)\n let p=Pair(l,l)\n return 0\nend\n', 'expected: )'),
    'raw-borrow': (base+'fn main(argc,argv)\n let l=Leaf(4)\n let p=Pair(l)\n return load64(p.child)\nend\n', 'record passed to raw intrinsic'),
    'borrow-result': (base+'result Escaped(Pair,u64)\nfn main(argc,argv)\n return 0\nend\n', 'borrowed nested record cannot escape in result'),
}
for name, (source, diagnostic) in refusals.items():
    for opt in (False, True):
        build(name, source, opt, diagnostic)

# Exercise maximum named-type depth and field offsets without changing budgets.
for depth, width in ((1,1),(1,16),(8,16),(31,1)):
    source = 'profile RF2_SYSTEM_A64_V1\nrecord Leaf(value:u64)\n'
    for n in range(depth):
        child = 'Leaf' if n == 0 else 'Layer'+str(n-1)
        source += 'record Layer'+str(n)+'('+','.join(f'f{x}:{child}' for x in range(width))+')\n'
    source += 'fn change(value)\n let count=buffer("counter",8)\n do store64(count,load64(count)+1)\n return value\nend\nfn main(argc,argv)\n let leaf=Leaf(7)\n'
    for n in range(depth):
        child = 'leaf' if n == 0 else 'layer'+str(n-1)
        source += ' let layer'+str(n)+'=Layer'+str(n)+'('+','.join([child]*width)+')\n'
    path = 'layer'+str(depth-1)+('.f'+str(width-1))*depth+'.value'
    source += f' set {path}=change(19)\n if (leaf.value!=19)|({path}!=19)|(load64(buffer("counter",8))!=1)\n  return 1\n end\n return 0\nend\n'
    for opt in (False, True):
        exe = build(f'depth{depth}-width{width}', source, opt)
        q = invoke([exe])
        check(f'boundary execution {depth} {width} {opt}', q.returncode == 0, q.stderr.decode(errors='replace'))

report = {
    'schema':'rf2.application-values.acceptance.v1',
    'baselineCommit':invoke(['git','rev-parse','HEAD'],cwd=ROOT).stdout.decode().strip(),
    'seed':SEED,'candidateSHA256':digest(CANDIDATE),'qualifiedCompilerSHA256':digest(BASELINE),
    'appSHA256':digest(APP),'controllerSHA256':digest(Path(__file__)),
    'sharedLibraries':{p.name:digest(p) for p in sorted(lib.iterdir())},
    'workloadsPerMode':len(workloads),'invalidInputsPerMode':len(invalid),
    'checks':ROWS,'allPassed':all(r['passed'] for r in ROWS),
    'scope':'Mac native borrowed record composition in an isolated candidate; no journal writes, owned nested values, physical hardware, speed/token benchmark or release qualification.',
}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':len(ROWS),'report':str(OUT/'report.json')}),flush=True)
