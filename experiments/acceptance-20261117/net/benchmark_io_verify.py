"""Check prepared benchmark framing independently; no timing or product changes."""
from pathlib import Path
import argparse, ast, hashlib, json, struct, subprocess, time

H = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main(prepared, out):
    out.mkdir(parents=True, exist_ok=False)
    (out / 'RUNNER.py').write_bytes(Path(__file__).read_bytes())
    manifest = json.loads((prepared / 'PREPARED.json').read_text())
    ns = {'struct': struct, 'hashlib': hashlib, 'SERVER': 0x0a4d0002, 'BASE': 0x0a4d0064}
    oracle = H / 'snapshot/dhcp/verify.py'
    for node in ast.parse(oracle.read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in ['packet', 'Oracle']:
            exec(compile(ast.Module([node], type_ignores=[]), str(oracle), 'exec'), ns)
    cases = []
    for size in [244, 300, 576]:
        packet = ns['packet'](xid=123)[:size].ljust(size, b'\0')
        code, meta = ns['Oracle']().parse(packet)
        expected = struct.pack('<Q', code if code else meta[0] + meta[1] + meta[5])
        wire = struct.pack('<QH', 1, size) + packet
        for fragments in [None, [1], [9, 1, 7, 3]]:
            cases.append((f'valid-{size}-{fragments}', wire, fragments, 0, expected))
    good = struct.pack('<QH', 1, 300) + ns['packet'](xid=123)
    for size in [0, 1, 9, 10, 309]:
        cases.append((f'early-eof-{size}', good[:size], [1, 3], 2, b''))
    for name, wire in [
        ('extra-byte', good + b'\0'),
        ('max-extra-byte', struct.pack('<QH', 1, 576) + ns['packet'](xid=123).ljust(576, b'\0') + b'\0'),
        ('oversize-length', struct.pack('<QH', 1, 577) + b'\0' * 577),
        ('zero-repetitions', struct.pack('<QH', 0, 300) + ns['packet']()),
        ('too-many-repetitions', struct.pack('<QH', 100000001, 300) + ns['packet']()),
    ]:
        cases.append((name, wire, [7, 2], 2, b''))
    results = []
    for probe in manifest['probes']:
        assert sha(probe['binary']) == probe['binarySHA256']
        for name, wire, fragments, code, expected in cases:
            p = subprocess.Popen([probe['binary']], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if fragments is None:
                stdout, stderr = p.communicate(wire, timeout=5)
            else:
                offset = 0
                try:
                    index = 0
                    while offset < len(wire):
                        n = fragments[index % len(fragments)]
                        p.stdin.write(wire[offset:offset+n]); p.stdin.flush()
                        offset += n; index += 1
                        time.sleep(0.0001)
                    p.stdin.close(); p.stdin = None
                except BrokenPipeError:
                    p.stdin = None
                stdout, stderr = p.communicate(timeout=5)
            passed = p.returncode == code and stdout == expected
            row = {'family': probe['family'], 'variant': probe['variant'], 'mode': probe['mode'], 'case': name,
                   'inputSHA256': hashlib.sha256(wire).hexdigest(), 'returncode': p.returncode, 'passed': passed}
            results.append(row)
            if not passed:
                (out / 'failure-input.bin').write_bytes(wire)
                (out / 'failure-stdout.bin').write_bytes(stdout)
                (out / 'failure-stderr.bin').write_bytes(stderr)
                (out / 'RESULTS.json').write_text(json.dumps({'completed': False, 'rows': results}, indent=2))
                raise AssertionError(row)
    result = {'completed': True, 'allPassed': True, 'casesPerProbe': len(cases), 'probes': len(manifest['probes']),
              'controllerSHA256': sha(Path(__file__)), 'preparedSHA256': sha(prepared / 'PREPARED.json'), 'rows': results}
    (out / 'RESULTS.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--prepared', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    main(args.prepared.resolve(), args.out.resolve())
