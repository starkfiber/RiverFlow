"""Prepare the combined 0.50 SDK/diagnostics candidate without altering old sources."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile

R = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('Use a new directory')
    sdk = load('rf2_sdk_prepare', R / 'experiments/sdk-packages/prepare.py')
    diagnostics = load('rf2_diagnostics_prepare', R / 'experiments/diagnostics-050/prepare.py')
    with tempfile.TemporaryDirectory(prefix='rf2-sdk-composed-base-') as temporary:
        base = Path(temporary) / 'base'
        subprocess.run([sys.executable, str(R / 'experiments/typed-requests/prepare.py'), str(base)],
                       check=True, capture_output=True)
        source = (base / 'compiler.flow').read_text()
    sha = lambda value: hashlib.sha256(value).hexdigest()
    baseline = sha(source.encode())
    assert baseline == '39f4944fa001397cf4977322d89f322316ee21f5105cbe3d75bdddd886820009'
    source = diagnostics.apply_bounds(source)
    source = sdk.apply(source)
    source = diagnostics.apply(source)
    destination.mkdir(parents=True)
    (destination / 'compiler.flow').write_text(source)
    inputs = [R / 'experiments/typed-requests/prepare.py', R / 'experiments/sdk-packages/prepare.py',
              R / 'experiments/sdk-packages/sdk.flow', R / 'experiments/diagnostics-050/prepare.py',
              R / 'experiments/diagnostics-050/diagnostics.flow', Path(__file__)]
    record = dict(schema='rf2.sdk-composed-source.v1', baselineSourceSHA256=baseline,
                  sourceSHA256=sha(source.encode()), inputs={str(p.relative_to(R)): sha(p.read_bytes()) for p in inputs},
                  order=['0.49 exact source', 'inventoried function bounds', 'explicit SDK roots', 'native diagnostics'])
    (destination / 'SOURCE.json').write_text(json.dumps(record, indent=2) + '\n')
    return destination


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('compose.py NEW-DIRECTORY')
    print(prepare(sys.argv[1]))
