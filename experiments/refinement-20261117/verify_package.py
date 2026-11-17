"""Check the experimental composition against independent complete-task oracles."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, subprocess, tempfile, time

HERE = Path(__file__).resolve().parent
COMPILER_SHA = '92d7546234a6fe4baa2408d2a79009f67798d0739c64a9c2a2a6f07edfc2d429'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify(args):
    if sha(args.compiler) != COMPILER_SHA:
        raise ValueError('Use the qualified source-context diagnostic compiler')
    if not os.environ.get('TMPDIR', '').startswith('/Volumes/Mac Work Cache/'):
        raise ValueError('Use the guarded disposable runner for reproducible binaries')
    args.out.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('refinement_package', HERE / 'package.py')
    package = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(package)
    sdk = package.create(args.out / 'sdk')
    images = Path(tempfile.mkdtemp(prefix='rf2-refinement-compose-', dir=os.environ['TMPDIR']))
    result = {'schema': 'rf2.refinement.composition.v1', 'compilerSHA256': sha(args.compiler),
              'packageBuilderSHA256': sha(HERE / 'package.py'), 'verifierSHA256': sha(__file__),
              'oracleSHA256': sha(HERE / 'ai/grade.py'), 'runs': [], 'allPassed': False,
              'performanceClaim': False, 'stableChanged': False}
    destination = args.out / 'RESULTS.json'
    def save():
        destination.write_text(json.dumps(result, indent=2) + '\n')
    for task in ['C', 'D']:
        for condition in ['manual', 'cli']:
            source = HERE / f'ai/golden-{task}-{condition}.flow'
            for mode in ['plain', 'opt']:
                label = f'{task}-{condition}-{mode}'
                logs = args.out / label
                logs.mkdir()
                binary = images / label
                command = [str(args.compiler.resolve()), str(source), str(binary), '--compact',
                           '--sdk-root', str(sdk), '--diagnostic-json']
                if mode == 'opt':
                    command.append('--opt')
                start = time.monotonic()
                built = subprocess.run(command, capture_output=True, timeout=30)
                (logs / 'compile.stdout').write_bytes(built.stdout)
                (logs / 'compile.stderr').write_bytes(built.stderr)
                row = {'label': label, 'sourceSHA256': sha(source), 'compileExit': built.returncode,
                       'passed': False}
                result['runs'].append(row)
                save()
                if built.returncode == 0:
                    subprocess.run(['codesign', '-s', '-', str(binary)], capture_output=True, check=True, timeout=10)
                    row['binarySHA256'] = sha(binary)
                    graded = subprocess.run(['python3', '-B', str(HERE / 'ai/grade.py'), task,
                                             '--binary', str(binary), '--out', str(logs / 'grade')],
                                            capture_output=True, timeout=180)
                    (logs / 'grade.stdout').write_bytes(graded.stdout)
                    (logs / 'grade.stderr').write_bytes(graded.stderr)
                    receipt = logs / 'grade/RESULTS.json'
                    row['gradeExit'] = graded.returncode
                    if receipt.exists():
                        outcome = json.loads(receipt.read_text())
                        row.update(passed=outcome['allPassed'] and graded.returncode == 0,
                                   checksPassed=outcome['passed'], checksTotal=outcome['total'],
                                   receiptSHA256=sha(receipt))
                row['seconds'] = time.monotonic() - start
                save()
    result['allPassed'] = len(result['runs']) == 8 and all(row['passed'] for row in result['runs'])
    result['complete'] = True
    save()
    print(json.dumps({'receipt': str(destination), 'allPassed': result['allPassed'],
                      'checksPassed': sum(r.get('checksPassed', 0) for r in result['runs'])}))
    if not result['allPassed']:
        raise SystemExit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    verify(parser.parse_args())
