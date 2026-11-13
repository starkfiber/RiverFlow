"""Explicit native 0.33 development bundle; supplied binaries only, no downloads."""
from pathlib import Path
import hashlib,json,subprocess,shutil,sys,zipfile
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=6:raise SystemExit('Usage: package-heap.py COMPILER RUNTIME SUMMARY FREQUENCY NEW-DIRECTORY')
C,RT,S,F,D=[Path(x).resolve()for x in sys.argv[1:]];D.mkdir(parents=True,exist_ok=False)
for name,src in [('rf2c',C),('rf2',RT),('telemetry-summary',S),('value-frequency',F)]:
 subprocess.run(['/usr/bin/codesign','--verify',src],check=True,capture_output=True);shutil.copy2(src,D/name)
shutil.copy2(R/'LICENSE',D/'LICENSE');shutil.copytree(R/'examples/collection-tools',D/'examples/collection-tools');(D/'source').mkdir();shutil.copy2(R/'native/compiler/compiler.rf2',D/'source/compiler.rf2')
(D/'README.txt').write_text('''RF2 0.33 development candidate. Apple Silicon macOS only.
Ad-hoc signed, not notarized; use normal OS security review.
Stable release unchanged. Native programs require no Node/npm/Python runtime.

./rf2 status
./rf2c --check examples/collection-tools/telemetry-summary.flow
printf '9,1,9,3,2' | ./telemetry-summary
printf '9,1,9,3,2' | ./value-frequency
./rf2 mcp

Both .flow apps share examples/collection-tools/lib/numbers.rf2 and output.rf2.
To compile: rf2c SOURCE NEW-OUTPUT --opt --compact
Then apply normal macOS codesign -s - NEW-OUTPUT before execution.
Input: canonical unsigned decimal integers, ASCII whitespace/comma separators,
1MiB stdin, 65536 values. Summary uses checked u64 sum and lower median.
Output numeric JSON requires an integer-aware consumer for full u64 precision.
Collections relocate heap storage; local checked moves and typed mutable borrows.
No owner returns, concurrency, arbitrary raw-pointer safety or infallible cleanup.
Runtime retains0.17 contract/nine bounded MCP tools; compiler development0.33.
No embedded AI, raw systems over MCP, ESP32 or Arduino firmware support.
Source/tests/limits: https://github.com/starkfiber/RiverFlow/blob/main/docs/HEAP-COLLECTIONS-0.33.md
Created by Ilangkhumanan Thirunavokkarasu. Published by SFE. MIT licence.
''')
def run(args,data=None):
 q=subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=30,env={'PATH':'/nonexistent'});assert q.returncode==0,(args,q.stderr);return q
assert json.loads(run([D/'rf2','status']).stdout)['version']=='0.17.0'
for name in ['telemetry-summary','value-frequency']:run([D/'rf2c','--check',D/f'examples/collection-tools/{name}.flow'])
summary=json.loads(run([D/'telemetry-summary'],b'9,1,9,3,2').stdout)
assert summary==dict(count=5,minimum=1,maximum=9,sum=24,median_lower=3),summary
frequency=json.loads(run([D/'value-frequency'],b'9,1,9,3,2').stdout)
assert frequency==dict(count=5,unique=4,frequencies=[dict(value=v,count=n)for v,n in [(1,1),(2,1),(3,1),(9,2)]]),frequency
manifest=dict(version='0.33.0-dev',target='macos-arm64',runtimeContract='0.17 nine bounded tools',smokePassed=True,summary=summary,frequency=frequency,packagerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),files={str(p.relative_to(D)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(D.rglob('*'))if p.is_file()},limits='Same-Mac development smoke; ad-hoc signed, not notarized. No embedded target, whole-language safety, concurrency, speed or AI productivity claim.')
(D/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');z=D.parent/(D.name+'.zip')
with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED)as out:
 for p in sorted(D.rglob('*')):
  if p.is_file():out.write(p,str(Path(D.name)/p.relative_to(D)))
print(json.dumps(dict(zip=str(z),bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest(),passed=True)))
