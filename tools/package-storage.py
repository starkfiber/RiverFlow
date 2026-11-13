"""Explicit RF2 0.32 development bundle; native binaries are supplied, never downloaded."""
from pathlib import Path
import hashlib,json,subprocess,shutil,sys,zipfile
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=6:raise SystemExit('Usage: package-storage.py COMPILER RUNTIME TEXT-SEARCH LOG-SCAN NEW-DIRECTORY')
C,RT,T,L,D=[Path(x).resolve()for x in sys.argv[1:]];D.mkdir(parents=True,exist_ok=False)
for name,src in [('rf2c',C),('rf2',RT),('text-search',T),('log-scan',L)]:
 subprocess.run(['/usr/bin/codesign','--verify',src],check=True,capture_output=True);shutil.copy2(src,D/name)
shutil.copy2(R/'LICENSE',D/'LICENSE');shutil.copytree(R/'examples/text-search',D/'examples/search-tools');(D/'source').mkdir();shutil.copy2(R/'native/compiler/compiler.rf2',D/'source/compiler.rf2')
(D/'README.txt').write_text('''RF2 0.32 development candidate. Apple Silicon macOS only.\nAd-hoc signed, not notarized; use normal OS security review.\nStable release remains unchanged. Native programs need no Node/npm/Python runtime.\n\n./rf2 status\n./rf2c --check examples/search-tools/main.rf2\nprintf banana | ./text-search ana --overlap\nprintf 'WARN retry\\nINFO ready\\n' | ./log-scan WARN\n./rf2 mcp\n\nBoth applications import examples/search-tools/lib/search.rf2.\nTo compile a fresh app, use rf2c SOURCE NEW-OUTPUT --opt --compact,\nthen apply normal macOS codesign -s - NEW-OUTPUT before execution.\nQuery limit4096bytes, stdin1MiB. Byte matching, not Unicode normalization.\nNew arrays have separate frame storage, not an unbounded heap or thread model.\nRuntime retains0.17 contract/nine bounded tools; compiler source is development0.32.\nNo embedded AI or raw systems execution over MCP.\nSource, tests and limits: https://github.com/starkfiber/RiverFlow/blob/main/docs/STRUCTURED-STORAGE-0.32.md\nCreated by Ilangkhumanan Thirunavokkarasu. Published by SFE. MIT licence.\n''')
def run(args,data=None):
 q=subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=30,env={'PATH':'/nonexistent'});assert q.returncode==0,(args,q.stderr);return q
assert json.loads(run([D/'rf2','status']).stdout)['version']=='0.17.0'
run([D/'rf2c','--check',D/'examples/search-tools/main.rf2']);run([D/'rf2c','--check',D/'examples/search-tools/log-scan.rf2'])
assert json.loads(run([D/'text-search','ana','--overlap'],b'banana').stdout)['matches']==2
observed=json.loads(run([D/'log-scan','WARN'],b'WARN retry\nINFO ready\n').stdout)
assert observed==dict(bytes=22,query_bytes=4,lines=2,matching_lines=1,matches=1,first_line=1),observed
manifest=dict(version='0.32.0-dev',target='macos-arm64',runtimeContract='0.17 nine bounded tools',smokePassed=True,logSmoke=observed,packagerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),files={str(p.relative_to(D)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(D.rglob('*'))if p.is_file()},limits='Same-Mac development smoke; ad-hoc signed, not notarized, no whole-language safety, portability, concurrency, speed or AI productivity claim.')
(D/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');z=D.parent/(D.name+'.zip')
with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED)as out:
 for p in sorted(D.rglob('*')):
  if p.is_file():out.write(p,str(Path(D.name)/p.relative_to(D)))
print(json.dumps(dict(zip=str(z),bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest(),passed=True)))
