"""Independent linear-local reuse controls with clean-byte and execution oracles.

Native compiler input is explicit; these fixtures are developer inputs, not field
measurements or a claim of general program equivalence. This controller never
changes the compiler or relaxes its oracle after a failing result.
"""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import random
import subprocess
import time

R = Path(__file__).resolve().parents[2]
C = Path(os.environ['RF2_TEST_COMPILER']).resolve()
D = R / 'artifacts/function-reuse' / ('extended-' + str(time.time_ns()))
D.mkdir(parents=True)
CONTROLLER_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
SYNTAX_ONLY = os.environ.get('RF2_EXTENDED_SYNTAX_ONLY') == '1'
ROWS = []
SERIAL = 0
MASK = (1 << 64) - 1


def run(args, timeout=20):
    return subprocess.run([str(x) for x in args], capture_output=True,
                          timeout=timeout, env={'PATH': '/nonexistent'})


def observe(binary):
    q = run(['/usr/bin/codesign', '-s', '-', binary])
    assert q.returncode == 0, q.stderr
    q = run([binary], timeout=5)
    return q.returncode, q.stdout.hex(), q.stderr.hex()


def units(cache):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in cache.glob('*.fn') if p.is_file() and not p.is_symlink()}


def source(body, expected=0, args='7', params='x', declarations=''):
    return ('profile RF2_SYSTEM_A64_V1\n' + declarations +
            'fn work(' + params + ')\n' + body + '\nend\n' +
            'fn main(argc,argv)\n return work(' + args + ')!=' +
            str(expected & MASK) + '\nend\n')


def private(name):
    p = D / name
    p.mkdir(mode=0o700)
    return p


def pair(label, text, cache, *, hit=None, bad=False, unsafe=False,
         opt=True, compact=True, zero_exit=True, full_check=None,
         source_path=None, preserve_mtime=False):
    global SERIAL
    SERIAL += 1
    path = source_path or D / ('source-' + str(SERIAL) + '.rf2')
    old_stat = path.stat() if preserve_mtime and path.exists() else None
    if old_stat is not None:
        assert path.stat().st_size == len(text.encode()), (label, 'same-size control changed size')
    path.write_text(text)
    if old_stat is not None:
        os.utime(path, ns=(old_stat.st_atime_ns,old_stat.st_mtime_ns))
        assert path.stat().st_mtime_ns == old_stat.st_mtime_ns
    clean = D / ('clean-' + str(SERIAL))
    cached = D / ('cached-' + str(SERIAL))
    flags = (['--opt'] if opt else []) + (['--compact'] if compact else [])
    before = units(cache) if cache.is_dir() and not unsafe else None
    q = run([C, path, clean, *flags])
    if bad:
        assert q.returncode != 0 and not clean.exists(), (label, q.stderr)
    else:
        assert q.returncode == 0, (label, q.stderr)
    if SYNTAX_ONLY:
        ROWS.append({'case': label, 'outcome': 'clean-refusal' if bad else 'clean-compile-only'})
        return None
    p = run([C, path, cached, *flags, '--reuse-cache', cache])
    if bad or unsafe:
        assert p.returncode != 0 and not cached.exists(), (label, p.returncode, p.stderr)
        if bad and before is not None:
            assert units(cache) == before, (label, 'invalid source changed committed units')
        ROWS.append({'case': label, 'outcome': 'refused-invalid-source' if bad else 'refused-unsafe-cache'})
        return None
    assert p.returncode == 0, (label, p.returncode, p.stderr)
    assert cached.read_bytes() == clean.read_bytes(), (label, 'unsigned image differs from clean oracle')
    receipt = json.loads(Path(str(cached) + '.reuse.json').read_text())
    assert receipt['compilerSHA256'] == hashlib.sha256(C.read_bytes()).hexdigest(), (label, receipt)
    assert receipt['schema'] == 'rf2.function.reuse.v1', (label, receipt)
    assert all(type(receipt.get(k)) is int and receipt[k]>=0
               for k in ['reused','compiled','ineligible','validationReused','fullValidationChecks']), (label, receipt)
    assert receipt['validationReused'] == receipt['reused'], (label, receipt)
    assert receipt['fullValidationChecks'] >= receipt['compiled'], (label, receipt)
    if 'unitFormat' in receipt:
        assert receipt['unitFormat'] == 'RF2FN002', (label, receipt)
    if full_check is not None:
        assert (receipt['fullValidationChecks']>0) == full_check, (label, receipt)
    if hit is not None:
        assert (receipt['reused'] > 0) == hit, (label, receipt)
    unsigned_digest = hashlib.sha256(clean.read_bytes()).hexdigest()
    expected, actual = observe(clean), observe(cached)
    assert actual == expected, (label, expected, actual)
    if zero_exit:
        assert actual[0] == 0, (label, actual)
    ROWS.append({'case': label, 'outcome': 'clean-byte-and-execution-match',
                 'reuse': receipt, 'observation': actual,
                 'unsignedSHA256': unsigned_digest})
    return receipt


def both(label, text, *, admitted=True, opt=True, compact=True):
    cache = private('cache-' + str(len(list(D.glob('cache-*')))))
    pair(label + ' cold', text, cache, hit=False, opt=opt, compact=compact)
    pair(label + ' warm', text, cache, hit=admitted, opt=opt, compact=compact)
    return cache


def main():
    base = source(' let y=x+1\n set y=y*3\n return y', 24)
    main_cache = both('linear let and assignment', base)
    both('parameter assignment', source(' set x=x+9\n return x', 16))
    both('transitive local readiness', source(' let y=x\n let z=y+2\n set y=z*4\n return y', 36))
    both('unused initialized locals', source(' let a=1\n let b=2\n return x', 7))
    both('parameter copied through zero', source(' let value=0\n set value=x\n return value', 7))
    both('parenthesized assignments', source(' let y=(x+7)*(x-2)\n set y=(y^15)&255\n return y', 73))
    both('comments and blank lines', source(' # explain\n\n let y=x+1\n\n # explain again\n set y=y*3\n return y', 24))
    both('typed scalar spelling', source(' let y=x+1\n return y', 8, params='x:u64'))
    both('zero-parameter constant locals', source(' let y=8\n set y=y*2\n return y', 16, args='', params=''))
    both('two parameter dependencies', source(' let a=x+y\n let b=a*x\n set b=b-y\n return b', 61, args='7,2', params='x,y'))
    both('narrowed coalesced assignment', source(' let y=x\n set y=(y*3+7)&4294967295\n return y',4,args=str(MASK)))
    for depth in [55,63]:
        both('expression depth '+str(depth), source(' let y='+('('*depth)+'x'+(')'*depth)+'\n return y',7))
    for depth in [64,65]:
        pair('expression depth refuses '+str(depth),source(' let y='+('('*depth)+'x'+(')'*depth)+'\n return y',7),main_cache,bad=True)
    # Register-only and framed-local boundaries use the same result oracle.
    for count in [6, 7, 8, 16, 32, 128, 255]:
        body='\n'.join(' let v'+str(i)+'='+('x' if i==0 else 'v'+str(i-1)+'+1') for i in range(count))
        body+='\n return v'+str(count-1)
        both('local slot count '+str(count), source(body, 7+count-1))
    for opt,compact in [(False,True),(True,False),(False,False)]:
        both('lowering opt='+str(opt)+' compact='+str(compact),base,opt=opt,compact=compact)
    # Reproducible generated arithmetic programs have independent Python results.
    rng = random.Random(20261113029)
    for seed in range(24):
        value = [0,1,7,MASK,1<<63,rng.getrandbits(64)][seed%6]
        body=' let a=x\n'
        expected=value
        for step in range(5):
            op=['+','-','*','^','&','|','<<','>>','//'][(seed+step)%9]
            operand=rng.randrange(1,64) if op in ('<<','>>','//') else rng.getrandbits(32)
            body+=' set a=a'+op+str(operand)+'\n'
            expected={'+':lambda a,b:a+b,'-':lambda a,b:a-b,'*':lambda a,b:a*b,
                      '^':lambda a,b:a^b,'&':lambda a,b:a&b,'|':lambda a,b:a|b,
                      '<<':lambda a,b:a<<b,'>>':lambda a,b:a>>b,
                      '//':lambda a,b:a//b}[op](expected,operand)&MASK
        body+=' return a'
        both('independent arithmetic seed '+str(seed),source(body,expected,args=str(value)))
    # Semantically invalid changed bodies must never obtain a cached pass.
    bad_bodies = [
        ('read before declaration',' let a=b+1\n let b=x\n return a'),
        ('self read in initializer',' let y=y+1\n return y'),
        ('set before declaration',' set y=x\n let y=1\n return y'),
        ('unknown assignment',' set absent=x\n return x'),
        ('unknown read',' let y=absent+1\n return y'),
        ('duplicate let',' let y=x\n let y=2\n return y'),
        ('parameter redeclaration',' let x=2\n return x'),
        ('comparison chain',' let y=x<8<9\n return y'),
        ('missing assignment equals',' let y x+1\n return y'),
        ('empty initializer',' let y=\n return x'),
        ('missing return expression',' let y=x\n return'),
        ('assignment expression malformed',' let y=x\n set y=y+\n return y'),
        ('assignment field on scalar',' let y=x\n set y.bad=1\n return y'),
        ('assignment index on scalar',' let y=x\n set y[0]=1\n return y'),
        ('unknown intrinsic',' let y=never(x)\n return y'),
        ('missing end in branch',' let y=x\n if y>0\n set y=1\n return y'),
        ('branch local escapes',' if x>0\n let y=x\n end\n return y'),
    ]
    for label,body in bad_bodies:
        pair(label,source(body,0),main_cache,bad=True)
    pair('cache survives all invalid bodies',base,main_cache,hit=True)
    # Changed statement order, local names/counts and read dependencies rekey units.
    mutations=[('changed initializer',' let y=x+2\n set y=y*3\n return y',27),
               ('changed assigned expression',' let y=x+1\n set y=y*4\n return y',32),
               ('renamed local',' let value=x+1\n set value=value*3\n return value',24),
               ('add local',' let y=x+1\n let z=y\n set z=z*3\n return z',24),
               ('drop local',' return x*3+3',24),
               ('different dependency',' let y=x+1\n let z=x+2\n set y=z*3\n return y',27)]
    for label,body,expected in mutations:
        text=source(body,expected)
        pair(label+' cold',text,main_cache,hit=False)
        pair(label+' warm',text,main_cache,hit=True)
    pair('original linear template remains reusable',base,main_cache,hit=True)
    # Excluded effects must keep ordinary code generation and preserve behavior.
    fallback = [
        ('branch',' let y=x\n if x>4\n set y=y+3\n end\n return y',10),
        ('loop',' let y=0\n let i=0\n while i<x\n set y=y+2\n set i=i+1\n end\n return y',14),
        ('memory',' let p=buffer("work",8)\n do store64(p,x+3)\n return load64(p)',10),
        ('logical intrinsic',' let y=all(x,1)\n return y',1),
        ('unused do expression',' let y=x\n do y+1\n return y',7),
    ]
    for label,body,expected in fallback:both('fallback '+label,source(body,expected),admitted=False)
    arrays='array Values(u64,4)\n'
    both('fallback typed array',source(' let a=Values()\n set a[3]=x+1\n return a[3]',8,declarations=arrays),admitted=False)
    records='record Value(n:u64)\n'
    both('fallback typed record',source(' let a=Value(x)\n set a.n=x+2\n return a.n',9,declarations=records),admitted=False)
    # Changed raw source must not inherit a proof just because size/mtime/slot count match.
    raw_cache = private('raw-body-proof-cache')
    raw_path = D/'same-size-mtime.rf2'
    raw_valid = source(' let y=x+1\n let z=1\n return y',8)
    raw_invalid = raw_valid.replace('let y=x+1','let y=z+1')
    pair('raw source proof cold',raw_valid,raw_cache,hit=False,full_check=True,source_path=raw_path)
    pair('raw source proof warm',raw_valid,raw_cache,hit=True,full_check=False,source_path=raw_path,preserve_mtime=True)
    pair('same-size same-mtime same-slot invalid readiness refuses',raw_invalid,raw_cache,bad=True,source_path=raw_path,preserve_mtime=True)
    pair('raw source reversion reuses prior proof',raw_valid,raw_cache,hit=True,full_check=False,source_path=raw_path,preserve_mtime=True)
    # A cache miss must fully validate excluded effects even when capture shape alone
    # would permit one exit fixup and zero object registrations in the helper.
    pointer_read = ('profile RF2_SYSTEM_A64_V1\nfn work(p)\n let y=load64(p)\n set y=y+1\n return y\nend\n'
                    'fn main(argc,argv)\n let p=buffer("pointer",8)\n do store64(p,7)\n return work(p)!=8\nend\n')
    pointer_write = ('profile RF2_SYSTEM_A64_V1\nfn work(p,x)\n let y=x+1\n do store64(p,y)\n return y\nend\n'
                     'fn main(argc,argv)\n let p=buffer("pointer",8)\n let y=work(p,7)\n return (y!=8)|(load64(p)!=8)\nend\n')
    for label,text in [('raw pointer read',pointer_read),('raw pointer write',pointer_write)]:
        cache=private(label.replace(' ','-')+'-cache')
        pair(label+' proof miss',text,cache,hit=False,full_check=True)
        pair(label+' still uncached',text,cache,hit=False,full_check=True)
        assert not list(cache.glob('*.fn')), (label,'excluded helper published a semantic proof')
    # A previously checked pure helper remains usable while an earlier ineligible
    # function changes object effects, emitted length and current label numbering.
    effect = ('profile RF2_SYSTEM_A64_V1\nfn effect()\n let p=buffer("effect",8)\n do store64(p,3)\n return load64(p)\nend\n'
              'fn work(x)\n let y=x+1\n return y\nend\n'
              'fn main(argc,argv)\n return (work(7)!=8)|(effect()!=3)\nend\n')
    effect_cache=private('preceding-effect-cache')
    pair('preceding effect cold',effect,effect_cache,hit=False)
    pair('preceding effect pure helper warm',effect,effect_cache,hit=True)
    pair('preceding buffer size changes',effect.replace('"effect",8','"effect",80'),effect_cache,hit=True)
    larger=effect.replace(' do store64(p,3)',' let extra=1\n set extra=extra+1\n do store64(p,extra+1)')
    pair('preceding function code size changes',larger,effect_cache,hit=True)
    pair('preceding function result changes',effect.replace('store64(p,3)','store64(p,4)').replace('effect()!=3','effect()!=4'),effect_cache,hit=True)
    if not SYNTAX_ONLY:
        # Unit metadata now carries the checked current scalar-slot count.
        proof_cache=private('metadata-proof-cache')
        pair('semantic proof metadata cold',base,proof_cache,hit=False,full_check=True)
        pair('semantic proof metadata warm',base,proof_cache,hit=True,full_check=False)
        for label,recompute in [('local-count checksum corruption',False),('wrong local-count with recomputed digest',True)]:
            for entry in proof_cache.glob('*.fn'):
                data=bytearray(entry.read_bytes())
                assert data[:8]==b'RF2FN002' and len(data)>=104, 'unexpected unit format'
                old_count=int.from_bytes(data[96:104],'little')
                data[96:104]=(old_count+1).to_bytes(8,'little')
                if recompute:
                    n=int.from_bytes(data[72:80],'little')
                    assert len(data)==104+n
                    data[40:72]=hashlib.sha256(data[72:104+n]).digest()
                entry.write_bytes(data)
            pair(label,base,proof_cache,hit=False,full_check=True)
            pair(label+' repaired memoized proof',base,proof_cache,hit=True,full_check=False)
        for entry in proof_cache.glob('*.fn'):
            data=entry.read_bytes();entry.write_bytes(b'RF2FN001'+data[8:])
        pair('old unit format never carries a new semantic proof',base,proof_cache,hit=False,full_check=True)
        pair('new format restores proof reuse',base,proof_cache,hit=True,full_check=False)
        # Entry admission must be robust to ordinary filesystem corruption.
        for label,alter in [
            ('unit permissions repair',lambda p:p.chmod(0o644)),
            ('unit size repair',lambda p:p.write_bytes(b'x'*100000)),
            ('unit FIFO repair',lambda p:(p.unlink(),os.mkfifo(p))),
        ]:
            for p in main_cache.glob('*.fn'):alter(p)
            pair(label,base,main_cache,hit=False)
            pair(label+' warm after repair',base,main_cache,hit=True)
        outside=D/'outside-canary';outside.write_bytes(b'outside-is-unchanged')
        for p in main_cache.glob('*.fn'):p.unlink();p.symlink_to(outside)
        pair('unit final symlink replacement',base,main_cache,hit=False)
        assert outside.read_bytes()==b'outside-is-unchanged'
        pair('unit symlink repair now reusable',base,main_cache,hit=True)
        descriptor=os.open(main_cache,os.O_RDONLY)
        try:
            fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
            pair('busy linear cache refuses',base,main_cache,unsafe=True)
        finally:os.close(descriptor)
        pair('linear cache unlock recovers',base,main_cache,hit=True)
    result={'schema':'rf2.function.reuse.extended.verification.v1',
            'passed':True,'syntaxOnly':SYNTAX_ONLY,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),
            'controllerSHA256':CONTROLLER_SHA,'cases':ROWS,
            'limits':'Finite macOS ARM64 local compiler checks. Clean output bytes and execution are separate oracles. Generated arithmetic is developer test data, not application throughput, security proof or universal program compatibility.'}
    (D/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(D/'report.json'),'passed':True,'syntaxOnly':SYNTAX_ONLY,'cases':len(ROWS)}))


if __name__ == '__main__':main()
