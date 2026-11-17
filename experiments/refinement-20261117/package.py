"""Compose an explicit experimental source SDK; never replace a release/default."""
from pathlib import Path
import argparse, hashlib, importlib.util, json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PINS = {
    'serializer/json_spans.flow': '8bb2ab48faceed5934ee2d6f676d14a6a7ffe5769dd2740ac9acceaf84532abe',
    '../evolution-20261117/report/report.flow': '8f272ebf7604989be3844267c0adc283295acdae34839079ba609a9f80c37ba8',
    '../acceptance-20261117/ai/text-report-cli.flow': '7d4e4c2cef46bfccf78ed6d8cb0f1db9456f7ec87ac651723c1228e0ef52b1a9',
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def safe_destination(destination):
    destination = destination.resolve()
    for name in ['sdk/v1', 'native/compiler', 'dist', 'bin', 'plugin', '.codex-plugin', 'site/downloads']:
        protected = (ROOT / name).resolve()
        if destination == protected or protected in destination.parents:
            raise ValueError('Experimental output cannot enter protected source/release tree: ' + name)
    return destination

def create(destination):
    destination = safe_destination(destination)
    for name, expected in PINS.items():
        if sha(HERE / name) != expected:
            raise ValueError('Reviewed source changed: ' + name)
    source = ROOT / 'sdk/v1'
    rows = (source / 'rf2-sdk.manifest').read_text().splitlines()
    if rows[0] != 'rf2-sdk-v1':
        raise ValueError('Unsupported SDK manifest')
    entries = [line.split(' ', 1) for line in rows[1:] if line]
    for expected, name in entries:
        if Path(name).name != name or sha(source / name) != expected:
            raise ValueError('Baseline SDK identity mismatch: ' + name)
    spec = importlib.util.spec_from_file_location('reviewed_r5_stage', HERE / 'serializer/stage_sdk.py')
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    destination = stage.stage(destination)
    additions = {
        'report.flow': HERE / '../evolution-20261117/report/report.flow',
        'text-report-cli.flow': HERE / '../acceptance-20261117/ai/text-report-cli.flow',
    }
    for name, path in additions.items():
        (destination / name).write_bytes(path.read_bytes())
    names = [name for _, name in entries] + list(additions)
    provenance = {
        'schema': 'rf2.refinement.experimental-sdk.v1',
        'edition': '0.50D-R5-experimental',
        'stableChanged': False,
        'defaultSDKChanged': False,
        'performancePromotionGranted': False,
        'scope': 'Explicit experiment, not a replacement for the accepted R3 source package. Consult the once-only R5 campaign and all failed gates.',
        'inputs': {str((HERE / name).resolve().relative_to(ROOT)): value for name, value in PINS.items()},
        'files': [{'path': name, 'sha256': sha(destination / name)} for name in names],
        'limits': ['Trusted synchronous Systems callback; no sandbox or reentrancy guarantee', 'No universal speed or AI-token saving claim', 'Mac ARM64 qualification only'],
    }
    (destination / 'PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (destination / 'rf2-sdk.manifest').write_text('rf2-sdk-v1\n' + ''.join(f'{sha(destination / name)} {name}\n' for name in names))
    return destination

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(create(args.destination))
