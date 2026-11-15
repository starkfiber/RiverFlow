"""Build an explicit native development archive from selected qualified local artifacts."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tarfile
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=6:raise SystemExit('Usage: package-typed-booking.py COMPILER GENERATED-COMPILER-SOURCE RUNTIME APP-BUILD NEW-DIRECTORY')
compiler,source,runtime,apps,destination=[Path(p).resolve()for p in sys.argv[1:]]
destination.mkdir(parents=True,exist_ok=False)
for name,p in [('rf2c',compiler),('rf2',runtime),*[(n,apps/n)for n in ('booking','booking-web','booking-agent')]]:
 subprocess.run(['/usr/bin/codesign','--verify',p],capture_output=True,check=True);shutil.copy2(p,destination/name);(destination/name).chmod(0o755)
shutil.copytree(apps/'source',destination/'source'/'booking');shutil.copy2(source,destination/'source'/'compiler.flow');shutil.copy2(R/'LICENSE',destination/'LICENSE');shutil.copy2(R/'experiments/typed-booking/tools.json',destination/'source'/'booking-tools.json')
(destination/'README.txt').write_text('''RiverFlow RF2 Booking 0.45 development edition. Apple Silicon macOS only.
Created by Ilangkhumanan Thirunavokkarasu. SFE. MIT licence.
Ad-hoc signed development binaries. No Developer ID signature or notarization.
Native programs need no Node, npm, Python or C++ runtime.
This bundle promotes the qualified bounded 0.44 owned-value compiler, not a
claim that every proposed type or platform exists. Stable 0.17 remains unchanged.

Run from this extracted directory, with your own new workspace path:
 ./booking /absolute/path/to/new-workspace.db init
 ./booking /absolute/path/to/new-workspace.db list
 ./booking-web /absolute/path/to/new-workspace.db
Open the printed private loopback URL in your browser. Stop with Ctrl+C.
The browser is the GUI; this is not an AppKit widget application.
This is local cooperative storage, not a public network reservation service.

Agent interface (stdio, read-only by default):
 ./booking-agent /absolute/path/to/existing-workspace.db
Write authority must be chosen explicitly at launch by adding --write.
Tools: booking_list, and with --write, booking_reserve/booking_cancel.
One selected journal only. No tool accepts a path, network URL or source code.
Current 2026-07-28 per-request metadata and legacy 2025-11-25 initialization
are supported. Read current data before retrying an uncertain mutation.
The separate ./rf2 mcp retains its nine bounded Core/capability tools.

Rebuild without another language runtime (development requires OS codesign):
 ./rf2c source/compiler.flow /new/path/rf2c --opt
 /usr/bin/codesign -s - /new/path/rf2c
 ./rf2c source/booking/main.flow /new/path/booking --opt
 /usr/bin/codesign -s - /new/path/booking
Replace main.flow with web.flow or agent.flow for the other frontends.
Output paths must be new; compiling does not launch the result.

Bounds: 16 rooms, 256 current reservations, 1 MiB journal, same-day intervals.
Dates have no timezone conversion. Journal SHA-256 is an unkeyed integrity
check, not authentication. Version1 compatibility data belongs to this new
codec and does not import the older Workbench RF2BOOK1 event format.
Explicit migration/recovery are available via CLI and GUI, not agent tools.
A full corrupt snapshot is never silently removed. Back up your files.
No speed, energy, AI productivity, hardware, security-proof or learner-study
claim follows from this development package.
Docs: https://github.com/starkfiber/RiverFlow/blob/main/docs/TYPED-BOOKING-0.45.md
''')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=dict(edition='0.45.0-dev',target='macos-arm64',compilerSourceSHA256=digest(source),runtimeContract='0.17 nine existing bounded tools; separate Booking server',packagerSHA256=digest(Path(__file__)),files={str(p.relative_to(destination)):dict(bytes=p.stat().st_size,sha256=digest(p))for p in sorted(destination.rglob('*'))if p.is_file()})
(destination/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n');archive=destination.with_name(destination.name+'.tar.gz')
with tarfile.open(archive,'x:gz')as f:f.add(destination,arcname=destination.name)
archive.with_name(archive.name+'.sha256').write_text(digest(archive)+'  '+archive.name+'\n')
print(json.dumps(dict(archive=str(archive),sha256=digest(archive),files=len(m['files']))))
