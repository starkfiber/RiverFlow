"""Supplementary real descriptor faults, separate from the frozen authoring grade."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys


def run(study, destination):
    study, destination = Path(study).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError('Use a new evidence directory; retain prior probes.')
    destination.mkdir(parents=True)
    sample = destination / 'sample.txt'
    sample.write_text('banana தமிழ்\n')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    before = sha(sample)
    results = []
    for name in ('1-python', '2-rf2', '3-rf2', '4-python'):
        workspace = study / name
        launch = json.loads((workspace / 'launch.json').read_text())
        for kind in ('closed-reader-report', 'closed-descriptor-report', 'closed-descriptor-mcp'):
            arguments = ['mcp' if kind.endswith('mcp') else 'report', str(sample), 'ana']
            raw = b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}\n' if kind.endswith('mcp') else None
            if kind.startswith('closed-reader'):
                reader, writer = os.pipe()
                os.close(reader)
                try:
                    child = subprocess.run([*launch, *arguments], cwd=workspace, stdout=writer,
                                           stderr=subprocess.PIPE, input=raw, timeout=10)
                finally:
                    os.close(writer)
            else:
                child = subprocess.run([*launch, *arguments], cwd=workspace, stdout=None,
                                       stderr=subprocess.PIPE, input=raw, preexec_fn=lambda: os.close(1), timeout=10)
            entry = workspace / ('app' if launch == ['./app'] else 'app.py')
            results.append(dict(attempt=name, kind=kind, expectedExit=2, actualExit=child.returncode,
                                passed=child.returncode == 2, stderr=child.stderr.decode(errors='replace')[:1500],
                                entrySHA256=sha(entry)))
    assert sha(sample) == before
    report = dict(schema='rf2.passage-supplementary-output.v1', controllerSHA256=sha(Path(__file__)),
                  scope='Read-only fault probes after all original calls. Not part of the frozen80-check grader. No original app, grade or usage repaired.',
                  sampleSHA256=before, frozenTaskSHA256=sha(study / 'TASK.md'), results=results, inputUnchanged=True)
    (destination / 'RESULTS.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('output_faults.py COMPLETED-STUDY NEW-DIRECTORY')
    report = run(*sys.argv[1:])
    print(json.dumps(dict(cases=len(report['results']), passed=sum(r['passed'] for r in report['results']))))
