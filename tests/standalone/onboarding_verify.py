"""Exercise the native first-app journey; Python is independent developer tooling."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import os
import random
import select
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
URL = ('https://raw.githubusercontent.com/starkfiber/RiverFlow/'
       '28b65ea9053925d98611bcda4b9818726c4239d9/'
       'dist/0.36-candidate/RF2-0.36-dev-macos-arm64.zip')
ZIP_SHA = 'a07f2f7ac7e4895171b7c6a178c9c6817427e76379bf2c6a26e9da40213d0f1d'
OUT = Path(tempfile.mkdtemp(prefix='onboarding-', dir=ROOT / 'artifacts'))
ROWS = []
TRANSCRIPT = []


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check(name, ok, details=None):
    ROWS.append(dict(name=name, passed=bool(ok), details=details))
    (OUT / 'progress.json').write_text(json.dumps(ROWS, indent=2) + '\n')
    assert ok, (name, details)


def run(args, data=b'', env=None, cwd=ROOT):
    return subprocess.run(list(map(str, args)), input=data, capture_output=True,
                          timeout=20, cwd=cwd, env=env)


archive = OUT / 'bundle.zip'
archive.write_bytes(urllib.request.urlopen(URL, timeout=45).read())
check('pinned-public-download', digest(archive) == ZIP_SHA)
extracted = OUT / 'native tools'
p = run(['/usr/bin/ditto', '-x', '-k', archive, extracted])
check('native-fresh-extraction', p.returncode == 0, p.stderr.decode())
BUNDLE = extracted / 'RF2-0.36-dev-macos-arm64'
manifest = json.loads((BUNDLE / 'MANIFEST.json').read_text())
for name, entry in manifest['files'].items():
    check('manifest:' + name, digest(BUNDLE / name) == entry['sha256'])
env = dict(os.environ, RF2_HOME=str(BUNDLE))
empty_env = dict(os.environ)
empty_env.pop('RF2_HOME', None)
HELPER = ROOT / 'tools/dev.sh'


def dev(*args, data=b'', environment=env, cwd=ROOT):
    return run(['/bin/sh', HELPER, *args], data, environment, cwd)


check('help-without-bundle', dev('--help', environment=empty_env).returncode == 0)
for name, args in [
        ('missing-bundle', ['doctor']),
        ('unknown-command', ['invent']),
        ('missing-home-value', ['--home']),
        ('missing-check-source', ['check']),
        ('extra-status-argument', ['status', 'extra']),
        ('extra-doctor-argument', ['doctor', 'extra']),
        ('extra-mcp-argument', ['mcp', 'extra']),
        ('missing-build-output', ['build', 'source.flow']),
        ('bad-build-flag', ['build', 'source.flow', 'new', '--surprise']),
        ('missing-firmware-prefix', ['firmware', 'source.flow'])]:
    check(name, dev(*args, environment=empty_env).returncode == 2)
check('missing-bundle-directory', dev('--home', OUT / 'absent', 'doctor').returncode == 2)
missing = OUT / 'empty bundle'
missing.mkdir()
check('missing-compiler', dev('--home', missing, 'doctor').returncode == 2)
bad = OUT / 'invalid tools'
bad.mkdir()
(bad / 'rf2c').write_text('not a native compiler\n')
(bad / 'rf2c').chmod(0o700)
check('bad-signature-refused', dev('--home', bad, 'doctor').returncode == 2)
p = dev('doctor')
check('doctor-real-tools-spaced-path', p.returncode == 0 and b'0.17.0' in p.stdout, p.stderr.decode())
p = dev('doctor', environment=dict(env, PATH='/nonexistent'))
check('doctor-without-language-toolchain-path', p.returncode == 0, p.stderr.decode())
p = dev('--home', BUNDLE, 'status', environment=dict(env, RF2_HOME=str(missing)))
check('explicit-home-overrides-environment', p.returncode == 0 and json.loads(p.stdout)['version'] == '0.17.0')
relative = os.path.relpath(BUNDLE, OUT)
p = dev('status', environment=dict(env, RF2_HOME=relative), cwd=OUT)
check('relative-bundle-path', p.returncode == 0)

summary = ROOT / 'examples/collection-tools/telemetry-summary.flow'
frequency = ROOT / 'examples/collection-tools/value-frequency.flow'
check_dir = OUT / 'check only'
check_dir.mkdir()
before = sorted(check_dir.iterdir())
p = dev('check', summary, cwd=check_dir)
check('check-without-image', p.returncode == 0 and sorted(check_dir.iterdir()) == before, p.stderr.decode())
invalid = OUT / 'invalid.flow'
invalid.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return missing_name\nend\n')
check('source-error-visible', dev('check', invalid).returncode != 0)
check('missing-source-visible', dev('check', OUT / 'missing.flow').returncode != 0)

builds = {}
for name, source in [('summary', summary), ('frequency', frequency)]:
    folder = OUT / (name + ' build')
    p = dev('build', source, folder, '--opt')
    check('build-' + name, p.returncode == 0, p.stderr.decode())
    builds[name] = folder / 'program'
    check('signature-' + name, run(['/usr/bin/codesign', '--verify', builds[name]]).returncode == 0)
    original = digest(builds[name])
    check('existing-output-refused-' + name, dev('build', source, folder).returncode != 0 and digest(builds[name]) == original)
    link = OUT / (name + '-link')
    link.symlink_to(folder, target_is_directory=True)
    check('symlink-output-refused-' + name, dev('build', source, link).returncode != 0 and digest(builds[name]) == original)

probe = OUT / 'print probe.flow'
probe.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n do write(1,"APP_EXECUTED\\n",13)\n return 9\nend\n')
p = dev('build', probe, OUT / 'probe build')
check('build-does-not-execute', p.returncode == 0 and b'APP_EXECUTED' not in p.stdout, p.stderr.decode())
p = run([OUT / 'probe build/program'])
check('explicit-execution-separate', p.returncode == 9 and p.stdout == b'APP_EXECUTED\n')
p = dev('build', probe, OUT / 'minimal path build', environment=dict(env, PATH='/nonexistent'))
check('build-without-language-toolchain-path', p.returncode == 0, p.stderr.decode())

rng = random.Random(20261115)
for i in range(20):
    values = [9, 1, 9, 3, 2] if i == 0 else [rng.randrange(100000) for _ in range(rng.randrange(1,500))]
    data = ','.join(map(str, values)).encode()
    p = run([builds['summary']], data)
    ordered = sorted(values)
    expected = dict(count=len(values), minimum=min(values), maximum=max(values), sum=sum(values), median_lower=ordered[(len(values)-1)//2])
    check('summary-oracle-' + str(i), p.returncode == 0 and json.loads(p.stdout) == expected)
    p = run([builds['frequency']], data)
    counts = collections.Counter(values)
    expected = dict(count=len(values), unique=len(counts), frequencies=[dict(value=v, count=counts[v]) for v in sorted(counts)])
    check('frequency-oracle-' + str(i), p.returncode == 0 and json.loads(p.stdout) == expected)
for name, executable in builds.items():
    for i, data in enumerate([b'9,,3', b'-1', b'01', b'1,', b'18446744073709551616']):
        p = run([executable], data)
        check('invalid-input-' + name + '-' + str(i), p.returncode == 1 and p.stdout == b'' and b'Error ' in p.stderr)
p = run([builds['summary']], b'9,,3')
check('tutorial-exact-error', p.returncode == 1 and p.stderr == b'Error 22\n')
p = run([builds['summary']], b'18446744073709551615,1')
check('checked-sum-overflow', p.returncode == 1 and not p.stdout)

prefix = OUT / 'new firmware'
p = dev('firmware', ROOT / 'examples/esp32c3/interrupt-heartbeat.flow', prefix)
check('firmware-without-flash', p.returncode == 0, p.stderr.decode())
for suffix in ['elf', 'bin', 'map']:
    path = Path(str(prefix) + '.' + suffix)
    check('firmware-equality-' + suffix, path.read_bytes() == (BUNDLE / ('firmware/interrupt-heartbeat.' + suffix)).read_bytes())
original = Path(str(prefix) + '.bin').read_bytes()
check('existing-firmware-refused', dev('firmware', ROOT / 'examples/esp32c3/interrupt-heartbeat.flow', prefix).returncode != 0 and Path(str(prefix) + '.bin').read_bytes() == original)

proc = subprocess.Popen(['/bin/sh', str(HELPER), 'mcp'], cwd=ROOT, env=env,
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def request(n, method, params):
    value = dict(jsonrpc='2.0', id=n, method=method, params=params)
    proc.stdin.write(json.dumps(value).encode() + b'\n')
    proc.stdin.flush()
    assert select.select([proc.stdout], [], [], 5)[0], 'MCP timeout'
    result = json.loads(proc.stdout.readline())
    assert result.get('id') == n, result
    TRANSCRIPT.append(dict(request=value, response=result))
    return result


try:
    request(1, 'initialize', dict(protocolVersion='2024-11-05', capabilities={}, clientInfo=dict(name='onboarding-test', version='1')))
    proc.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
    proc.stdin.flush()
    tools = request(2, 'tools/list', {})['result']['tools']
    check('mcp-nine-tools', len(tools) == 9)
    for i, (source, data, error, expected) in enumerate([
            ('rf2 v1 checked\nsum input', [1,2,3], False, 6),
            ('rf2 v1 checked\nsum input', [4294967295,1], True, None),
            ('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return 0\nend\n', [], True, None),
            ('rf2 v1 checked\nsum input', [4,5], False, 9)]):
        result = request(3+i, 'tools/call', dict(name='rf2_run', arguments=dict(source=source, data=data)))['result']
        check('mcp-boundary-' + str(i), result.get('isError', False) == error and (error or result['structuredContent']['value'] == expected))
finally:
    proc.stdin.close()
    proc.wait(timeout=5)
check('mcp-process-clean-exit', proc.returncode == 0)
check('published-tools-unchanged', all(digest(BUNDLE / n) == manifest['files'][n]['sha256'] for n in ['rf2', 'rf2c', 'rf2-esp32c3']))
report = dict(schema='rf2.onboarding.v1', passed=True, checks=len(ROWS),
              checkedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT).decode().strip(),
              sourceWorkingTree='onboarding changes under review; controller/helper hashes identify tested changes',
              packageURL=URL, packageSHA256=ZIP_SHA, manifestFiles=len(manifest['files']),
              helperSHA256=digest(HELPER), controllerSHA256=digest(Path(__file__)),
              compilerSHA256=digest(BUNDLE / 'rf2c'), runtimeSHA256=digest(BUNDLE / 'rf2'),
              hardwareTested=False, firmwareEmulatedThisRun=False,
              scope='Fresh package and native developer journey; no speed, AI usage, learning or physical hardware measurement.',
              rows=ROWS)
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
(OUT / 'mcp.json').write_text(json.dumps(TRANSCRIPT, indent=2) + '\n')
print(json.dumps(dict(passed=True, checks=len(ROWS), report=str(OUT / 'report.json'))))
