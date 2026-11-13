"""Explicit development bundle; no stable-release mutation or network operations."""
from pathlib import Path
import hashlib,json,os,platform,shutil,subprocess,sys,zipfile
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=5:raise SystemExit('Usage: package-foundation.py qualified-compiler qualified-runtime qualified-search NEW-directory')
C,RT,APP,OUT=map(lambda x:Path(x).resolve(),sys.argv[1:]);OUT.mkdir(parents=True,exist_ok=False)
for name,p in [('rf2c',C),('rf2',RT),('text-search',APP)]:
 subprocess.run(['/usr/bin/codesign','--verify',p],check=True,capture_output=True);shutil.copy2(p,OUT/name)
(OUT/'source').mkdir();shutil.copy2(R/'native/compiler/compiler.rf2',OUT/'source/compiler.rf2');shutil.copy2(R/'LICENSE',OUT/'LICENSE')
shutil.copytree(R/'examples/text-search',OUT/'examples/text-search')
(OUT/'examples/hello.rf2').write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return (20+22)!=42\nend\n')
(OUT/'README.txt').write_text('''RF2 0.31 development bundle: Apple Silicon macOS only\n\nDevelopment candidate, not a stable release, signed with local ad-hoc signatures.\nNot Apple-notarized. Follow your normal OS security review; do not bypass warnings.\nThese native programs require no Node, npm, Python or C++ runtime.\n\nFrom this folder:\n ./rf2 status\n ./rf2c --check examples/hello.rf2\n ./rf2c examples/hello.rf2 new-hello --opt --compact\n codesign -s - new-hello\n ./new-hello\n printf banana | ./text-search ana --overlap\n ./rf2 mcp\n\nThe hello program exits0; the search returns two overlapping matches.\nMCP retains the stable0.17 runtime contract and nine bounded tools. Compiler source\nis development0.31; these are separate version identities. There is no embedded AI\nmodel or raw systems-code execution over MCP. Systems compilation is trusted.\n\nSearch limits:1MiB stdin,128-byte query, byte matching rather than Unicode words.\nCheck-only validates but does not run source or prove its runtime correctness.\nSignature/manifest hashes identify bytes, not external certification.\n\nSource, test controllers, exact measurements and remaining gaps:\n https://github.com/starkfiber/RiverFlow/blob/main/docs/FOUNDATION-0.31.md\n\nCreated by Ilangkhumanan Thirunavokkarasu. Published by SFE. MIT licence.\n''')
# Fresh disposable exercise within the exact bundle, with developer runtimes absent.
work=OUT/'smoke';work.mkdir();env={'PATH':'/nonexistent'}
def run(args,data=None):
 q=subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=30,env=env,cwd=work);assert q.returncode==0,(args,q.stderr);return q
assert json.loads(run([OUT/'rf2','status']).stdout)['version']=='0.17.0'
assert run([OUT/'rf2c','--check',OUT/'examples/hello.rf2']).stdout==b'RF2 source checked; no executable written.\n'
image=work/'hello';run([OUT/'rf2c',OUT/'examples/hello.rf2',image,'--opt','--compact']);run(['/usr/bin/codesign','-s','-',image]);run([image]);image.unlink()
assert json.loads(run([OUT/'text-search','ana','--overlap'],b'banana').stdout)==dict(bytes=6,query_bytes=3,matches=2,first_byte=1)
assert not list(work.iterdir());work.rmdir()
manifest=dict(schema='rf2.development.bundle.v1',version='0.31.0-dev',host=platform.platform(),target='macos-arm64',runtimeContract='0.17.0 nine bounded tools',compilerSourceSHA256=hashlib.sha256((OUT/'source/compiler.rf2').read_bytes()).hexdigest(),packagerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),nativeSmokePassed=True,files={str(p.relative_to(OUT)):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)for p in sorted(OUT.rglob('*'))if p.is_file()},limits='Development Apple Silicon Mac bundle; ad-hoc signed, not notarized. No universal language, security, portability, AI usage or speed guarantee.')
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');archive=OUT.parent/(OUT.name+'.zip')
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED)as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,str(Path(OUT.name)/p.relative_to(OUT)))
print(json.dumps(dict(bundle=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,smokePassed=True)))
