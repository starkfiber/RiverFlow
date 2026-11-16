"""Freeze and execute one bounded four-attempt real-provider construction study.

Reviewed inputs only; no app repairs, inference proxy, installs or publication.
Raw traces stay under ignored project-owned artifacts.
"""
from pathlib import Path
import hashlib
import json
import os
import platform
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

R = Path(__file__).resolve().parents[2]
S = R / 'experiments/sdk-task'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def files(root, issues=None):
    result = {}
    issues = [] if issues is None else issues
    for base, directories, names in os.walk(root):
        kept = []
        for name in sorted(directories):
            p = Path(base) / name
            if p.is_symlink():
                target = os.path.abspath(os.path.join(str(p.parent), os.readlink(p)))
                kind = 'symlink directory:' if os.path.commonpath([str(root), target]) == str(root) else 'out-of-root symlink directory:'
                issues.append(kind + str(p.relative_to(root)))
            elif name != '__pycache__':
                kept.append(name)
        directories[:] = kept
        for name in sorted(names):
            p = Path(base) / name
            if p.is_symlink():
                target = os.path.abspath(os.path.join(str(p.parent), os.readlink(p)))
                kind = 'symlink file:' if os.path.commonpath([str(root), target]) == str(root) else 'out-of-root symlink file:'
                issues.append(kind + str(p.relative_to(root)))
                continue
            try:
                if p.is_file():
                    result[str(p.relative_to(root))] = sha(p)
                elif stat.S_ISFIFO(p.lstat().st_mode):
                    issues.append('excluded FIFO fixture:' + str(p.relative_to(root)))
                else:
                    issues.append('nonregular artifact:' + str(p.relative_to(root)))
            except OSError as exc:
                issues.append(type(exc).__name__ + ':' + str(p.relative_to(root)))
    return result


def integrity(workspace, protected, package_hashes, arm):
    issues = []
    for name, digest in protected.items():
        path = workspace / name
        try:
            if path.is_symlink() or not path.is_file() or sha(path) != digest:
                issues.append('changed or missing:' + name)
        except OSError as exc:
            issues.append(type(exc).__name__ + ':' + name)
    if arm == 'rf2' and files(workspace / 'sdk', issues) != package_hashes:
        issues.append('SDK package changed or missing')
    return not issues, issues


def execute(compiler, package, sdk_guide, output, resume=False):
    compiler, package, sdk_guide, output = map(lambda p: Path(p).resolve(), (compiler, package, sdk_guide, output))
    if output.exists() and not resume:
        raise SystemExit('Use a new study directory; completed attempts are never rerun.')
    if not compiler.is_file() or not package.is_dir() or not sdk_guide.is_file():
        raise SystemExit('Qualified compiler, package and RF2 guide are required.')
    cli = shutil.which('codex')
    if not cli:
        raise SystemExit('Installed Codex CLI required; no download/fallback.')
    if shutil.disk_usage(R).free < 4 * 1024**3:
        raise SystemExit('Less than 4 GiB free; no authoring calls started.')
    if resume:
        manifest = json.loads((output / 'RESULTS.json').read_text())
        frozen = json.loads((output / 'FROZEN.json').read_text())
        assert subprocess.check_output([cli, '--version'], text=True).strip() == frozen['cli'], 'CLI identity changed'
        assert sys.version == frozen['python'], 'Controller Python identity changed'
        frozen_files = frozen['frozenSHA256']
        completed = len(manifest['trials'])
        assert 0 < completed < len(frozen['order']), 'Only unfinished original attempt slots may resume'
        assert not manifest.get('resumed'), 'One explicit interrupted-study continuation only'
        assert [t['arm'] for t in manifest['trials']] == frozen['order'][:completed]
        assert all(t['attempt'] == n for n, t in enumerate(manifest['trials'], 1))
        intact, issues = integrity(output, frozen_files, {}, 'controller')
        assert intact, issues
        assert sha(compiler) == sha(output / 'rf2c')
        assert files(package) == files(output / 'sdk')
        assert sha(sdk_guide) == sha(output / 'SDK-RF2.md')
        assert manifest['stopReason'] and all(t['immutableInputsIntact'] for t in manifest['trials'])
        for n in range(completed + 1, len(frozen['order']) + 1):
            assert not (output / f'{n}-{frozen["order"][n-1]}').exists(), 'Never overwrite or replace an attempt'
        # Preserve the actual stop and code. This is an explicit controller
        # correction, not an uninterrupted original four-call experiment.
        previous = output / 'STOPPED-BEFORE-RESUME.json'
        if not previous.exists():
            shutil.copy2(output / 'RESULTS.json', previous)
        amendment = dict(schema='rf2.passage-controller-amendment.v1',
                         originalFrozenSHA256=sha(output / 'FROZEN.json'), stoppedReportSHA256=sha(previous),
                         controllerSHA256=sha(Path(__file__)), preservedAttempts=completed,
                         remainingOriginalSlots=list(range(completed + 1, len(frozen['order']) + 1)),
                         correction='Skip and record nonregular/symlink self-test artifacts without following them. Protected task/SDK/compiler integrity still fails closed. No grader, SDK, task, model, budget, order or completed result changes.',
                         limitation='The four attempts were interrupted by a reviewed controller correction. They are not an uninterrupted preregistered execution; no replacement calls or repaired original scores.')
        assert not (output / 'AMENDMENT.json').exists()
        (output / 'AMENDMENT.json').write_text(json.dumps(amendment, indent=2) + '\n')
        manifest['priorStopReason'] = manifest.pop('stopReason')
        manifest['resumed'] = amendment
        order = manifest['order'][completed:]
        start = completed + 1
    else:
        output.mkdir(parents=True)
        for name in ('TASK.md', 'PROTOCOL.md', 'grade.py', 'text_sdk.py', 'SDK-PYTHON.md'):
            shutil.copy2(S / name, output / name)
        shutil.copy2(R / 'experiments/app-effort/mcp_sdk.py', output / 'mcp_sdk.py')
        shutil.copy2(sdk_guide, output / 'SDK-RF2.md')
        shutil.copy2(compiler, output / 'rf2c')
        shutil.copytree(package, output / 'sdk')
        shutil.copy2(Path(__file__), output / 'CONTROLLER.py')
        frozen_files = files(output)
        manifest = dict(schema='rf2.passage-construction.v1', protocol='PROTOCOL.md',
                    baseRevision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip(),
                    host=platform.platform(), python=sys.version, pythonExecutable=sys.executable,
                    cli=subprocess.check_output([cli, '--version'], text=True).strip(),
                    requestedModel='gpt-6.1-sol', requestedReasoningEffort='low',
                    servedModelIdentity='not inferred; only emitted identity is evidence',
                    order=['python', 'rf2', 'rf2', 'python'], secondsPerAttempt=600,
                    expectedGradeChecks=80, frozenSHA256=frozen_files,
                    constructionScope='Warm-SDK complete app composition. Timed author reads/writes/own compile/sign/self-tests; excludes prior SDK/compiler development and external grading.',
                        trials=[])
        (output / 'FROZEN.json').write_text(json.dumps(manifest, indent=2) + '\n')
        (output / 'grades').mkdir()
        order = manifest['order']
        start = 1
    print(json.dumps(dict(directory=str(output), frozenSHA256=sha(output / 'FROZEN.json'))), flush=True)
    for number, arm in enumerate(order, start):
        if shutil.disk_usage(R).free < 4 * 1024**3:
            manifest['stopReason'] = 'less than4GiB free before next attempt'
            break
        workspace = output / f'{number}-{arm}'
        workspace.mkdir()
        shutil.copy2(output / 'TASK.md', workspace / 'TASK.md')
        protected = ['TASK.md', 'SDK.md']
        if arm == 'rf2':
            shutil.copy2(output / 'rf2c', workspace / 'rf2c')
            shutil.copytree(output / 'sdk', workspace / 'sdk')
            shutil.copy2(output / 'SDK-RF2.md', workspace / 'SDK.md')
            protected += ['rf2c']
        else:
            for name in ('text_sdk.py', 'mcp_sdk.py'):
                shutil.copy2(output / name, workspace / name)
                protected.append(name)
            shutil.copy2(output / 'SDK-PYTHON.md', workspace / 'SDK.md')
        (workspace / 'AGENTS.md').write_text(
            'Isolated Passage Desk authoring attempt. Work only here. Read TASK.md and SDK.md. '
            'No other workspaces, prior attempts, grader, auth files, remote calls, installs, delegation, '
            'GitHub writes, Memory or shared compute. Do not edit task, SDK guide or supplied helpers/package/compiler. '
            'Use targeted source inspection; at most150lines per read unless more context is necessary and explained. '
            'Preserve failures. Deliver source, tests, launch.json and README. No invented results.\n')
        immutable = {name: sha(workspace / name) for name in protected}
        package_hashes = files(workspace / 'sdk') if arm == 'rf2' else {}
        language = 'RF2' if arm == 'rf2' else 'Python'
        prompt = (f'Build Passage Desk in {language} according to TASK.md and SDK.md. Implement the complete application, '
                  'test its actual commands, and deliver launch.json and README.md. Use the supplied warm helpers but write '
                  'your own application entry/report/HTML renderer. Work autonomously only in this directory; no remote '
                  'services, installs, delegation, other workspace access or external grader. Do not edit TASK.md, SDK.md, '
                  'supplied libraries/packages/compiler. Targeted contract reads and batched checks are encouraged. '
                  'You have one600second attempt; preserve failures and disclose limits. Do not claim unseen grader results.')
        (workspace / 'PROMPT.txt').write_text(prompt + '\n')
        command = [cli, 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check', '--json',
                   '--sandbox', 'workspace-write', '--model', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="low"',
                   '-c', 'approval_policy="never"', '-C', str(workspace), '-']
        started = time.monotonic()
        timed_out = False
        with (workspace / 'TRACE.jsonl').open('wb') as stdout, (workspace / 'STDERR.txt').open('wb') as stderr:
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, start_new_session=True)
            child.stdin.write(prompt.encode())
            child.stdin.close()
            try:
                code = child.wait(timeout=600)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    code = child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    code = child.wait()
        elapsed = time.monotonic() - started
        events, parse_errors = [], 0
        for line in (workspace / 'TRACE.jsonl').read_text(errors='replace').splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                parse_errors += 1
        usages = [e['usage'] for e in events if isinstance(e.get('usage'), dict)]
        commands = [e['item'] for e in events if e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'command_execution']
        intact, integrity_issues = integrity(workspace, immutable, package_hashes, arm)
        grade_path = output / 'grades' / f'{number}-{arm}.json'
        try:
            grade_run = subprocess.run([sys.executable, str(output / 'grade.py'), str(workspace), str(grade_path)],
                                       cwd=R, capture_output=True, timeout=240)
            grade_exit = grade_run.returncode
            (output / 'grades' / f'{number}-{arm}.log').write_bytes(grade_run.stdout + grade_run.stderr)
        except subprocess.TimeoutExpired:
            grade_exit = 'timeout'
        grade = None
        if grade_exit == 0 and grade_path.is_file() and not grade_path.is_symlink():
            try:
                proposed = json.loads(grade_path.read_text())
                if proposed.get('schema') == 'rf2.passage-grade.v1' and proposed.get('checks') == 80 and len(proposed.get('results', [])) == 80:
                    grade = proposed
            except (ValueError, OSError):
                pass
        after_intact, after_issues = integrity(workspace, immutable, package_hashes, arm)
        intact = intact and after_intact
        integrity_issues.extend(after_issues)
        inventory_issues = []
        source_files = files(workspace, inventory_issues)
        result = dict(attempt=number, arm=arm, exit=code, timedOut=timed_out, seconds=elapsed,
                      providerReportedUsage=usages, usageAvailable=bool(usages), JSONLErrors=parse_errors,
                      completedCommands=len(commands), immutableInputsIntact=intact, integrityIssues=integrity_issues,
                      inventoryIssues=inventory_issues, packageSHA256=package_hashes,
                      sourceSHA256={k: v for k, v in source_files.items() if Path(k).suffix in ('.flow', '.rf2', '.py', '.md')},
                      traceSHA256=sha(workspace / 'TRACE.jsonl'), promptSHA256=sha(workspace / 'PROMPT.txt'),
                      graderExit=grade_exit, graderPath=str(grade_path), grade=grade, humanRepairs=0)
        manifest['trials'].append(result)
        (output / 'RESULTS.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(json.dumps({k: result[k] for k in ('attempt', 'arm', 'exit', 'timedOut', 'seconds', 'providerReportedUsage', 'immutableInputsIntact')} |
                         dict(gradePassed=grade.get('passed') if grade else None, gradeChecks=grade.get('checks') if grade else None)), flush=True)
        benign = ('symlink directory:', 'symlink file:', 'excluded FIFO fixture:')
        unsafe_inventory = [issue for issue in inventory_issues if not issue.startswith(benign)]
        if not intact or unsafe_inventory or not events or not usages or parse_errors or grade is None:
            manifest['stopReason'] = 'input integrity, controller or provider failure; no substitute attempt'
            break
    manifest['frozenInputsIntact'], manifest['frozenIntegrityIssues'] = integrity(output, frozen_files, {}, 'controller')
    (output / 'RESULTS.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(results=str(output / 'RESULTS.json'), trials=len(manifest['trials']))), flush=True)


if __name__ == '__main__':
    if len(sys.argv) not in (5, 6) or (len(sys.argv) == 6 and sys.argv[5] != '--resume'):
        raise SystemExit('run.py QUALIFIED-COMPILER QUALIFIED-SDK RF2-GUIDE DIRECTORY [--resume]')
    execute(*sys.argv[1:5], resume=len(sys.argv) == 6)
