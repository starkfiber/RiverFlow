"""Reproduce the exact 0.50 native source candidate from an explicit public0.46 compiler.

Development tooling only. No download, package installation or compiler fallback.
Failed builds keep their new output directory and logs for inspection.
"""
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[2]
BASELINE_SHA256 = '2ea72481993820e264c356325380fb01e225d4f4d5ec144a8023228d7c37ac3b'
SOURCE_SHA256 = '5ec6f9f43d1f76e838cb4485f7f6b60dcc0319c8d381e15541a4f14552b76c82'
PROGRAM_SHA256 = '4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(baseline, destination):
    baseline = Path(baseline).resolve(strict=True)
    destination = Path(destination).resolve()
    if sha(baseline) != BASELINE_SHA256:
        raise ValueError('Selected baseline is not the qualified public0.46 native compiler; no fallback was attempted')
    if destination.exists():
        raise ValueError('Use a new output directory; existing evidence is never overwritten')
    if sys.platform != 'darwin' or platform.machine() != 'arm64':
        raise ValueError('This reproduction is qualified only on macOS ARM64')
    destination.mkdir(parents=True)
    record = dict(schema='rf2.sdk-native-build.v1', status='building',
                  baselineCompilerSHA256=sha(baseline), baselineCompiler=str(baseline),
                  sourceExpectedSHA256=SOURCE_SHA256, programExpectedSHA256=PROGRAM_SHA256,
                  buildFlags=['--compact', '--opt'], steps=[], host=platform.platform(),
                  python=sys.version, buildToolSHA256=sha(Path(__file__)),
                  limits='Development source preparation uses Python. Resulting compiler/app runtime is native. Ad-hoc signing, not publisher notarization; no downloads or implicit fallback.')
    report = destination / 'BUILD.json'

    def save():
        report.write_text(json.dumps(record, indent=2) + '\n')

    def run(label, command):
        started = time.monotonic()
        stdout = destination / (label + '.stdout')
        stderr = destination / (label + '.stderr')
        try:
            q = subprocess.run([str(x) for x in command], cwd=R, capture_output=True, timeout=60)
        except subprocess.TimeoutExpired as error:
            stdout.write_bytes(error.stdout or b'')
            stderr.write_bytes(error.stderr or b'')
            record['steps'].append(dict(label=label, command=[str(x) for x in command],
                                        exit='timeout', timedOut=True, timeoutSeconds=60,
                                        seconds=time.monotonic() - started,
                                        stdoutSHA256=sha(stdout), stderrSHA256=sha(stderr)))
            save()
            raise
        stdout.write_bytes(q.stdout)
        stderr.write_bytes(q.stderr)
        record['steps'].append(dict(label=label, command=[str(x) for x in command],
                                    exit=q.returncode, seconds=time.monotonic() - started,
                                    stdoutSHA256=sha(stdout), stderrSHA256=sha(stderr)))
        save()
        if q.returncode:
            raise RuntimeError('Failed build step: ' + label + '; inspect retained logs')

    save()
    try:
        bridge = destination / 'bridge'
        run('bridge', [sys.executable, R / 'experiments/diagnostics-050/bootstrap.py', baseline, bridge])
        source = destination / 'source'
        run('source', [sys.executable, R / 'experiments/sdk-packages/compose.py', source])
        compiler_source = source / 'compiler.flow'
        record['sourceSHA256'] = sha(compiler_source)
        if record['sourceSHA256'] != SOURCE_SHA256:
            raise ValueError('Composed source changed; review the edition instead of silently rebuilding a different compiler')
        (destination / 'SOURCES.json').write_bytes((source / 'SOURCE.json').read_bytes())
        program = destination / 'program'
        run('compile', [bridge / 'program', compiler_source, program, '--compact', '--opt'])
        run('sign', ['/usr/bin/codesign', '-s', '-', program])
        run('verify-signature', ['/usr/bin/codesign', '--verify', program])
        record['programSHA256'] = sha(program)
        if record['programSHA256'] != PROGRAM_SHA256:
            raise ValueError('Native program differs from the qualified source candidate; inspect retained logs')
        self_dir = destination / 'self'
        self_dir.mkdir()
        self_program = self_dir / 'program'
        run('self-compile', [program, compiler_source, self_program, '--compact', '--opt'])
        run('self-sign', ['/usr/bin/codesign', '-s', '-', self_program])
        record['selfSHA256'] = sha(self_program)
        if record['selfSHA256'] != record['programSHA256']:
            raise ValueError('Signed self-generation mismatch with matching flags')
        record['status'] = 'passed'
        record['selfGenerationMatched'] = True
        save()
        return destination
    except BaseException as error:
        record['status'] = 'failed'
        record['failure'] = type(error).__name__ + ': ' + str(error)
        save()
        raise


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: build.py PUBLIC-046-NATIVE-COMPILER NEW-DIRECTORY')
    print(build(sys.argv[1], sys.argv[2]))
