"""Adversarial native function-reuse checks; clean compilation is the byte oracle.

The compiler must be supplied explicitly through RF2_TEST_COMPILER. This is a
local developer controller, never an MCP effect or a user runtime dependency.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time
import shutil
import fcntl

R = Path(__file__).resolve().parents[2]
C = Path(os.environ['RF2_TEST_COMPILER']).resolve()
D = R / 'artifacts/function-reuse' / ('verify-' + str(time.time_ns()))
D.mkdir(parents=True)
CACHE = D / 'cache'
CACHE.mkdir(mode=0o700)
REUSE_FLAG = os.environ.get('RF2_FUNCTION_REUSE_FLAG', '--reuse-cache')
CONTROLLER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
ROWS = []
SERIAL = 0


def run(args, timeout=30):
    return subprocess.run([str(x) for x in args], capture_output=True,
                          timeout=timeout, env={'PATH': '/nonexistent'})


def receipt(process, output):
    """Interface is pinned by implementation before qualifying this controller."""
    sidecar = Path(str(output) + '.reuse.json')
    if sidecar.exists():
        return json.loads(sidecar.read_text())
    for line in process.stderr.decode(errors='replace').splitlines():
        if line.startswith('RF2_REUSE '):
            return json.loads(line[len('RF2_REUSE '):])
    raise AssertionError('compiler did not emit a function-reuse receipt')


def signed_observation(output):
    signed = run(['/usr/bin/codesign', '-s', '-', output])
    assert signed.returncode == 0, signed.stderr
    q = run([output], timeout=5)
    return (q.returncode, q.stdout, q.stderr)


def compile_pair(label, source, *, opt=True, compact=True, expect_reuse=None,
                 bad_source=False, cache=CACHE, compiler=C, cache_refusal=False, functions=False):
    global SERIAL
    SERIAL += 1
    p = D / f'source-{SERIAL}.rf2'
    p.write_text(source)
    clean = D / f'clean-{SERIAL}'
    cached = D / f'cached-{SERIAL}'
    flags = (['--opt'] if opt else []) + (['--compact'] if compact else []) + (['--functions'] if functions else [])
    oracle = run([compiler, p, clean, *flags])
    candidate = run([compiler, p, cached, *flags, REUSE_FLAG, cache])
    if bad_source:
        assert oracle.returncode != 0, (label, 'bad-source control unexpectedly valid')
        assert candidate.returncode != 0 and not cached.exists(), (label, candidate.stderr)
        ROWS.append({'case': label, 'outcome': 'rejected-invalid-source'})
        return None
    assert oracle.returncode == 0, (label, oracle.stderr)
    if cache_refusal:
        assert candidate.returncode != 0 and not cached.exists(), (label, candidate.stderr)
        ROWS.append({'case': label, 'outcome': 'rejected-unsafe-cache'})
        return None
    assert candidate.returncode == 0, (label, candidate.stderr)
    assert clean.read_bytes() == cached.read_bytes(), (label, 'cache differs from clean build')
    if functions:
        assert Path(str(clean)+'.functions').read_bytes() == Path(str(cached)+'.functions').read_bytes(), (label, 'function map differs from clean build')
    info = receipt(candidate, cached)
    assert info['schema'] == 'rf2.function.reuse.v1', (label, info)
    assert all(type(info[k]) is int and info[k] >= 0 for k in ['reused','compiled','ineligible']), (label, info)
    assert info['compilerSHA256'] == hashlib.sha256(Path(compiler).read_bytes()).hexdigest(), (label, info)
    if expect_reuse is not None:
        assert (info['reused'] > 0) == expect_reuse, (label, info)
    expected = signed_observation(clean)
    got = signed_observation(cached)
    assert got == expected, (label, expected, got)
    ROWS.append({'case': label, 'outcome': 'clean-byte-and-execution-match',
                 'reuse': info, 'exit': got[0],
                 'stdoutHex': got[1].hex(), 'stderrHex': got[2].hex()})
    return info


BASE = '''profile RF2_SYSTEM_A64_V1
fn leaf(x)
 return x*3+1
end
fn separate(x)
 return x+9
end
fn caller(x)
 return leaf(x)
end
fn main(argc,argv)
 return caller(7)!=22
end
'''


def main():
    compile_pair('cold scalar functions', BASE, expect_reuse=False)
    compile_pair('warm scalar functions', BASE, expect_reuse=True)
    compile_pair('function maps coexist with reuse request', BASE, functions=True, expect_reuse=False)
    compile_pair('ordinary reuse remains available after function maps', BASE, expect_reuse=True)
    # argv[0] is caller-controlled; compiler identity must come from the running image.
    fakepath=R/'output/rf2c-027-reviewed'
    assert fakepath.exists() and hashlib.sha256(fakepath.read_bytes()).digest()!=hashlib.sha256(C.read_bytes()).digest()
    spoof_source=D/'spoofed-argv0.rf2'
    spoof_source.write_text(BASE)
    spoof_output=D/'spoofed-argv0'
    spoof_clean=D/'spoofed-argv0-clean'
    oracle=run([C,spoof_source,spoof_clean,'--opt','--compact'])
    assert oracle.returncode==0,oracle.stderr
    spoof=subprocess.run([str(fakepath),str(spoof_source),str(spoof_output),
                          '--opt','--compact',REUSE_FLAG,str(CACHE)],
                         executable=str(C),capture_output=True,timeout=30,
                         env={'PATH':'/nonexistent'})
    assert spoof.returncode==0,spoof.stderr
    spoof_info=receipt(spoof,spoof_output)
    assert spoof_info['compilerSHA256']==hashlib.sha256(C.read_bytes()).hexdigest(),spoof_info
    assert spoof_info['reused']>0,spoof_info
    assert spoof_clean.read_bytes()==spoof_output.read_bytes(),'spoofed argv0 changed clean output'
    assert signed_observation(spoof_clean)==signed_observation(spoof_output),'spoofed argv0 changed execution'
    ROWS.append({'case':'spoofed argv0 does not change actual compiler identity',
                 'outcome':'clean-byte-and-execution-match','reuse':spoof_info})
    compile_pair('comment and blank line edit', BASE.replace(' return x*3+1',
                 ' # commentary\n\n return x*3+1'))
    compile_pair('changed scalar body', BASE.replace('x*3+1', 'x*5+2'))
    compile_pair('source reversion', BASE)
    leaf = 'fn leaf(x)\n return x*3+1\nend\n'
    separate = 'fn separate(x)\n return x+9\nend\n'
    compile_pair('function order changes', BASE.replace(leaf, '').replace(separate, separate + leaf))
    compile_pair('remove unreferenced function', BASE.replace(separate, ''))
    compile_pair('add unreferenced scalar function', BASE.replace('fn main',
                 'fn added(x)\n return x*7+11\nend\nfn main'))
    compile_pair('change function signature and caller', BASE.replace('fn leaf(x)',
                 'fn leaf(x,y)').replace('return x*3+1', 'return x*3+y').replace('return leaf(x)', 'return leaf(x,1)'))
    compile_pair('record declaration context', BASE.replace('fn leaf', 'record Value(n:u64)\nfn leaf'))
    compile_pair('array declaration context', BASE.replace('fn leaf', 'array Values(u64,4)\nfn leaf'))
    compile_pair('optimizer mode separation', BASE, opt=False)
    compile_pair('legacy image mode separation', BASE, compact=False)
    compile_pair('warm legacy image', BASE, compact=False)
    compile_pair('unknown local must reject after warm cache', BASE.replace('return x*3+1', 'return absent+1'), bad_source=True)
    compile_pair('unknown callee must reject after warm cache', BASE.replace('return leaf(x)', 'return missing(x)'), bad_source=True)
    compile_pair('typed parameter misuse must reject after warm cache', BASE.replace('fn leaf(x)', 'fn leaf(x:Value)').replace('fn leaf', 'record Value(n:u64)\nfn leaf'), bad_source=True)
    compile_pair('missing function end must reject', BASE.replace(' return x*3+1\nend\n', ' return x*3+1\n'), bad_source=True)
    compile_pair('branching leaf clean fallback', BASE.replace(' return x*3+1',
                 ' if x>4\n  return x*3+1\n end\n return x+1'))
    compile_pair('loop leaf clean fallback', BASE.replace(' return x*3+1',
                 ' let total=1\n let i=0\n while i<x\n  set total=total+3\n  set i=i+1\n end\n return total'))
    shared = '''profile RF2_SYSTEM_A64_V1
fn shared()
 return buffer("shared",64)
end
fn main(argc,argv)
 let p=buffer("shared",64)
 do store64(p,123)
 return load64(shared())!=123
end
'''
    compile_pair('shared object registration fallback', shared)
    compile_pair('shared object size change', shared.replace('64)', '80)'))
    compile_pair('shared object size conflict refuses', shared.replace('let p=buffer("shared",64)', 'let p=buffer("shared",80)'), bad_source=True)
    compile_pair('source literals require object effect replay or fallback', BASE.replace('return x*3+1', 'return load8("a")+x'))
    library = D/'lib'
    library.mkdir()
    shared = library/'shared.rf2'
    shared.write_text('module shared\nfn adjust(x)\n return x*3+1\nend\n')
    (library/'helper.rf2').write_text('module helper\nuse "lib/shared.rf2"\nfn compute(x)\n return adjust(x)\nend\n')
    modular = 'profile RF2_SYSTEM_A64_V1\nuse "lib/helper.rf2"\nfn main(argc,argv)\n return compute(7)!=22\nend\n'
    compile_pair('transitive module cold', modular)
    compile_pair('transitive module warm', modular, expect_reuse=True)
    old_stat=shared.stat()
    shared.write_text(shared.read_text().replace('x*3+1','x*5+2'))
    os.utime(shared,ns=(old_stat.st_atime_ns,old_stat.st_mtime_ns))
    compile_pair('same-size same-mtime transitive body change',modular)
    shared.write_text(shared.read_text().replace('return x*5+2','return absent'))
    compile_pair('invalid transitive body after warm cache rejects',modular,bad_source=True)
    # A focused numeric corpus checks that reuse is real across emitted operators.
    numeric = [
        ('addition-wrap', 'x+9', 18446744073709551615, 8),
        ('subtraction-wrap', 'x-1', 0, 18446744073709551615),
        ('multiply-wrap', 'x*3', 18446744073709551615, 18446744073709551613),
        ('integer-division', 'x//7', 18446744073709551615, 2635249153387078802),
        ('bit-mask', 'x&255', 18446744073709551615, 255),
        ('bit-or', 'x|16', 1, 17),
        ('bit-xor', 'x^255', 15, 240),
        ('left-shift', 'x<<63', 1, 9223372036854775808),
        ('right-shift', 'x>>63', 18446744073709551615, 1),
        ('unsigned-comparison', 'x>9223372036854775808', 18446744073709551615, 1),
        ('parenthesized-expression', '(x+7)*(x-2)', 9, 112),
    ]
    for label,expr,value,expected in numeric:
        source=('profile RF2_SYSTEM_A64_V1\nfn numeric(x)\n return '+expr+
                '\nend\nfn main(argc,argv)\n return numeric('+str(value)+')!='+
                str(expected)+'\nend\n')
        compile_pair(label+' cold',source)
        compile_pair(label+' warm',source,expect_reuse=True)
        assert ROWS[-1]['exit']==0,(label,ROWS[-1])
    # One-byte corruption, header damage and truncation must never bless code.
    compile_pair('prepare corruption controls', BASE)
    entries = sorted(CACHE.glob('*.fn'))
    assert entries, 'no native function units were published'
    for label, mutate in [
            ('function payload corruption', lambda data: data[:-1]+bytes([data[-1]^1])),
            ('wrong entry key', lambda data: data[:8]+bytes(32)+data[40:]),
            ('wrong entry magic', lambda data: b'BADMAGIC'+data[8:]),
            ('declared code size bound', lambda data: data[:72]+(2**64-1).to_bytes(8,'little')+data[80:]),
            ('exit target bound', lambda data: data[:80]+(2**64-1).to_bytes(8,'little')+data[88:]),
            ('in-bounds exit metadata corruption', lambda data: data[:80]+bytes(8)+data[88:]),
            ('relocation offset bound', lambda data: data[:88]+(2**64-1).to_bytes(8,'little')+data[96:]),
            ('truncated unit header', lambda data: data[:20]),
            ('truncated unit payload', lambda data: data[:-4])]:
        # All matching units are damaged so a reported hit cannot be incidental.
        for entry in CACHE.glob('*.fn'):
            entry.write_bytes(mutate(entry.read_bytes()))
        compile_pair(label, BASE, expect_reuse=False)
        compile_pair(label+' repaired warm reuse', BASE, expect_reuse=True)
    # A sibling temporary file is not a committed native unit.
    (CACHE/'interrupted-writer.tmp').write_bytes(b'RF2FN001partial')
    compile_pair('incomplete sibling temporary ignored', BASE, expect_reuse=True)
    copy = D/'same-compiler-copy'
    shutil.copy2(C,copy)
    compile_pair('same compiler bytes at another path', BASE, compiler=copy, expect_reuse=True)
    alternate = os.environ.get('RF2_ALTERNATE_COMPILER')
    if alternate:
        alternate = Path(alternate).resolve()
        assert hashlib.sha256(alternate.read_bytes()).digest()!=hashlib.sha256(C.read_bytes()).digest()
        compile_pair('changed compiler byte identity', BASE, compiler=alternate, expect_reuse=False)
        compile_pair('original compiler identity remains reusable', BASE, expect_reuse=True)
    CACHE.chmod(0o755)
    compile_pair('shared-permission cache refuses', BASE, cache_refusal=True)
    CACHE.chmod(0o700)
    link = D/'cache-link'
    link.symlink_to(CACHE)
    compile_pair('cache root final symlink refuses', BASE, cache=link, cache_refusal=True)
    fd=os.open(CACHE,os.O_RDONLY)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        compile_pair('concurrent cache owner refuses', BASE, cache_refusal=True)
    finally:
        os.close(fd)
    compile_pair('lock release permits healthy reuse', BASE, expect_reuse=True)
    # Refusal before the final image must not commit pending cache entries.
    invalid_cache=D/'invalid-source-cache'
    invalid_cache.mkdir(mode=0o700)
    compile_pair('invalid source never publishes units', BASE.replace('return leaf(x)','return missing(x)'), cache=invalid_cache, bad_source=True)
    assert not list(invalid_cache.glob('*.fn')), 'failed compilation published function units'
    (D/'report.json').write_text(json.dumps({'schema': 'rf2.function.reuse.verification.v1',
        'passed': True, 'compilerSHA256': hashlib.sha256(C.read_bytes()).hexdigest(),
        'controllerSHA256': CONTROLLER_SHA256,
        'cases': ROWS, 'limits': 'Finite local ARM64 native compiler controls; no shared untrusted cache or universal language compatibility proof.'}, indent=2)+'\n')
    print(json.dumps({'report': str(D/'report.json'), 'passed': True, 'cases': len(ROWS)}))


if __name__ == '__main__':
    main()
