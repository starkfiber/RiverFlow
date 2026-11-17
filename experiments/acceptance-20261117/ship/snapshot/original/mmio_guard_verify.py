"""Fault-injection controls for MMIO mapping permissions and revocation.

Unexpected faults deliberately enter the existing fatal handler. These tests
do not establish automatic device cleanup after arbitrary kernel exceptions.
"""
from pathlib import Path
import subprocess,json,re,hashlib
D=Path('artifacts/rf2ship-secure-018');V=Path('experiments/rf2ship/secure-transport-018');base=(V/'console.s').read_text();rows=[]
cases=[
 ('before-map',base.replace(' callq Lvirtio_negotiate',' callq Lvirtio_negotiate',1).replace(' # A single uncached',' movq 0x20000,%rax\n # A single uncached',1),0,0x20000),
 ('nx-fetch',base.replace(' callq Lvirtio_negotiate',' movq $0x20000,%rax\n callq *%rax\n callq Lvirtio_negotiate',1),17,0x20000),
 ('adjacent-page',base.replace(' callq Lvirtio_negotiate',' movq 0x21000,%rax\n callq Lvirtio_negotiate',1),0,0x21000),
 ('after-revoke',base.replace(' movq $0,0x4100\n invlpg 0x20000',' movq $0,0x4100\n invlpg 0x20000\n movq 0x20000,%rax',1),0,0x20000),
]
for label,source,code,address in cases:
 f=D/('guard-'+label);f.mkdir(exist_ok=True);(f/'console.s').write_text(source)
 with (f/'build.log').open('wb') as log:subprocess.run(['python3',str(V/'build.py'),str(f),str(f)],check=True,stdout=log,stderr=log)
 trace=f/'qemu.trace'
 cmd=['qemu-system-x86_64','-machine','pc','-cpu','qemu64','-accel','tcg','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-drive',f'file={f}/rf2ship.img,format=raw,if=floppy,readonly=on','-no-reboot','-device','isa-debug-exit,iobase=0xf4,iosize=0x04','-netdev','hubport,id=lab,hubid=102','-device','virtio-net-pci,netdev=lab,disable-legacy=on,romfile=','-d','int','-D',str(trace)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 # Synchronize on the complete prompt before sending the only command.
 out=b''
 import select,os,time
 deadline=time.monotonic()+8
 while b'RF2Ship> ' not in out:
  assert time.monotonic()<deadline,(label,out)
  if select.select([p.stdout],[],[],.1)[0]:
   chunk=os.read(p.stdout.fileno(),4096);assert chunk;out+=chunk
 tail,err=p.communicate(b'v',timeout=8);out+=tail
 text=trace.read_text();faults=re.findall(r'v=0e e=([0-9a-f]+).*?CR2=([0-9a-f]+)',text)
 passed=p.returncode==69 and b'FATAL: unexpected page-fault frame' in out and any(int(e,16)==code and int(a,16)==address for e,a in faults)
 rows.append(dict(label=label,passed=passed,expectedError=code,expectedAddress=hex(address),faults=faults,exit=p.returncode,serial=out.decode(errors='replace'),traceSHA256=hashlib.sha256(trace.read_bytes()).hexdigest()))
 (D/'MMIO-GUARD-VERIFICATION.json').write_text(json.dumps(dict(passed=all(x['passed'] for x in rows),completed=len(rows),planned=len(cases),scope='Injected unexpected CPU faults halt; not exception cleanup or hostile-device proof',results=rows),indent=2)+'\n')
 print(label,'PASS' if passed else rows[-1],flush=True)
 if not passed:raise SystemExit(1)
