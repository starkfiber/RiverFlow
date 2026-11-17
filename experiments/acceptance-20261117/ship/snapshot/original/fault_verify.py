"""Bounded local clock/startup fault models and actual IRQ-masked clock progress."""
from pathlib import Path
import subprocess,socket,select,os,time,json,struct,hashlib,tempfile
V=Path('experiments/rf2ship/secure-transport-018');D=Path('artifacts/rf2ship-secure-018');base=(V/'console.s').read_text();rows=[]
models={
 'disabled-after-start':base.replace('Lservice_round:\n','Lservice_round:\n movq $0,0x52010\n',1),
 'counter-regression':base.replace(' movq 0x520f0,%rax\n cmpq 0x5a60,%rax',' xorl %eax,%eax\n cmpq 0x5a60,%rax',1),
 'period-mismatch':base.replace(' movl 0x52004,%eax\n cmpq 0x5a58,%rax',' xorl %eax,%eax\n cmpq 0x5a58,%rax',1),
 'stalled-initial-read':base.replace('Lclock_progress:\n movq 0x520f0,%rax','Lclock_progress:\n movq %r8,%rax',1),
 'zero-period':base.replace(' shrq $32,%rcx\n testq %rcx,%rcx',' shrq $32,%rcx\n xorl %ecx,%ecx\n testq %rcx,%rcx',1),
}
probe=''' movq 0x5a20,%rax
 movq %rax,0x507d0
 movq 0x520f0,%r8
 movq %r8,0x507d8
 movq 0x5a68,%rax
 xorl %edx,%edx
 movl $30,%ecx
 divq %rcx
 movq %rax,%r9
 movl $100000000,%ecx
Lmasked_wait:
 movq 0x520f0,%rax
 subq %r8,%rax
 cmpq %r9,%rax
 jae Lmasked_pass
 loop Lmasked_wait
 movq $0,0x507f0
 jmp Lmasked_done
Lmasked_pass:
 movq $1,0x507f0
Lmasked_done:
 movq 0x5a20,%rax
 movq %rax,0x507e0
 movq 0x520f0,%rax
 movq %rax,0x507e8
'''
key='Lclock_report:\n pushfq\n cli\n callq Lclock_now\n';assert base.count(key)==1
models['masked-progress']=base.replace(key,key+probe,1)
for name,s in models.items():
 assert s!=base,name
 folder=D/'models'/name;folder.mkdir(parents=True,exist_ok=True);(folder/'console.s').write_text(s)
 with (folder/'build.log').open('wb') as f:subprocess.run(['python3',str(V/'build.py'),str(folder),str(folder)],stdout=f,stderr=f,check=True)
for machine in ['pc','q35']:
 for label in ['no-hpet','missing-interface','no-peer-idle',*models]:
  image=D/'models'/label/'rf2ship.img' if label in models else D/'rf2ship.img'
  with tempfile.TemporaryDirectory(prefix='rf2fault-',dir='/tmp') as tmp:
   qpath=str(Path(tmp)/'q.sock')
   cmd=['qemu-system-x86_64','-machine',machine+(',hpet=off' if label=='no-hpet' else ''),'-cpu','qemu64','-accel','tcg','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-qmp',f'unix:{qpath},server=on,wait=off','-drive',f'file={image},format=raw,if=floppy,readonly=on','-no-reboot','-device','isa-debug-exit,iobase=0xf4,iosize=0x04']
   for i in range(1 if label=='missing-interface' else 2):cmd+=['-netdev',f'hubport,id=n{i},hubid={102+i}','-device',f'virtio-net-pci,id=if{i}dev,netdev=n{i},disable-legacy=on,romfile=,addr=0x{3+i:x}']
   p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out=b'';qs=None;error=None;details={}
   def until(needle,mark=0):
    global out
    end=time.monotonic()+15
    while needle not in out[mark:]:
     assert time.monotonic()<end,(label,needle,out[-1500:],p.poll())
     if select.select([p.stdout],[],[],.1)[0]:
      b=os.read(p.stdout.fileno(),8192);assert b,(p.poll(),out,p.stderr.read());out+=b
   try:
    until(b'RF2Ship> ');qs=socket.socket(socket.AF_UNIX);qs.settimeout(5);qs.connect(qpath);qf=qs.makefile('rb');assert 'QMP' in json.loads(qf.readline());seq=0
    def q(name,args=None):
     global seq
     seq+=1;r={'execute':name,'id':seq}
     if args:r['arguments']=args
     qs.sendall((json.dumps(r)+'\n').encode())
     while True:
      r=json.loads(qf.readline())
      if r.get('id')==seq:assert 'return' in r,r;return r['return']
    q('qmp_capabilities')
    def mem(at,n):
     f=Path(tmp)/'mem.bin';q('pmemsave',{'val':at,'size':n,'filename':str(f)});return f.read_bytes()
    if label=='masked-progress':
     for key in ['o','i']:
      mark=len(out);p.stdin.write(key.encode());p.stdin.flush();until(b'RF2Ship> ',mark)
     mark=len(out);p.stdin.write(b'j');p.stdin.flush();until(b'RF2Ship> ',mark)
     before,clock_before,pit_after,clock_after=struct.unpack('<QQQQ',mem(0x507d0,32));assert before==pit_after and clock_after>clock_before and mem(0x507f0,8)==(1).to_bytes(8,'little')
     details={'PITbefore':before,'PITafter':pit_after,'HPETbefore':clock_before,'HPETafter':clock_after,'maskedProgressPassed':True}
     p.stdin.write(b'x');p.stdin.flush();until(b'RF2Ship> ',len(out)-1)
    elif label=='no-peer-idle':
     mark=len(out);p.stdin.write(b'z');p.stdin.flush();until(b'NAT service running;',mark)
     assert mem(0x5a78,8)==(1).to_bytes(8,'little') and mem(0x5a80,24)==bytes(24)
     assert mem(0x32002,2)==bytes(2) and mem(0x65002,2)==bytes(2)
     before=int.from_bytes(mem(0x5a60,8),'little');time.sleep(.1);after=int.from_bytes(mem(0x5a60,8),'little');assert after>before
     mark=len(out);p.stdin.write(b'x');p.stdin.flush();until(b'NAT service stopped.',mark);until(b'RF2Ship> ',mark)
     assert mem(0x5a78,8)==bytes(8) and mem(0x5ae0,8)==bytes(8)
     assert mem(0x30000,90112)==bytes(90112) and mem(0x60000,90112)==bytes(90112)
     details={'noPeerOrHandshake':True,'serviceRanIdle':True,'noStartupTX':True,'clockAdvanced':True,'cancelledCleanly':True}
    else:
     mark=len(out);p.stdin.write(b'z');p.stdin.flush();until(b'NAT service stopped.',mark);until(b'RF2Ship> ',mark)
     assert mem(0x5a78,8)==bytes(8) and mem(0x5ae0,8)==bytes(8)
     assert mem(0x30000,90112)==bytes(90112) and mem(0x60000,90112)==bytes(90112)
     assert mem(0x502c0,8)==bytes(8) and mem(0x50ac0,8)==bytes(8)
     assert mem(0x4100,16)==bytes(16) and mem(0x4180,176)==bytes(176)
     if label!='missing-interface':assert mem(0x5a50,8)==(2).to_bytes(8,'little')
     details={'stopped':True,'authorizationRevoked':True,'arenasZero':True,'ownersReleased':True,'CPUaliasesRevoked':True}
    p.stdin.write(b'q');p.stdin.flush();p.wait(timeout=8);assert p.returncode==65
   except BaseException:
    import traceback
    error=traceback.format_exc()
   finally:
    if qs:qs.close()
    if p.poll() is None:p.kill();p.wait()
    rows.append({'model':label,'machine':machine,'passed':error is None,'error':error,'details':details,'serial':out.decode(errors='replace'),'imageSHA256':hashlib.sha256(image.read_bytes()).hexdigest(),'exit':p.returncode})
    (D/'FAULT-VERIFICATION.json').write_text(json.dumps({'passed':all(r['passed'] for r in rows),'completed':len(rows),'planned':18,'scope':'Local emulated clock/startup faults and source-hook models, no physical fault or hostile-host attestation','results':rows},indent=2)+'\n')
   print(machine,label,'PASS' if error is None else error,flush=True)
   if error:raise SystemExit(1)
