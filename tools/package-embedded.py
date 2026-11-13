"""Package supplied RF2 native compilers and sources; no vendor binaries/downloads."""
from pathlib import Path
import sys,subprocess,json,hashlib,shutil,zipfile
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=6:raise SystemExit('Usage: package-embedded.py MAC-RF2C ESP-RF2C RUNTIME COMPOSED-COMPILER-SOURCE NEW-DIRECTORY')
C,E,RT,S,D=[Path(x).resolve()for x in sys.argv[1:]];D.mkdir(parents=True,exist_ok=False)
for name,src in [('rf2c',C),('rf2-esp32c3',E),('rf2',RT)]:
 subprocess.run(['/usr/bin/codesign','--verify',src],capture_output=True,check=True);shutil.copy2(src,D/name)
shutil.copy2(R/'LICENSE',D/'LICENSE');shutil.copytree(R/'examples/esp32c3',D/'examples/esp32c3',ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'));(D/'source').mkdir();shutil.copy2(S,D/'source/embedded-compiler.rf2');shutil.copy2(R/'native/embedded/compiler.flow',D/'source/backend.flow');(D/'firmware').mkdir()
def run(args):
 q=subprocess.run(list(map(str,args)),capture_output=True,timeout=30,env={'PATH':'/nonexistent'});assert q.returncode==0,(args,q.stderr);return q
for name in ['uart-smoke','uart-echo','tmp102','timed-heartbeat','interrupt-heartbeat']:run([D/'rf2-esp32c3',D/f'examples/esp32c3/{name}.flow',D/f'firmware/{name}'])
assert json.loads(run([D/'rf2','status']).stdout)['version']=='0.17.0'
(D/'README.txt').write_text('''RF2 0.36 development candidate. Native compiler HOST: Apple Silicon macOS.
Firmware TARGET: ESP32-C3 bounded RV32IM RAM image, not arbitrary RF2 programs.
Ad-hoc signed, not notarized. Stable release unchanged.

./rf2-esp32c3 examples/esp32c3/uart-smoke.flow NEW-PREFIX
Outputs NEW-PREFIX.elf / .bin / .map. Existing outputs refuse.
./rf2 mcp

To rebuild the cross-compiler using RF2 only:
./rf2c source/embedded-compiler.rf2 NEW-COMPILER --compact
Apply normal macOS codesign -s - NEW-COMPILER before execution.
The native compilers need no Python/Node/C++/assembler/linker runtime.
Python test controllers and GNU/QEMU comparison tools are development tools.

ROM/SPI boot, UART TX/RX and scripted GPIO/sensor models were tested in QEMU.
NO physical board or temperature sensor was tested. Firmware is NOT automatically flashed.
The examples inherit ROM UART setup. I2C timing and physical watchdog behavior need hardware checks.
New interrupt syntax: interrupt fn dispatch(cause), one bounded non-nested dispatcher.
ISR paths reject loops and interrupt re-enabling. Stack/register preservation and fail-closed
storm/exception controls were tested in QEMU, not on a physical board.
Checked boot-local peripheral leases cover SYSTIMER0/target0/CPU line1 and TIMG0 WDT.
Copied or guessed integer handles/raw MMIO are not a security boundary or linear type proof.
Reserve DRAM 0x3FCA8100..0x3FCA83FF and interrupt stack 0x3FCAC000..0x3FCAFFFF.
RTC watchdog, electrical behavior and physical interrupt timing remain unqualified.
Read examples/esp32c3/README.md and board.json before any device operation.
No Secure Boot, OTA, radio, other ESP32 architecture, Arduino or Pico support claimed.
Existing nine bounded MCP tools gain no raw-MMIO/flash/device authority.
Evidence/limits: https://github.com/starkfiber/RiverFlow/blob/main/docs/ESP32C3-INTERRUPTS-0.36.md
Created by Ilangkhumanan Thirunavokkarasu. Published by SFE. MIT licence.
''')
m=dict(version='0.36.0-dev',compilerHost='macos-arm64',firmwareTarget='esp32c3-rv32im-ram-interrupt-v1',runtimeContract='0.17 nine bounded tools',physicalHardwareTested=False,packagerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),files={str(p.relative_to(D)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(D.rglob('*'))if p.is_file()})
(D/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n');z=D.parent/(D.name+'.zip')
with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED)as f:
 for p in sorted(D.rglob('*')):
  if p.is_file():f.write(p,str(Path(D.name)/p.relative_to(D)))
print(json.dumps(dict(passed=True,zip=str(z),bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest())))
