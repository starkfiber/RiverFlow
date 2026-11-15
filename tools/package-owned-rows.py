"""Package the explicitly selected native 0.46 candidate and its reproducible sources."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tarfile
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=7:raise SystemExit('Usage: package-owned-rows.py COMPILER COMPILER-SOURCE RUNTIME BOOKING-BUILD CATALOG-BUILD NEW-DIRECTORY')
compiler,source,runtime,apps,catalog,destination=[Path(p).resolve()for p in sys.argv[1:]]
destination.mkdir(parents=True,exist_ok=False)
selected=[('rf2c',compiler),('rf2',runtime),('rf2-labels',catalog/'rf2-labels'),*[(n,apps/n)for n in('booking','booking-web','booking-agent')]]
for name,p in selected:
 subprocess.run(['/usr/bin/codesign','--verify',p],capture_output=True,check=True);shutil.copy2(p,destination/name);(destination/name).chmod(0o755)
shutil.copytree(apps/'source',destination/'source/booking');shutil.copytree(catalog/'source',destination/'source/catalog');shutil.copy2(source,destination/'source/compiler.flow');shutil.copy2(R/'LICENSE',destination/'LICENSE');shutil.copy2(R/'experiments/typed-booking/tools.json',destination/'source/booking-tools.json')
(destination/'README.txt').write_text('''RiverFlow RF2 0.46 development candidate. SFE. MIT licence.
Apple Silicon macOS only. Ad-hoc signed; not Developer ID signed or notarized.
All included user programs are native. No Node/npm/Python/C++ runtime required.
The unchanged rf2 runtime retains version0.17 and its nine bounded MCP tools.
The experimental rf2c adds owned structured rows to the 0.44 compiler.
The prior0.45 and stable0.17 downloads are preserved unchanged.

 ./rf2-labels 'Jitra' 'தமிழ்' 'Hello'
Creates a JSON label manifest on stdout after validating every input.
Limits:64 labels,256 Unicode scalar values/1024 UTF-8 bytes per label.
Scalars are not graphemes; scalar_sum is an arithmetic summary, not a hash.
Input errors produce no JSON. Output failure can leave a written prefix.

 ./booking /absolute/path/to/new.db init
 ./booking /absolute/path/to/new.db list
 ./booking-web /absolute/path/to/new.db
Open the printed private loopback URL. Stop with Ctrl+C.
 ./booking-agent /absolute/path/to/existing.db
Agent defaults to read-only. Add --write only for explicit mutation authority.
No source/path/network/init/migrate/recover tool is admitted by that server.
Original ./rf2 mcp is separate and unchanged.

Booking limits:16 rooms,256 current rows,1MiB append-only snapshot journal.
The journal budget can fill before256 consecutive reservations.
Same-day minute intervals; no timezone conversion or public server claim.
SHA-256 is an unkeyed integrity check, not authentication.
Storage uses cooperative file locking; it is not hostile same-user isolation.
Version1/2 are new Booking-specific codecs, not a Workbench journal importer.

Rebuild using explicit new output paths and macOS code signing:
 ./rf2c source/compiler.flow /new/path/program --opt
 /usr/bin/codesign -s - /new/path/program
 ./rf2c source/booking/main.flow /new/path/booking --opt
 /usr/bin/codesign -s - /new/path/booking
Use web.flow and agent.flow for the other Booking frontends.
 ./rf2c source/catalog/main.flow /new/path/rf2-labels --opt
 /usr/bin/codesign -s - /new/path/rf2-labels
Compilation does not automatically run the output.

Owned rows support consuming rows_push and caller-owned rows_take results,
reserve/clear and recursive cleanup. Failed insertion consumes the source's
static binding; runtime ownership remains for scope cleanup if no transfer
occurred. Failed recursive cleanup quarantines row access until clear/release
succeeds. Persistent OS refusal can retain mappings until process exit.
Limits:acyclic declared types,255 inline row words,65536 collection words,
256 local slots and16 cleanup registrations per function. Raw Systems code
can bypass checked invariants. No universal safety, portability, runtime speed,
AI productivity, hardware, human usability or GitHub language acceptance claim.
Docs: https://github.com/starkfiber/RiverFlow/blob/main/docs/OWNED-ROWS-0.46.md
''')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=dict(edition='0.46.0-dev',target='macos-arm64',compilerSourceSHA256=digest(source),runtimeContract='unchanged0.17 nine bounded tools; separate Booking agent',packagerSHA256=digest(Path(__file__)),files={str(p.relative_to(destination)):dict(bytes=p.stat().st_size,sha256=digest(p))for p in sorted(destination.rglob('*'))if p.is_file()})
(destination/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');archive=destination.with_name(destination.name+'.tar.gz')
with tarfile.open(archive,'x:gz')as f:f.add(destination,arcname=destination.name)
archive.with_name(archive.name+'.sha256').write_text(digest(archive)+'  '+archive.name+'\n');print(json.dumps(dict(archive=str(archive),sha256=digest(archive),files=len(manifest['files']))))
