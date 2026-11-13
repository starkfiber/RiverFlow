"""Build the native RF2-written RV32IM/ESP32-C3 crosscompiler.
Python only assembles reviewed RF2 source and invokes the existing native host
compiler. It emits no target instructions, ELF objects or Espressif images.
"""
from pathlib import Path
import hashlib,json,re,subprocess,sys
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=3:raise SystemExit('Usage: build-embedded.py qualified-native-rf2c new-directory')
c=Path(sys.argv[1]).resolve();d=Path(sys.argv[2]).resolve();d.mkdir(parents=True,exist_ok=False)
s=(R/'native/compiler/compiler.rf2').read_text()
names=['state','die','diagnostic_number','diagnostic_position','require','length','same','cp','digit','letter','token','add_token','tmatch','match','advance','expect','newline','tokenize_tail','comment_end','identifier_end','hex','number_end','read_source','module_state','module_info','module_path','line_end','line_trim','line_starts','module_path_check','module_load','module_append','module_walk','expand_modules','output','rotate','sha256_software']
parts=[]
for n in names:
 m=re.search(r'^fn '+re.escape(n)+r'\(',s,re.M);assert m,n
 nxt=re.search(r'^fn ',s[m.end():],re.M)
 part=s[m.start():m.end()+nxt.start()]if nxt else s[m.start():]
 if n in ['module_walk','expand_modules']:
  part=part.replace('"profile RF2_SYSTEM_A64_V1", 25','"profile RF2_ESP32C3_V1", 22').replace('"profile RF2_SYSTEM_A64_V1\\n", 26','"profile RF2_ESP32C3_V1\\n", 23')
 parts.append(part)
backend=R/'native/embedded/compiler.flow';src='profile RF2_SYSTEM_A64_V1\n'+''.join(parts)+backend.read_text().split('\n',1)[1]
p=d/'compiler.rf2';p.write_text(src);exe=d/'rf2-esp32c3'
subprocess.run([str(c),str(p),str(exe),'--compact'],check=True)
subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],check=True)
subprocess.run(['/usr/bin/codesign','--verify',str(exe)],check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'schema':'rf2.esp32c3.builder.v1','hostCompilerSHA256':sha(c),'canonicalBackendSHA256':sha(backend),'extractedHostSourceSHA256':hashlib.sha256(s.encode()).hexdigest(),'extractedFunctions':names,'profileAdaptation':'Exact module entry profile RF2_ESP32C3_V1 replaces Mac profile in derived frontend only.','derivedSourceSHA256':sha(p),'executableSHA256':sha(exe),'buildScriptSHA256':sha(Path(__file__)),'host':'macos-arm64','target':'esp32c3 RV32IM RAM image; no board tested by build','runtime':'Native RF2 executable; no Node/npm/Python/assembler/linker at runtime.'}
(d/'BUILD.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
