from pathlib import Path
import subprocess,select,os,time,re,json,hashlib
D=Path('artifacts/rf2ship-secure-018');base=(D/'rf2ship.img').read_bytes();rows=[]
def changed(label):
 b=base
 def swap(old,new):
  nonlocal b
  old=bytes.fromhex(old);new=bytes.fromhex(new);assert len(old)==len(new) and b.count(old)==1,(label,b.count(old));b=b.replace(old,new)
 if label=='masked-timer':swap('b0fee621','b0ffe621')
 elif label=='missing-eoi':swap('66ba2000b020ee5a5848cf','66ba2000b020905a5848cf')
 elif label=='missing-ist2':swap('66c7042504520000028e','66c7042504520000008e')
 elif label=='timer-guard':swap('488b042500000100','488b042500700100')
 elif label=='guard-bypass':
  swap('488b042500000100','488b042500700100');swap('48c70425b840000000000000','48c70425b840000003700100')
 return b
for label in ['normal','masked-timer','missing-eoi','missing-ist2','timer-guard','guard-bypass']:
 image=D/('irq-'+label+'.img');image.write_bytes(changed(label));trace=D/('irq-'+label+'.trace')
 cmd=['qemu-system-x86_64','-machine','pc','-cpu','qemu64','-accel','tcg','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-drive',f'file={image},format=raw,if=floppy,readonly=on','-boot','a','-no-reboot','-device','isa-debug-exit,iobase=0xf4,iosize=0x04','-d','int','-D',str(trace)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out=b'';error=None;ticks=[]
 def until(needle,start=0):
  global out
  end=time.monotonic()+10
  while needle not in out[start:]:
   assert time.monotonic()<end,(label,needle,out[-500:],p.poll())
   if select.select([p.stdout],[],[],.1)[0]:
    b=os.read(p.stdout.fileno(),4096);assert b,(label,p.poll(),out[-500:]);out+=b
 try:
  if label=='missing-ist2':
   p.wait(timeout=10);out+=p.stdout.read();assert p.returncode==69 and b'unexpected timer interrupt frame' in out
  else:
   until(b'RF2Ship> ')
   if label in ['masked-timer','missing-eoi']:
    time.sleep(.1);mark=len(out);p.stdin.write(b'h');p.stdin.flush();end=time.monotonic()+2
    while time.monotonic()<end:
     if select.select([p.stdout],[],[],.1)[0]:out+=os.read(p.stdout.fileno(),4096)
    assert p.poll() is None and b'validated fault recovery' not in out[mark:]
   elif label in ['timer-guard','guard-bypass']:
    p.stdin.write(b'p');p.stdin.flush();p.wait(timeout=10);out+=p.stdout.read();assert p.returncode==69
    if label=='timer-guard':assert b'unexpected page-fault frame' in out
    else:assert b'recovered register/stack mismatch' in out
   else:
    for i in range(3):
     mark=len(out);p.stdin.write(b's');p.stdin.flush();until(b'RF2Ship> ',mark);m=re.search(rb'Timer ticks: 0x([0-9a-f]{16})',out[mark:]);assert m;ticks.append(int(m[1],16));time.sleep(.06)
    assert all(y>x for x,y in zip(ticks,ticks[1:])),ticks
    p.stdin.write(b'q');p.stdin.flush();p.wait(timeout=10);out+=p.stdout.read();assert p.returncode==65
 except Exception as e:error=repr(e)
 finally:
  if p.poll() is None:p.kill();p.wait()
  text=trace.read_text();count=len(re.findall(r'v=20 e=0000',text))
  if not error:
   if label=='masked-timer':assert count==0,count
   elif label=='missing-eoi':assert count==1,count
   elif label=='timer-guard':assert re.search(r'v=0e e=0000.*CR2=0*17000',text,re.I)
   elif label=='guard-bypass':assert 'v=0e' not in text
   elif label=='normal':assert count>=2
  rows.append(dict(label=label,passed=error is None,error=error,exit=p.returncode,tickSamples=ticks,IRQTraceCount=count,serial=out.decode(errors='replace'),imageSHA256=hashlib.sha256(image.read_bytes()).hexdigest(),traceSHA256=hashlib.sha256(trace.read_bytes()).hexdigest(),command=cmd))
  (D/'IRQ-VERIFICATION.json').write_text(json.dumps(dict(passed=all(x['passed'] for x in rows),completed=len(rows),planned=6,results=rows),indent=2)+'\n')
 print(label,'PASS' if not error else error,flush=True)
 if error:raise SystemExit(1)
