"""CPU guard/NX/revocation tests and a BIOS-memory refusal model."""
from pathlib import Path
import subprocess,select,os,time,json,re,hashlib
D=Path('artifacts/rf2ship-secure-018');V=Path('experiments/rf2ship/secure-transport-018');base=(V/'console.s').read_text();rows=[]
cases=[('leading-guard',base.replace(' # Build RX and TX descriptors',' movq 0x2f000,%rax\n # Build RX and TX descriptors',1),0,0x2f000),('trailing-guard',base.replace(' # Build RX and TX descriptors',' movq 0x46000,%rax\n # Build RX and TX descriptors',1),0,0x46000),('dma-nx',base.replace(' # Build RX and TX descriptors',' movq $0x30000,%rax\n callq *%rax\n # Build RX and TX descriptors',1),17,0x30000),('after-release',base.replace(' callq Ldma_cleanup\n',' callq Ldma_cleanup\n movq 0x30000,%rax\n',1),0,0x30000)]
for label,source,error,address in cases:
 f=D/('guard-'+label);f.mkdir(exist_ok=True);(f/'console.s').write_text(source)
 with (f/'build.log').open('wb') as log:subprocess.run(['python3',str(V/'build.py'),str(f),str(f)],check=True,stdout=log,stderr=log)
 trace=f/'qemu.trace';cmd=['qemu-system-x86_64','-machine','pc','-cpu','qemu64','-accel','tcg','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-drive',f'file={f}/rf2ship.img,format=raw,if=floppy,readonly=on','-no-reboot','-device','isa-debug-exit,iobase=0xf4,iosize=0x04','-netdev','hubport,id=lab,hubid=102','-device','virtio-net-pci,netdev=lab,disable-legacy=on,romfile=','-d','int','-D',str(trace)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out=b'';deadline=time.monotonic()+8
 while b'RF2Ship> ' not in out:
  assert time.monotonic()<deadline,(label,out)
  if select.select([p.stdout],[],[],.1)[0]:
   part=os.read(p.stdout.fileno(),4096);assert part;out+=part
 tail,err=p.communicate(b'd',timeout=20);out+=tail
 faults=re.findall(r'v=0e e=([0-9a-f]+).*?CR2=([0-9a-f]+)',trace.read_text())
 passed=p.returncode==69 and any(int(e,16)==error and int(a,16)==address for e,a in faults)
 rows.append(dict(label=label,passed=passed,expectedError=error,address=hex(address),faults=faults,exit=p.returncode,serial=out.decode(errors='replace'),traceSHA256=hashlib.sha256(trace.read_bytes()).hexdigest()))
 (D/'DMA-GUARD-VERIFICATION.json').write_text(json.dumps(dict(passed=all(r['passed'] for r in rows),completed=len(rows),planned=4,scope='Injected unexpected faults halt; CPU guards are not an IOMMU or exception-unwind proof',results=rows),indent=2)+'\n')
 print(label,'PASS' if passed else rows[-1],flush=True)
 if not passed:raise SystemExit(1)
b=(D/'rf2ship.img').read_bytes();needle=bytes.fromhex('cd1290');assert b.count(needle)==1
mutated=b.replace(needle,bytes.fromhex('b88000'),1);image=D/'bios-memory-refused.img';image.write_bytes(mutated)
cmd=['qemu-system-x86_64','-machine','pc','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-drive',f'file={image},format=raw,if=floppy,readonly=on','-no-reboot','-device','isa-debug-exit,iobase=0xf4,iosize=0x04']
p=subprocess.run(cmd,capture_output=True,timeout=8);assert p.returncode==77 and b'RF2Ship' not in p.stdout
(D/'BIOS-MEMORY-VERIFICATION.json').write_text(json.dumps(dict(passed=True,exit=p.returncode,scope='Binary hook supplies128KiB conventional RAM; refused before banner, not a physical low-memory observation',imageSHA256=hashlib.sha256(mutated).hexdigest()),indent=2)+'\n');print('conventional-memory-refusal PASS')
