"""CPU guard/NX/revocation tests and a BIOS-memory refusal model."""
from pathlib import Path
import subprocess,select,os,time,json,re,hashlib
D=Path('artifacts/rf2ship-secure-018');V=Path('experiments/rf2ship/secure-transport-018');base=(V/'console.s').read_text();rows=[]
key=' movq $1,0x5a28\n';assert base.count(key)==1
cases=[('code-C-readonly',base.replace(key,' movq 0xc000,%rax\n movq %rax,0xc000\n'+key,1),3,0xc000),('telemetry-nx',base.replace(key,' movq $0x54000,%rax\n callq *%rax\n'+key,1),17,0x54000),('NAT-state-nx',base.replace(key,' movq $0x53000,%rax\n callq *%rax\n'+key,1),17,0x53000)]

cases += [(label,base.replace(key,' movq $'+hex(at)+',%rax\n callq *%rax\n'+key,1),17,at) for label,at in [('intent-nx',0x5a000),('routes-nx',0x55000),('pending0-nx',0x56000),('pending1-nx',0x57000),('tcp-nx',0x58000),('shadow-nx',0x59000),('irq-stack-nx',0x18000)]]
cases += [(label,base.replace(key,' movq '+hex(at)+',%rax\n movq %rax,'+hex(at)+'\n'+key,1),3,at) for label,at in [('codeD-readonly',0xd000),('codeE-readonly',0xe000),('codeF-readonly',0xf000)]]
cases.append(('irq-guard',base.replace(key,' movq 0x17000,%rax\n'+key,1),0,0x17000))
for label,source,error,address in cases:
 f=D/('guard-'+label);f.mkdir(exist_ok=True);(f/'console.s').write_text(source)
 with (f/'build.log').open('wb') as log:subprocess.run(['python3',str(V/'build.py'),str(f),str(f)],check=True,stdout=log,stderr=log)
 trace=f/'qemu.trace';cmd=['qemu-system-x86_64','-machine','pc','-cpu','qemu64','-accel','tcg','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-drive',f'file={f}/rf2ship.img,format=raw,if=floppy,readonly=on','-no-reboot','-device','isa-debug-exit,iobase=0xf4,iosize=0x04','-netdev','hubport,id=lab,hubid=102','-device','virtio-net-pci,netdev=lab,disable-legacy=on,romfile=','-d','int','-D',str(trace)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out=b'';deadline=time.monotonic()+8
 while b'RF2Ship> ' not in out:
  assert time.monotonic()<deadline,(label,out)
  if select.select([p.stdout],[],[],.1)[0]:
   part=os.read(p.stdout.fileno(),4096);assert part;out+=part
 tail,err=p.communicate(b'o',timeout=20);out+=tail
 faults=re.findall(r'v=0e e=([0-9a-f]+).*?CR2=([0-9a-f]+)',trace.read_text())
 passed=p.returncode==69 and any(int(e,16)==error and int(a,16)==address for e,a in faults)
 rows.append(dict(label=label,passed=passed,expectedError=error,address=hex(address),faults=faults,exit=p.returncode,serial=out.decode(errors='replace'),traceSHA256=hashlib.sha256(trace.read_bytes()).hexdigest()))
 (D/'NEW-PAGE-GUARDS.json').write_text(json.dumps(dict(passed=all(r['passed'] for r in rows),completed=len(rows),planned=14,scope='Injected unexpected faults halt; CPU guards are not an IOMMU or exception-unwind proof',results=rows),indent=2)+'\n')
 print(label,'PASS' if passed else rows[-1],flush=True)
 if not passed:raise SystemExit(1)
