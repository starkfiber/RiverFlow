"""Package supplied, qualified native Documents tools; no downloads or publishing."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) != 7:
    raise SystemExit('Usage: package-documents.py RF2C RUNTIME WORKSPACE TEXT-LINES TEST-REPORT NEW-DIRECTORY')
compiler, runtime, workspace, lines, report_path, destination = [Path(p).resolve() for p in sys.argv[1:]]
report = json.loads(report_path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert report['passed'] is True
assert sha(compiler) == report['compilerSHA256']
assert sha(workspace) == report['binaries']['opt']['workspace']
assert sha(lines) == report['binaries']['opt']['lines']
for name, expected in report['sources'].items():
    assert sha(ROOT / name) == expected, name
assert not any(p.is_symlink() for p in (ROOT / 'examples/documents').rglob('*'))
destination.mkdir(parents=True, exist_ok=False)
for name, path in [('rf2c', compiler), ('rf2', runtime), ('workspace', workspace), ('text-lines', lines)]:
    subprocess.run(['/usr/bin/codesign', '--verify', str(path)], check=True)
    shutil.copy2(path, destination / name)
shutil.copy2(ROOT / 'LICENSE', destination / 'LICENSE')
shutil.copytree(ROOT / 'examples/documents', destination / 'examples/documents',
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
(destination / 'tools').mkdir()
for name in ['dev.sh', 'build-program.sh']:
    shutil.copy2(ROOT / 'tools' / name, destination / 'tools' / name)
(destination / 'README.txt').write_text('''RF2 Documents 0.37 development bundle
Created by Ilangkhumanan Thirunavokkarasu. Published by SFE. MIT licence.
Host: Apple Silicon macOS. Ad-hoc signed, not notarized.
No Node/npm/Python/C++ user runtime is required.

From this extracted folder:
./workspace examples/documents/fixtures/documents.txt --serve
Open the printed local URL. Stop in Terminal with Ctrl+C.
The included texts are programming examples. To read your own files, put one
literal path per line in a UTF-8 manifest, then name it instead of the example list.
Relative paths resolve from the current Terminal directory, not the manifest folder.
Files are read-only, strict UTF-8; final-component symlinks and nonregular files refuse.
Limits: 64 documents, 64 KiB each, 1 MiB total; query 256 UTF-8 bytes.
The snapshot lives in memory; restart to reload changes. No PDF/DOCX extraction,
edits, persistent index, watched updates, accounts or collaboration is included.
The local listener is not authenticated against other processes on this Mac.

./workspace examples/documents/fixtures/documents.txt --catalog
./text-lines examples/documents/fixtures/tamil.txt தமிழ்
./rf2 status
./rf2 mcp

The unchanged native runtime reports 0.17.0 and exposes the same nine bounded tools.
The included Mac compiler is the previously qualified 0.36-bundle compiler.
Version 0.37 identifies these new libraries/application/package, not a new backend.
No embedded compiler, device operation, flash capability or new MCP authority is added.

To rebuild the application from included RF2 source:
export RF2_HOME="$PWD"
sh tools/dev.sh build examples/documents/workspace.flow rebuilt-workspace --opt
./rebuilt-workspace/program examples/documents/fixtures/documents.txt --catalog

Source documentation links assume the full source repository. Current guide:
https://github.com/starkfiber/RiverFlow/tree/main/examples/documents
Tests use independent developer tooling; they are not user runtime dependencies.
No new speed, energy, AI-token or independent security-certification claim.
''')
manifest = dict(version='0.37.0-dev', product='RF2 Documents', host='macos-arm64',
                compilerSHA256=sha(compiler), runtimeSHA256=sha(runtime),
                testReportSHA256=sha(report_path), packagerSHA256=sha(Path(__file__)),
                files={str(p.relative_to(destination)): dict(bytes=p.stat().st_size, sha256=sha(p))
                       for p in sorted(destination.rglob('*')) if p.is_file()})
(destination / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
archive = destination.parent / (destination.name + '.zip')
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as output:
    for path in sorted(destination.rglob('*')):
        if path.is_file():
            output.write(path, str(Path(destination.name) / path.relative_to(destination)))
print(json.dumps(dict(passed=True, archive=str(archive), sha256=sha(archive), files=len(manifest['files']))))
