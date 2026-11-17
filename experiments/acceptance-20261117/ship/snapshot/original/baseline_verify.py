"""Two active NICs, persistent rings and independent IPv4/UDP peers."""
from pathlib import Path
import subprocess,socket,os,select,time,json,tempfile,threading,re,struct,hashlib,sys
sys.path.insert(0,str(Path(__file__).parent));from wire_peer import exchange,exact,checksum
from route_oracle import route_reply,echo_reply,ip_checksum
D=Path('artifacts/rf2ship-secure-018');rows=[];ADVERSARIAL='--adversarial' in sys.argv
for machine in ['pc','q35']:
 with tempfile.TemporaryDirectory(prefix='rf2if-',dir='/tmp') as tmp:
  paths=[str(Path(tmp)/('p%d.sock'%i)) for i in range(2)];qpath=str(Path(tmp)/'q.sock')
  cmd=['qemu-system-x86_64','-machine',machine,'-cpu','qemu64','-accel','tcg','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-qmp',f'unix:{qpath},server=on,wait=off','-drive',f'file={D}/rf2ship.img,format=raw,if=floppy,readonly=on','-no-reboot','-device','isa-debug-exit,iobase=0xf4,iosize=0x04']
  for slot in range(2):cmd+=['-netdev',f'stream,id=wire{slot},server=on,addr.type=unix,addr.path={paths[slot]}','-device',f'virtio-net-pci,id=if{slot}dev,netdev=wire{slot},disable-legacy=on,romfile=,mac=02:52:46:32:00:{2+slot*2:02x},addr=0x{3+slot:x}']
  cmd+=['-d','in_asm,int','-D',str(D/(machine+'.trace'))]
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
   def packet(slot,payload=b'test',ttl=64,source_port=None,dest_port=None,source_ip=None,zero=False,flags=0x4000,protocol=17,dest_ip=None):
    dst=bytes.fromhex('0252463200')+bytes([2+slot*2]);src=bytes.fromhex('0252463200')+bytes([3+slot*2])
    sip=source_ip or (bytes([10,77,0,3]) if slot==0 else bytes([198,51,100,9]));dip=dest_ip or (bytes([198,51,100,9]) if slot==0 else bytes([198,51,100,2]))
    sport=source_port if source_port is not None else (12345 if slot==0 else 443);dport=dest_port if dest_port is not None else (443 if slot==0 else 40000)
    udp=bytearray(struct.pack('!HHHH',sport,dport,8+len(payload),0)+payload)
    if not zero:struct.pack_into('!H',udp,6,checksum(sip+dip+b'\0'+bytes([protocol])+struct.pack('!H',len(udp))+udp) or 65535)
    ip=bytearray(struct.pack('!BBHHHBBH4s4s',0x45,0,20+len(udp),123,flags,ttl,protocol,0,sip,dip));struct.pack_into('!H',ip,10,checksum(ip))
    return (dst+src+b'\x08\x00'+ip+udp).ljust(60,b'\0')
   def transformed(b,slot,mapped_port=40000,lan_ip=bytes([10,77,0,3]),lan_port=12345):
    if slot==0 and b[22]==1:return route_reply(b)
    out=bytearray(b);out[4:6]=bytes([0,5 if slot==0 else 3]);out[10:12]=bytes([0,4 if slot==0 else 2]);out[22]-=1
    if slot==0:out[26:30]=bytes([198,51,100,2]);out[34:36]=struct.pack('!H',mapped_port)
    else:out[30:34]=lan_ip;out[36:38]=struct.pack('!H',lan_port)
    out[24:26]=b'\0\0';struct.pack_into('!H',out,24,checksum(out[14:34]));length=int.from_bytes(out[38:40],'big');out[40:42]=b'\0\0';struct.pack_into('!H',out,40,checksum(out[26:34]+b'\0\x11'+struct.pack('!H',length)+out[34:34+length]) or 65535)
    return bytes(out)
   def nat(slot,b,expected=0,label='',mapped_port=40000,lan_ip=bytes([10,77,0,3]),lan_port=12345):
    peers[slot].sendall(struct.pack('!I',len(b))+b);mark=len(out);p.stdin.write(b'r' if slot==0 else b'w');p.stdin.flush();until(b'RF2Ship> ',mark);part=out[mark:]
    m=re.search(rb'Relay result=0x([0-9a-f]+) bytes=0x([0-9a-f]+)',part);assert m,part
    result,size=[int(x,16) for x in m.groups()];assert result==expected,(label,expected,part)
    if expected==0:
     other=peers[slot if slot==0 and b[22]==1 else slot^1];length=struct.unpack('!I',exact(other,4))[0];actual=exact(other,length);wanted=transformed(b,slot,mapped_port,lan_ip,lan_port);assert actual==wanted,(label,actual.hex(),wanted.hex())
     wire.append({'label':label,'slot':slot,'result':result,'TX':actual.hex(),'RX':b.hex(),'passed':True})
    else:
     assert not select.select([peers[0],peers[1]],[],[],.02)[0],('unexpected egress',label)
     wire.append({'label':label,'slot':slot,'result':result,'RX':b.hex(),'passed':True})
    assert memory(0x4100,16)==bytes(16) and memory(0x4180,176)==bytes(176) and memory(0x51000,4096)==bytes(4096)
   CASES=[]
   def remember(label):CASES.append({'label':label,'passed':True})
   def runpacket(slot,b,code,wanted=None,label='',egress=None):
    table=memory(0x53000,3072)
    peers[slot].sendall(struct.pack('!I',len(b))+b);mark=len(out);p.stdin.write(b'r' if slot==0 else b'w');p.stdin.flush();until(b'RF2Ship> ',mark)
    m=re.search(rb'Relay result=0x([0-9a-f]+)',out[mark:]);assert m and int(m[1],16)==code,(label,code,out[mark:])
    if wanted is not None:
     target=peers[(slot if wanted[23]==1 else 1-slot) if egress is None else egress];n=struct.unpack('!I',exact(target,4))[0];actual=exact(target,n);assert actual==wanted,(label,actual.hex(),wanted.hex());wire.append({'label':label,'RX':b.hex(),'TX':actual.hex()})
    else:assert not select.select(peers,[],[],.02)[0],('unexpectedTX',label)
    assert memory(0x4100,16)==bytes(16) and memory(0x4180,176)==bytes(176) and memory(0x51000,4096)==bytes(4096)
    if code not in (0,42):assert memory(0x53000,3072)==table,(label,'refusalorARPcreatedNAT')
    remember(label)
   def arp_reply(ip=0xc6336409,mac=bytes.fromhex('025246320005')):
    local=bytes.fromhex('025246320004')
    return (local+mac+struct.pack('!HHHBBH',0x0806,1,0x0800,6,4,2)+mac+struct.pack('!I',ip)+local+bytes([198,51,100,2])).ljust(60,b'\0')
   def arp_probe(ip):
    local=bytes.fromhex('025246320004')
    return (bytes([255])*6+local+struct.pack('!HHHBBH',0x0806,1,0x0800,6,4,1)+local+bytes([198,51,100,2])+bytes(6)+struct.pack('!I',ip)).ljust(60,b'\0')
   def config(gen,slot,network,prefix,hop,accepted=True,label='config'):
    old=memory(0x55000,512);oldnat=memory(0x53000,4096);mark=len(out)
    data='R'+''.join('%08x'%n for n in [gen,slot,network,prefix,hop])+'\n';p.stdin.write(data.encode());p.stdin.flush();until(b'RF2Ship> ',mark)
    m=re.search(rb'Route result=0x([0-9a-f]+)',out[mark:]);assert m and int(m[1],16)==(0 if accepted else 43),(label,out[mark:])
    if accepted:
     assert int.from_bytes(memory(0x55000,8),'little')==gen+1
     assert memory(0x53000,4096)==bytes(4096) and memory(0x55100,64)==bytes(64)
    else:assert memory(0x55000,512)==old and memory(0x53000,4096)==oldnat,label
    assert memory(0x55400,64)==bytes(64);remember(label)
   def owned():return memory(0x56000,8192)
   def want(b,mac,port):
    x=bytearray(transformed(b,0,mapped_port=port));x[:6]=mac;return bytes(x)
   for i,(net,hop) in enumerate([(0xc6336400,9),(0xcb007100,10),(0xc0000200,11),(0x64400000,12)]):
    gen=int.from_bytes(memory(0x55000,8),'little');config(gen,i,net,24 if i<3 else 16,0xc6336400+hop,label='configure-four-'+str(i))
   frames=[]
   for i,dip in enumerate([bytes([198,51,100,7]),bytes([203,0,113,7]),bytes([192,0,2,7]),bytes([100,64,1,7])]):
    b=packet(0,payload=b'owned'+bytes([i]),dest_ip=dip,source_port=12345+i);frames.append(b)
    runpacket(0,b,0,arp_probe(0xc6336409+i),'queue-'+str(i))
    record=owned()[i*2048:(i+1)*2048];assert int.from_bytes(record[:8],'little')==1 and int.from_bytes(record[8:16],'little')==len(b) and record[64:64+len(b)]==b
    assert memory(0x53000,3072)==bytes(3072)
   before=owned();gen=int.from_bytes(memory(0x55000,8),'little')
   config(gen-1,0,0xc6336400,24,0xc6336409,False,'stale-config-preserves-all-four-owners');assert owned()==before
   config(gen,4,0xc6336400,24,0xc6336409,False,'invalid-slot-preserves-all-four-owners');assert owned()==before
   for label,at,value,code in [('bad-hardware',15,2,32),('bad-protocol',17,1,32),('bad-width',18,5,32),('wrong-target-IP',41,3,33),('wrong-target-MAC',37,6,33),('different-ARP-sender',27,6,33),('wrong-sender-IP',31,99,33),('multicast-source',6,3,28)]:
    bad=bytearray(arp_reply());bad[at]=value;before=owned()
    runpacket(1,bytes(bad),code,label=label);assert owned()==before and memory(0x58000,1024)==bytes(1024)
   old=owned();runpacket(0,frames[0],44,label='pending-capacity-no-overwrite');assert old==owned()
   for ordinal,i in enumerate([3,1,2,0]):
    mac=bytes.fromhex('02aabbccdd')+bytes([20+i]);old=owned()
    runpacket(1,arp_reply(0xc6336409+i,mac),42,want(frames[i],mac,40000+ordinal),'reverse-order-resolution-'+str(i),egress=1)
    assert owned()[i*2048:(i+1)*2048]==bytes(2048)
    assert int.from_bytes(memory(0x55100+i*64,8),'little')==2
    # Other owners are not released by this reply.
    for j in range(4):
     if j!=i:assert owned()[j*2048:(j+1)*2048]==old[j*2048:(j+1)*2048]
   assert owned()==bytes(8192);remember('all-four-originals-released-once')
   for ordinal,i in enumerate([3,1,2,0]):
    mac=bytes.fromhex('02aabbccdd')+bytes([20+i]);b=bytearray(packet(1,payload=b'return'+bytes([i]),source_ip=frames[i][30:34],source_port=443,dest_port=40000+ordinal));b[6:12]=mac
    wanted=bytearray(transformed(bytes(b),1,lan_port=12345+i));wanted[:12]=bytes.fromhex('025246320003025246320002')
    runpacket(1,bytes(b),0,bytes(wanted),'multiNeighbor-exactLANreturn-'+str(i))
   runpacket(1,arp_reply(),33,label='unsolicited-no-pending-owner')
   # Explicit policy reload cancels a held owner and cannot replay it.
   gen=int.from_bytes(memory(0x55000,8),'little');config(gen,0,0xc6336400,24,0xc6336409,label='reload-clears-state')
   runpacket(0,frames[0],0,arp_probe(0xc6336409),'pending-before-reload');assert owned()!=bytes(8192)
   gen=int.from_bytes(memory(0x55000,8),'little');config(gen,0,0xc6336400,24,0xc6336409,label='reload-cancels-owner');assert owned()==bytes(8192)
   runpacket(1,arp_reply(),33,label='stale-reply-cannot-flush-cancelled-owner')
   runpacket(0,frames[0],0,arp_probe(0xc6336409),'pending-before-expiry')
   started=int.from_bytes(memory(0x55118,8),'little');life=int.from_bytes(memory(0x5a68,8),'little');deadline=time.monotonic()+12
   while True:
    mark=len(out);p.stdin.write(b'j');p.stdin.flush();until(b'RF2Ship> ',mark)
    if int.from_bytes(memory(0x5a60,8),'little')-started>=life:break
    assert time.monotonic()<deadline;time.sleep(.02)
   runpacket(1,arp_reply(),33,label='expired-reply-no-flush')
   newer=packet(0,payload=b'newowner',dest_ip=bytes([198,51,100,7]))
   runpacket(0,newer,0,arp_probe(0xc6336409),'expiry-releases-old-before-new-owner')
   runpacket(1,arp_reply(),42,want(newer,bytes.fromhex('025246320005'),40000),'only-fresh-packet-flushed',egress=1)
   # Close while a different neighbor owns a packet.
   runpacket(0,frames[1],0,arp_probe(0xc633640a),'pending-before-close')
   cancelled=int.from_bytes(memory(0x540d0,8),'little');mark=len(out);p.stdin.write(b'z');p.stdin.flush();until(b'NAT service running;',mark)
   deadline=time.monotonic()+12
   while memory(0x56000,8192)!=bytes(8192):
    assert time.monotonic()<deadline,'idleServiceMustReleaseExpiredOwners';time.sleep(.02)
   assert int.from_bytes(memory(0x540d0,8),'little')==cancelled+1
   assert not select.select(peers,[],[],.02)[0],'expiredOwnerForwarded'
   mark=len(out);p.stdin.write(b'x');p.stdin.flush();until(b'NAT service stopped.',mark);until(b'RF2Ship> ',mark);remember('idle-service-expires-held-packet-without-new-request')
   command('c',0);command('e',1)
   assert memory(0x55100,256)==bytes(256) and owned()==bytes(8192) and memory(0x53000,4096)==bytes(4096)
   assert memory(0x58000,8192)==bytes(8192);remember('close-revokes-all-owned-pages')
   assert memory(0x30000,90112)==bytes(90112) and memory(0x60000,90112)==bytes(90112)
   p.stdin.write(b'q');p.stdin.flush();assert p.wait(timeout=5)==65
  except Exception as e:
   import traceback
   error=repr(e);(D/('FAIL-'+machine+'.json')).write_text(json.dumps({'error':error,'traceback':traceback.format_exc(),'serial':out.decode(errors='replace'),'configDiagnostic':memory(0x55000,256).hex(),'rejectedFrame':memory(0x55500,64).hex()},indent=2))
  finally:
   if p.poll() is None:p.kill();p.wait()
   for s in peers+[qs]:
    if s:s.close()
  rows.append({'machine':machine,'passed':error is None,'error':error,'cases':locals().get('CASES',[]),'wire':wire,'serial':out.decode(errors='replace')})
(D/'PENDING-VERIFICATION.json').write_text(json.dumps({'passed':all(r['passed'] for r in rows),'completed':sum(len(r['cases']) for r in rows),'rows':rows},indent=2)+'\n')
assert all(r['passed'] for r in rows),[(r['machine'],r['error']) for r in rows]
print('Neighbor/pending controls:',[len(r['cases']) for r in rows])
