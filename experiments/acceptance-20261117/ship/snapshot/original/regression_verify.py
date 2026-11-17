from pathlib import Path
import subprocess,select,os,time,json,hashlib,struct,re
D=Path('artifacts/rf2ship-secure-018');original=(D/'rf2ship.img').read_bytes();rows=[]
def mutate(label):
 b=original
 def swap(old,new):
  nonlocal b
  assert len(old)==len(new) and b.count(old)==1,(label,old.hex(),b.count(old));b=b.replace(old,new)
 if label=='unarmed':swap(bytes.fromhex('48c70425005a000001000000'),bytes.fromhex('48c70425005a000000000000'))
 elif label=='wrong-address':swap(bytes.fromhex('488b042500000100'),bytes.fromhex('488b042500100100'))
 elif label=='wrong-error':swap(bytes.fromhex('488b042500000100'),bytes.fromhex('4889042500000100'))
 elif label=='bad-resume':
  key=bytes.fromhex('48890425105a0000');assert b.count(key)==1;at=b.index(key);assert b[at-7:at-4]==bytes.fromhex('488d05');old=struct.unpack_from('<i',b,at-4)[0];b=b[:at-4]+struct.pack('<i',old+1)+b[at:]
 elif label=='bad-stack':swap(bytes.fromhex('bc00800000'),bytes.fromhex('bc10800000'))
 elif label=='missing-ist':swap(bytes.fromhex('66c70425e4500000018e'),bytes.fromhex('66c70425e4500000008e'))
 elif label=='corrupt-restore':swap(bytes.fromhex('5b584883c40848cf'),bytes.fromhex('5b5b4883c40848cf'))
 return b
cases=[('normal',cpu,transport) for cpu in ['qemu64','max'] for transport in ['floppy','cdrom']]+[(x,'qemu64','floppy') for x in ['unarmed','wrong-address','wrong-error','bad-resume','bad-stack','missing-ist','corrupt-restore']]
for label,cpu,transport in cases:
 target=D/('rf2ship.iso' if transport=='cdrom' else label+'.img')
 if transport=='floppy':target.write_bytes(mutate(label))
 trace=D/(label+'-'+cpu+'-'+transport+'.trace')
 cmd=['qemu-system-x86_64','-machine','pc','-cpu',cpu,'-accel','tcg','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-drive',f'file={target},format=raw,if={"floppy" if transport=="floppy" else "ide"},media={"disk" if transport=="floppy" else "cdrom"},readonly=on','-boot','a' if transport=='floppy' else 'd','-no-reboot','-device','isa-debug-exit,iobase=0xf4,iosize=0x04','-d','int','-D',str(trace)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out=b'';error=None
 def until(needle,start=0):
  global out
  deadline=time.monotonic()+10
  while needle not in out[start:]:
   if time.monotonic()>=deadline:raise RuntimeError(('timeout',needle,out[-1000:],p.poll()))
   if select.select([p.stdout],[],[],.2)[0]:
    got=os.read(p.stdout.fileno(),4096)
    if not got:raise RuntimeError(('eof',needle,out[-1000:],p.poll()))
    out+=got
 try:
  until(b'RF2Ship> ')
  if label=='normal':
   for iteration in range(32):
    start=len(out);p.stdin.write(b'p');p.stdin.flush();until(b'RECOVERED: registers, carry flag and stack preserved.',start);until(b'RF2Ship> ',start)
   start=len(out);p.stdin.write(b's');p.stdin.flush();until(b'Recovered page faults: 0x0000000000000020',start)
   start=len(out);p.stdin.write(b'h');p.stdin.flush();until(b'validated fault recovery',start)
   p.stdin.write(b'q');p.stdin.flush();p.wait(timeout=10);out+=p.stdout.read();assert p.returncode==65
   text=trace.read_text();assert len(re.findall(r'v=0e e=0000',text))==32
  else:
   p.stdin.write(b'p');p.stdin.flush();p.wait(timeout=10);out+=p.stdout.read();assert p.returncode==69,(p.returncode,out)
   assert b'RECOVERED:' not in out
   expected=b'recovered register/stack mismatch' if label=='corrupt-restore' else b'unexpected page-fault frame; recovery refused'
   assert expected in out,(label,out)
 except Exception as e:error=repr(e)
 finally:
  if p.poll() is None:p.kill();p.wait()
  rows.append(dict(label=label,cpu=cpu,transport=transport,passed=error is None,error=error,exit=p.returncode,serial=out.decode(errors='replace'),imageSHA256=hashlib.sha256(target.read_bytes()).hexdigest(),traceSHA256=hashlib.sha256(trace.read_bytes()).hexdigest(),command=cmd))
  (D/'VERIFICATION.json').write_text(json.dumps(dict(passed=all(x['passed'] for x in rows),completed=len(rows),planned=len(cases),results=rows),indent=2)+'\n')
 print(label,cpu,transport,'PASS' if error is None else error,flush=True)
 if error:raise SystemExit(1)
print('All recovery and refusal controls passed.')
