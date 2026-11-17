"""Two active NICs, persistent rings and independent IPv4/UDP peers."""
from pathlib import Path
import subprocess,socket,os,select,time,json,tempfile,threading,re,struct,hashlib,sys
sys.path.insert(0,str(Path(__file__).parent));from wire_peer import exchange,exact,checksum
D=Path('artifacts/rf2ship-secure-018');rows=[];ADVERSARIAL='--adversarial' in sys.argv
for machine in ['pc','q35']:
 with tempfile.TemporaryDirectory(prefix='rf2if-',dir='/tmp') as tmp:
  paths=[str(Path(tmp)/('p%d.sock'%i)) for i in range(2)];qpath=str(Path(tmp)/'q.sock')
  cmd=['qemu-system-x86_64','-machine',machine,'-cpu','qemu64','-accel','tcg','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-qmp',f'unix:{qpath},server=on,wait=off','-drive',f'file={D}/rf2ship.img,format=raw,if=floppy,readonly=on','-no-reboot','-device','isa-debug-exit,iobase=0xf4,iosize=0x04']
  for slot in range(2):cmd+=['-netdev',f'stream,id=wire{slot},server=on,addr.type=unix,addr.path={paths[slot]}','-netdev',f'hubport,id=lab{slot},hubid={102+slot}','-netdev',f'hubport,id=peer{slot},hubid={102+slot},netdev=wire{slot}','-device',f'virtio-net-pci,id=if{slot}dev,netdev=lab{slot},disable-legacy=on,romfile=,mac=02:52:46:32:00:{2+slot*2:02x},addr=0x{3+slot:x}']
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out=b'';peers=[];qs=None;error=None;wire=[];proof=[]
  def until(needle,mark=0):
   global out
   deadline=time.monotonic()+15
   while needle not in out[mark:]:
    assert time.monotonic()<deadline,(needle,out[-1800:],p.poll())
    if select.select([p.stdout],[],[],.1)[0]:
     b=os.read(p.stdout.fileno(),8192);assert b,(p.poll(),out,p.stderr.read());out+=b
  try:
   until(b'RF2Ship> ')
   for path in paths:
    s=socket.socket(socket.AF_UNIX);s.settimeout(12);s.connect(path);peers.append(s)
   qs=socket.socket(socket.AF_UNIX);qs.settimeout(5);qs.connect(qpath);qf=qs.makefile('rb')
   for _ in range(16):
    hello=json.loads(qf.readline())
    if 'QMP' in hello:break
    assert 'event' in hello
   else:raise RuntimeError('missing greeting')
   seq=0
   def q(execute,arguments=None):
    global seq
    seq+=1;request={'execute':execute,'id':seq}
    if arguments:request['arguments']=arguments
    qs.sendall((json.dumps(request)+'\n').encode())
    while True:
     obj=json.loads(qf.readline())
     if obj.get('id')==seq:
      assert 'return' in obj,obj
      return obj['return']
   q('qmp_capabilities')
   def memory(at,size):
    f=Path(tmp)/'mem.bin';q('pmemsave',{'val':at,'size':size,'filename':str(f)});b=f.read_bytes();assert len(b)==size;return b
   def command(key,slot,expected=0,generation=None,start=None,mode='normal'):
    rec={};thread=None
    if generation is not None:
     thread=threading.Thread(target=exchange,args=(peers[slot],slot,generation,start,mode,rec),daemon=True);thread.start()
    mark=len(out);p.stdin.write(key.encode());p.stdin.flush();until(b'RF2Ship> ',mark);part=out[mark:]
    if thread:thread.join(2);assert not thread.is_alive() and rec.get('passed'),rec;wire.append(rec)
    found=re.search(rb'Interface0x([0-9a-f]+) result=0x([0-9a-f]+) cleanup: 0x([0-9a-f]+) active=0x([0-9a-f]+)',part);assert found,part
    which,result,cleanup,mask=[int(x,16) for x in found.groups()];assert which==slot and result==expected and cleanup==0,(expected,part)
    assert memory(0x4100,16)==bytes(16) and memory(0x4180,176)==bytes(176),'CPU aliases leaked between commands'
    proof.append({'command':key,'slot':slot,'result':result,'activeMask':mask,'CPUaliasesZero':True})
    return part
   command('o',0);command('i',1)
   for slot in [0,1]:
    bank=0x50000+slot*0x800;arena=0x30000+slot*0x30000
    assert int.from_bytes(memory(bank+0x138,8),'little')==16
    assert int.from_bytes(memory(bank+0xa8,8),'little')==16
    assert int.from_bytes(memory(arena+0x1002,2),'little')==16
    assert int.from_bytes(memory(bank+0x140,8),'little')==15

   assert memory(0x32002,2)==bytes(2) and memory(0x35002,2)==bytes(2)
   assert memory(0x62002,2)==bytes(2) and memory(0x65002,2)==bytes(2)
   assert not select.select(peers,[],[],.05)[0],'raw startup emitted packets'
   mark=len(out);p.stdin.write(b'j');p.stdin.flush();until(b'RF2Ship> ',mark)
   assert b'HPET state=0x0000000000000001' in out[mark:],out[mark:]
   clock1=int.from_bytes(memory(0x5a60,8),'little');time.sleep(.02)
   mark=len(out);p.stdin.write(b'j');p.stdin.flush();until(b'RF2Ship> ',mark)
   clock2=int.from_bytes(memory(0x5a60,8),'little');assert clock2>clock1
   command('c',0);command('e',1)
   p.stdin.write(b'q');p.stdin.flush();p.wait(timeout=8);assert p.returncode==65
  except Exception:
   import traceback
   error=traceback.format_exc()
  finally:
   for sock in peers:sock.close()
   if qs:qs.close()
   if p.poll() is None:p.kill();p.wait()
   rows.append({'machine':machine,'passed':error is None,'error':error,'serial':out.decode(errors='replace'),'exit':p.returncode,'stderr':p.stderr.read().decode(errors='replace')})
   (D/'START-CLOCK-VERIFICATION.json').write_text(json.dumps({'passed':all(r['passed'] for r in rows),'completed':len(rows),'planned':2,'results':rows},indent=2)+'\n')
  print(machine,'PASS' if not error else error,flush=True)
  if error:raise SystemExit(1)
