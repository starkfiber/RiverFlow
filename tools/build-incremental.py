"""Explicit development build of the native RF2 target-cache driver; no runtime Python."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=3:raise SystemExit('Usage: build-incremental.py qualified-rf2c new-output-directory')
compiler=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True)
text=(R/'native/compiler/compiler.rf2').read_text();names=['state','die','require','length','same','cp','digit','letter','identifier_end','module_state','module_info','module_path','line_end','line_trim','line_starts','module_path_check','module_append','module_walk','expand_modules']
parts=[]
for name in names:
 m=re.search(r'^fn '+name+r'\(',text,re.M);assert m,name;n=re.search(r'^fn ',text[m.end():],re.M);parts.append(text[m.start():m.end()+n.start()]if n else text[m.start():])
sha=(R/'examples/evidence-contract/lib/sha256.rf2').read_text().split('\n',1)[1];driver=(R/'native/build/incremental.rf2').read_text();source='profile RF2_SYSTEM_A64_V1\n'+''.join(parts)+sha+driver;identity=hashlib.sha256(source.encode()).hexdigest();source+='\nfn builder_identity()\n return "'+identity+'"\nend\n';p=out/'driver.rf2';p.write_text(source);exe=out/'rf2-build';subprocess.run([compiler,p,exe,'--opt'],check=True);subprocess.run(['/usr/bin/codesign','-s','-',exe],check=True);subprocess.run(['/usr/bin/codesign','--verify',exe],check=True)
report={'schema':'rf2.incremental.build.v1','builderIdentity':identity,'buildScriptSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'compilerSHA256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest(),'extractedCompilerFunctions':names,'extractSourceSHA256':hashlib.sha256(text.encode()).hexdigest(),'shaLibrarySHA256':hashlib.sha256(sha.encode()).hexdigest(),'target':'macos-arm64','runtimeDependencies':'Native RF2 executable and explicitly selected native compiler; normal Darwin APIs. No Python/Node runtime.'};(out/'BUILD.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
