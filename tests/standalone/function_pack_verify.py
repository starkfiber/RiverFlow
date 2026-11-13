"""Packed native function cache: clean-build and adversarial container controls.

Local developer controller. Hashes detect corruption; this is not authentication
against a malicious writer with the same user identity.
"""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import struct
import subprocess
import time

R = Path(__file__).resolve().parents[2]
C = Path(os.environ['RF2_TEST_COMPILER']).resolve()
D = R / 'artifacts/function-reuse' / ('pack-verify-' + str(time.time_ns()))
D.mkdir(parents=True)
CACHE = D / 'cache'
CACHE.mkdir(mode=0o700)
ROWS = []
SERIAL = 0
BASE = '''profile RF2_SYSTEM_A64_V1
fn leaf(x)
 let n=x*3
 return n+1
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


def run(args, timeout=30):
    return subprocess.run([str(x) for x in args], capture_output=True,
                          timeout=timeout, env={'PATH': '/nonexistent'})


def observe(path):
    q = run(['/usr/bin/codesign', '-s', '-', path])
    assert q.returncode == 0, q.stderr
    q = run([path], timeout=5)
    return q.returncode, q.stdout.hex(), q.stderr.hex()


def compile_pair(label, source=BASE, *, cache=CACHE, hits=None, bad=False,
                 refusal=False, publication_failure=False, flags=('--opt', '--compact')):
    global SERIAL
    SERIAL += 1
    source_path = D / f'source-{SERIAL}.rf2'
    source_path.write_text(source)
    clean = D / f'clean-{SERIAL}'
    packed = D / f'packed-{SERIAL}'
    oracle = run([C, source_path, clean, *flags])
    got = run([C, source_path, packed, *flags, '--reuse-pack', cache])
    if bad:
        assert oracle.returncode != 0, (label, 'invalid source accepted')
        assert got.returncode != 0 and not packed.exists(), (label, got.stderr)
        ROWS.append(dict(case=label, outcome='invalid-source-rejected'))
        return None
    assert oracle.returncode == 0, (label, oracle.stderr)
    if publication_failure:
        assert got.returncode != 0 and packed.exists(), (label, got.stderr)
        assert clean.read_bytes() == packed.read_bytes(), (label, 'partial image differs')
        assert not Path(str(packed)+'.reuse.json').exists()
        ROWS.append(dict(case=label, outcome='publication-refused-valid-image-remains', stderr=got.stderr.decode()))
        return None
    if refusal:
        assert got.returncode != 0 and not packed.exists(), (label, got.stderr)
        ROWS.append(dict(case=label, outcome='unsafe-cache-rejected'))
        return None
    assert got.returncode == 0, (label, got.stderr)
    assert clean.read_bytes() == packed.read_bytes(), (label, 'unsigned bytes differ')
    info = json.loads(Path(str(packed) + '.reuse.json').read_text())
    assert info['schema'] == 'rf2.function.reuse.v1', (label, info)
    assert info['compilerSHA256'] == hashlib.sha256(C.read_bytes()).hexdigest(), (label, info)
    if hits is not None:
        assert info['reused'] == hits, (label, info, hits)
    observation = observe(clean)
    assert observe(packed) == observation, (label, 'execution differs')
    if '--functions' in flags:
        assert Path(str(clean)+'.functions').read_bytes() == Path(str(packed)+'.functions').read_bytes()
    ROWS.append(dict(case=label, outcome='clean-byte-and-execution-match',
                     receipt=info, observation=observation))
    return info


def u64(data, off):
    return struct.unpack_from('<Q', data, off)[0]


def put64(data, off, value):
    struct.pack_into('<Q', data, off, value)


def repair(data):
    data[40:72] = hashlib.sha256(data[72:]).digest()
    return data


def entries(data):
    count = u64(data, 72)
    assert 0 < count <= 256
    found = []
    for i in range(count):
        slot = 96 + i*48
        off, size = u64(data, slot), u64(data, slot+8)
        if size:
            assert off >= 96 + count*48 and off+size <= len(data)
            found.append((slot, off, size))
    assert found
    return found


def mutate_all_units(data, offset, value, *, rehash_units=True):
    for _, off, size in entries(data):
        put64(data, off+offset, value)
        if rehash_units:
            data[off+40:off+72] = hashlib.sha256(data[off+72:off+size]).digest()
    return repair(data)


def fresh_pack():
    packs = sorted(CACHE.glob('*.pack'))
    # Source context/mode tests create other namespaces. Select BASE by testing
    # under an isolated cache for corruption and unsafe entry controls.
    assert len(packs) == 1, packs
    return packs[0]


def main():
    compile_pair('empty packed cache', hits=0)
    compile_pair('warm packed cache', hits=2)
    pack = fresh_pack()
    original = pack.read_bytes()
    assert original[:8] == b'RF2FP001'
    assert u64(original, 80) == len(original)
    assert original[40:72] == hashlib.sha256(original[72:]).digest()
    entries(original)
    before = (pack.stat().st_mtime_ns, hashlib.sha256(original).hexdigest())
    compile_pair('warm hit does not rewrite unchanged pack', hits=2)
    assert (pack.stat().st_mtime_ns, hashlib.sha256(pack.read_bytes()).hexdigest()) == before
    compile_pair('main entry-only edit keeps scalar units',
                 BASE.replace('caller(7)!=22', 'caller(8)!=25'), hits=2)
    compile_pair('one helper body changes one slot', BASE.replace('x*3', 'x*5'), hits=1)
    compile_pair('changed helper warm', BASE.replace('x*3', 'x*5'), hits=2)
    compile_pair('source reversion rebuilds changed slot', hits=1)
    compile_pair('source reversion warm', hits=2)

    mutations = [
        ('pack payload bit flip', lambda d: d[:-1]+bytes([d[-1]^1])),
        ('pack header truncation', lambda d: d[:20]),
        ('pack payload truncation', lambda d: d[:-4]),
        ('pack trailing bytes', lambda d: d+b'extra'),
        ('pack magic', lambda d: b'BADMAGIC'+d[8:]),
        ('pack namespace', lambda d: d[:8]+bytes(32)+d[40:]),
    ]
    for label, mutate in mutations:
        pack.write_bytes(mutate(bytearray(original)))
        compile_pair(label+' fallback', hits=0)
        compile_pair(label+' repaired warm', hits=2)

    def field(off, value):
        def mutate(data):
            put64(data, off, value)
            return repair(data)
        return mutate

    def directory(which):
        def mutate(data):
            es = entries(data)
            first, off, size = es[0]
            if which == 'before-payload': put64(data, first, 96)
            elif which == 'past-end': put64(data, first, len(data)+8)
            elif which == 'overflow-length': put64(data, first+8, 2**64-1)
            elif which == 'zero-length-nonzero-offset': put64(data, first+8, 0)
            elif which == 'overlap':
                assert len(es)>1
                put64(data, es[1][0], off)
            elif which == 'wrong-key': data[first+16:first+48] = bytes(32)
            else: raise AssertionError(which)
            return repair(data)
        return mutate

    structural = [
        ('wrong function count', field(72, 257)),
        ('wrong declared container size', field(80, 2**64-1)),
        ('nonzero reserved field', field(88, 1)),
    ] + [('directory '+x, directory(x)) for x in [
        'before-payload', 'past-end', 'overflow-length',
        'zero-length-nonzero-offset', 'overlap', 'wrong-key']]
    for label, mutate in structural:
        pack.write_bytes(mutate(bytearray(original)))
        compile_pair(label+' rehashed structural refusal', hits=0)
        compile_pair(label+' repaired warm', hits=2)
    for label, offset, value in [
        ('unit code size overflow', 72, 2**64-1),
        ('unit epilogue offset overflow', 80, 2**64-1),
        ('unit fixup offset overflow', 88, 2**64-1),
        ('unit local count mismatch', 96, 999),
    ]:
        pack.write_bytes(mutate_all_units(bytearray(original), offset, value))
        compile_pair(label+' rehashed units', hits=0)
        compile_pair(label+' repaired warm', hits=2)

    # A sound container may have one individually damaged unit. Other slots
    # remain useful, and repair must republish both the repaired and hit units.
    for kind in ['unit-digest', 'unit-magic']:
        data = bytearray(original)
        _, off, size = entries(data)[0]
        if kind == 'unit-digest': data[off+40] ^= 1
        else: data[off:off+8] = b'BADUNIT!'
        pack.write_bytes(repair(data))
        compile_pair(kind+' repairs one slot and retains the other', hits=1)
        compile_pair(kind+' repaired warm', hits=2)
    pack.write_bytes(original + bytes(1114113-len(original)))
    compile_pair('oversized container falls back within bound', hits=0)
    compile_pair('oversized container repaired warm', hits=2)
    branch = BASE.replace(' let n=x*3\n return n+1',
                          ' if x>4\n  return x*3+1\n end\n return x+1')
    compile_pair('ineligible changed helper never replays old unit', branch, hits=1)
    compile_pair('ineligible changed helper stays on normal compiler path', branch, hits=1)
    compile_pair('eligible source reversion has valid identity', hits=2)

    # Hashes are integrity checks only. Do not claim rejection of arbitrary
    # attacker-rehashed code under the explicitly excluded same-UID writer.
    pack.unlink()
    target = D/'outside-entry'
    target.write_bytes(original)
    target.chmod(0o600)
    pack.symlink_to(target)
    compile_pair('entry final symlink ignored and safely replaced', hits=0)
    assert target.read_bytes() == original and not pack.is_symlink()
    pack.unlink()
    os.link(target, pack)
    compile_pair('hardlinked entry ignored and safely replaced', hits=0)
    assert target.read_bytes() == original and pack.stat().st_nlink == 1
    pack.chmod(0o644)
    compile_pair('world-readable entry ignored', hits=0)
    pack.unlink()
    os.mkfifo(pack, 0o600)
    compile_pair('FIFO entry never blocks and is replaced', hits=0)
    assert pack.is_file()
    pack.unlink()
    pack.mkdir(mode=0o700)
    # A directory cannot be atomically replaced by a regular cache file.
    compile_pair('directory at entry path refuses publication', publication_failure=True)
    pack.rmdir()
    compile_pair('directory obstruction removed', hits=0)
    compile_pair('recovered healthy warm pack', hits=2)
    (CACHE/'uncommitted.pack.tmp').write_bytes(b'incomplete')
    compile_pair('uncommitted sibling ignored', hits=2)
    CACHE.chmod(0o755)
    compile_pair('shared root permissions rejected', refusal=True)
    CACHE.chmod(0o700)
    link = D/'cache-symlink'
    link.symlink_to(CACHE)
    compile_pair('root final symlink rejected', cache=link, refusal=True)
    fd = os.open(CACHE, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        compile_pair('concurrent directory owner rejected', refusal=True)
    finally:
        os.close(fd)
    compile_pair('released lock permits reuse', hits=2)

    other = D/'context-cache'
    other.mkdir(mode=0o700)
    compile_pair('context baseline', cache=other, hits=0)
    compile_pair('declaration changes namespace', BASE.replace('fn leaf', 'record Value(n:u64)\nfn leaf'), cache=other, hits=0)
    compile_pair('function signature changes namespace', BASE.replace('fn separate(x)', 'fn separate(x,y)').replace('return x+9','return x+y'), cache=other, hits=0)
    compile_pair('function reorder changes namespace', BASE.replace('fn separate(x)\n return x+9\nend\n','').replace('fn leaf(x)', 'fn separate(x)\n return x+9\nend\nfn leaf(x)'), cache=other, hits=0)
    compile_pair('optimizer mode namespace', cache=other, hits=0, flags=('--compact',))
    compile_pair('legacy image namespace', cache=other, hits=0, flags=('--opt',))
    compile_pair('legacy image warm', cache=other, hits=2, flags=('--opt',))
    compile_pair('function maps disable replay', cache=other, hits=0, flags=('--opt','--compact','--functions'))
    no_units = D/'no-units'
    no_units.mkdir(mode=0o700)
    only_main = 'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return 0\nend\n'
    compile_pair('no eligible helpers needs no container', only_main, cache=no_units, hits=0)
    assert not list(no_units.iterdir())
    invalid = D/'invalid-cache'
    invalid.mkdir(mode=0o700)
    compile_pair('invalid source does not publish pack', BASE.replace('return leaf(x)', 'return missing(x)'), cache=invalid, bad=True)
    assert not list(invalid.iterdir())
    before = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in CACHE.glob('*.pack')}
    compile_pair('invalid source does not modify existing pack', BASE.replace('return leaf(x)', 'return missing(x)'), bad=True)
    assert before == {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in CACHE.glob('*.pack')}
    out = D/'duplicate-output'
    p = D/'duplicate-source.rf2'
    p.write_text(BASE)
    q = run([C,p,out,'--reuse-cache',CACHE,'--reuse-pack',CACHE])
    assert q.returncode != 0 and not out.exists()
    ROWS.append(dict(case='mixed loose and packed options reject', outcome='rejected-duplicate-cache-option'))
    report = dict(schema='rf2.function.pack.verification.v1', passed=True,
                  compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),
                  controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  cases=ROWS, limits='Finite local ARM64 controls. Clean unsigned image bytes and execution are checked per admitted source. SHA-256 is corruption detection, not protection against malicious same-UID cache writers. Root ancestor trust remains a local precondition.')
    (D/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(report=str(D/'report.json'), passed=True, cases=len(ROWS))))


if __name__ == '__main__':
    main()
