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
   def runpacket(slot,b,code,wanted=None,label=''):
    table=memory(0x53000,3072)
    peers[slot].sendall(struct.pack('!I',len(b))+b);mark=len(out);p.stdin.write(b'r' if slot==0 else b'w');p.stdin.flush();until(b'RF2Ship> ',mark)
    m=re.search(rb'Relay result=0x([0-9a-f]+)',out[mark:]);assert m and int(m[1],16)==code,(label,code,out[mark:])
    if wanted is not None:
     target=peers[slot if wanted[23]==1 or code==42 else 1-slot];n=struct.unpack('!I',exact(target,4))[0];actual=exact(target,n);assert actual==wanted,(label,actual.hex(),wanted.hex());wire.append({'label':label,'RX':b.hex(),'TX':actual.hex()})
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
    assert memory(0x55200,64)==bytes(64);remember(label)
   def warm():
    runpacket(0,packet(0),0,arp_probe(0xc6336409),'neighborProbeBeforeUDP')
    runpacket(1,arp_reply(),42,transformed(packet(0),0),label='solicitedResolutionReleasesOwnedUDP')
    assert int.from_bytes(memory(0x53000,8),'little')==1 and memory(0x56000,8192)==bytes(8192)
   warm()
   nat(1,packet(1,dest_port=40031),36,'unallocated-WAN-port-refused')
   assert int.from_bytes(memory(0x4298,8),'little')&~0x60==0x8000000000053003
   flows=[]
   for i in range(32):
    ip=bytes([10,77,0,3+i%4]);port=12345+i//4;remote=443+i%3
    flows.append((ip,port,remote))
    nat(0,packet(0,payload=bytes([i]),source_port=port,dest_port=remote,source_ip=ip),label='allocate-'+str(i),mapped_port=40000+i)
   table=memory(0x53000,3072)
   assert sum(struct.unpack_from('<Q',table,i*96)[0]==1 for i in range(32))==32,'all32 bindings must coexist'
   for i,(ip,port,remote) in enumerate(flows):
    entry=struct.unpack_from('<12Q',table,i*96)
    assert entry[1]==port and entry[2]==remote and entry[6]==1 and entry[7]==int.from_bytes(ip,'little'),(i,entry)
   nat(0,packet(0,source_port=65500),38,'table-exhaustion-refused')
   assert memory(0x53000,3072)==table,'full table refusal changed existing bindings'
   # Existing entries still work while full, including out-of-order returns.
   for i in list(range(31,-1,-1)):
    ip,port,remote=flows[i]
    nat(1,packet(1,payload=bytes([i]),source_port=remote,dest_port=40000+i),label='isolated-return-'+str(i),mapped_port=40000+i,lan_ip=ip,lan_port=port)
   ip,port,remote=flows[7]
   nat(0,packet(0,source_port=port,dest_port=remote,source_ip=ip),label='existing-flow-reuses-port',mapped_port=40007)
   nat(1,packet(1,source_port=9999,dest_port=40007),36,'wrong-remote-port')
   nat(1,packet(1,dest_port=39999),36,'below-pool')
   nat(1,packet(1,dest_port=40032),36,'above-pool')
   nat(0,packet(0,source_port=0),33,'zero-source-port')
   nat(0,packet(0,dest_port=0),33,'zero-destination-port')
   nat(0,packet(0,source_ip=bytes([10,77,0,2])),33,'gateway-address-refused')
   nat(0,packet(0,source_ip=bytes([10,77,1,3])),33,'outside-LAN-refused')
   for slot in [0,1]:
    nat(slot,packet(slot,ttl=1),0 if slot==0 else 34,'TTL-one')
    nat(slot,packet(slot,flags=0x2000),32,'fragment')
    nat(slot,packet(slot,protocol=6),32,'truncatedTCP')
    b=bytearray(packet(slot));b[40]^=1;nat(slot,bytes(b),35,'checksum')
   # Wait on actual HPET predicate until every saved outbound entry is expired.
   last=max(struct.unpack_from('<Q',memory(0x53000,3072),i*96+24)[0] for i in range(32));lifetime=int.from_bytes(memory(0x5a68,8),'little');deadline=time.monotonic()+15
   while True:
    mark=len(out);p.stdin.write(b'j');p.stdin.flush();until(b'RF2Ship> ',mark)
    tick=int.from_bytes(memory(0x5a60,8),'little')
    if tick-last>=lifetime:break
    assert time.monotonic()<deadline,'expiry wait budget';time.sleep(.03)
   nat(1,packet(1,dest_port=40007),33,'expired-neighbor-and-pool-refused');assert memory(0x53000,3072)==bytes(3072)
   # Reuse after expiry; UDP cannot distinguish an old identical tuple from new traffic.
   warm()
   nat(0,packet(0),label='reuse-after-expiry');nat(1,packet(1),label='return-after-expiry')
   command('e',1);assert memory(0x53000,4096)==bytes(4096)
   command('i',1);nat(1,packet(1),33,'old-neighbor-generation-refused')
   warm()
   nat(0,packet(0),label='new-generation-out');nat(1,packet(1),label='new-generation-return')
   command('c',0);command('e',1)
   assert memory(0x53000,4096)==bytes(4096) and memory(0x5ae0,8)==bytes(8)
   assert memory(0x30000,90112)==bytes(90112) and memory(0x60000,90112)==bytes(90112)
   p.stdin.write(b'q');p.stdin.flush();assert p.wait(timeout=5)==65
  except Exception as e:
   import traceback
   error=repr(e);(D/('FAIL-'+machine+'.json')).write_text(json.dumps({'error':error,'traceback':traceback.format_exc(),'serial':out.decode(errors='replace')},indent=2))
  finally:
   if p.poll() is None:p.kill();p.wait()
   for s in peers+[qs]:
    if s:s.close()
  rows.append({'machine':machine,'passed':error is None,'error':error,'cases':locals().get('CASES',[]),'wire':wire,'serial':out.decode(errors='replace')})
(D/'MULTIFLOW-VERIFICATION.json').write_text(json.dumps({'passed':all(r['passed'] for r in rows),'completed':sum(len(r['cases']) for r in rows),'rows':rows},indent=2)+'\n')
assert all(r['passed'] for r in rows),[(r['machine'],r['error']) for r in rows]
print('Config/neighbor controls passed:',[len(r['cases']) for r in rows])
