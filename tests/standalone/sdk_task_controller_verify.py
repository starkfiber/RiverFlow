"""Failure-retention controls for the authoring controller; no model calls."""
from pathlib import Path
import importlib.util
import json
import tempfile

R = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('rf2_sdk_task_controller', R / 'experiments/sdk-task/run.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checks = []


def check(name, passed):
    checks.append(dict(name=name, passed=bool(passed)))
    assert passed, name


with tempfile.TemporaryDirectory(prefix='rf2-controller-') as temporary:
    root = Path(temporary)
    work = root / 'work'
    work.mkdir()
    protected = work / 'TASK.md'
    protected.write_text('fixed task')
    pinned = {'TASK.md': module.sha(protected)}
    check('matching source intact', module.integrity(work, pinned, {}, 'python') == (True, []))
    protected.unlink()
    intact, issues = module.integrity(work, pinned, {}, 'python')
    check('deleted protected file recorded without exception', not intact and bool(issues))
    protected.write_text('modified task')
    check('modified task refused', not module.integrity(work, pinned, {}, 'python')[0])
    outside = root / 'outside'
    outside.write_text('not eligible for source inventory')
    protected.unlink()
    protected.symlink_to(outside)
    check('protected symlink refused', not module.integrity(work, pinned, {}, 'python')[0])
    (work / 'other-link').symlink_to(root, target_is_directory=True)
    inventory_issues = []
    inventory = module.files(work, inventory_issues)
    check('source inventory excludes symlink files and directories', not inventory and len(inventory_issues) == 2)
    protected.unlink()
    (work / 'other-link').unlink()
    sdk = work / 'sdk'
    sdk.mkdir()
    (sdk / 'text.flow').write_text('module fixed')
    package = module.files(sdk)
    check('matching package intact', module.integrity(work, {}, package, 'rf2') == (True, []))
    (sdk / 'text.flow').unlink()
    check('deleted package module retained as failed input', not module.integrity(work, {}, package, 'rf2')[0])
    (sdk / '__pycache__').mkdir()
    (sdk / '__pycache__/ignored.pyc').write_bytes(b'bytecode')
    check('derived bytecode excluded from immutable package source map', module.files(sdk) == {})
print(json.dumps(dict(checks=len(checks), allPassed=all(x['passed'] for x in checks), results=checks)))
