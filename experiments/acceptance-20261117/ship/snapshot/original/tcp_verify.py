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
   def tcp(slot,seq=0,ack=0,flags=2,payload=b'',sport=None,dport=None,sip=None,dip=None,options=b''):
    source=sip or (bytes([10,77,0,3]) if slot==0 else bytes([198,51,100,9]));dest=dip or (bytes([198,51,100,9]) if slot==0 else bytes([198,51,100,2]))
    sport=sport if sport is not None else (23456 if slot==0 else 443);dport=dport if dport is not None else(443 if slot==0 else 50000)
    segment=bytearray(struct.pack('!HHIIBBHHH',sport,dport,seq,ack,((20+len(options))//4)<<4,flags,4096,0,0)+options+payload)
    struct.pack_into('!H',segment,16,checksum(source+dest+b'\0\x06'+struct.pack('!H',len(segment))+segment))
    ip=bytearray(struct.pack('!BBHHHBBH4s4s',0x45,0,20+len(segment),123,0x4000,64,6,0,source,dest));struct.pack_into('!H',ip,10,checksum(ip))
    return (bytes.fromhex('025246320002025246320003' if slot==0 else'025246320004025246320005')+b'\x08\x00'+ip+segment).ljust(60,b'\0')
   def translated(b,slot,mapped=50000,clientport=23456):
    x=bytearray(b);x[:12]=bytes.fromhex('025246320005025246320004' if slot==0 else'025246320003025246320002');x[22]-=1
    if slot==0:x[26:30]=bytes([198,51,100,2]);x[34:36]=struct.pack('!H',mapped)
    else:x[30:34]=bytes([10,77,0,3]);x[36:38]=struct.pack('!H',clientport)
    x[24:26]=bytes(2);struct.pack_into('!H',x,24,checksum(x[14:34]));x[50:52]=bytes(2);length=int.from_bytes(x[16:18],'big')-20;struct.pack_into('!H',x,50,checksum(x[26:34]+b'\0\x06'+struct.pack('!H',length)+x[34:34+length]));return bytes(x)
   def check(slot,b,result=0,label='',mapped=50000,clientport=23456):
    table=memory(0x58000,1024);wanted=translated(b,slot,mapped,clientport) if result==0 else None
    runpacket(slot,b,result,wanted,label)
    if result:assert memory(0x58000,1024)==table,(label,'refused frame changed committed TCPstate')
    assert memory(0x59000,4096)==bytes(4096),'prospectiveTCPstate leaked'
   syn=tcp(0,seq=0xffffffff)
   runpacket(1,tcp(1,seq=9000,ack=0,flags=18),33,label='unsolicitedTCP-before-neighbor')
   runpacket(0,syn,0,arp_probe(0xc6336409),'SYN-owned-awaiting-resolution');assert memory(0x58000,1024)==bytes(1024)
   runpacket(1,arp_reply(),42,translated(syn,0),'ARP-releases-SYN-and-only-then-state',egress=1)
   assert int.from_bytes(memory(0x58000,8),'little')==1 and memory(0x59000,4096)==bytes(4096)
   check(0,syn,label='SYN-retransmit-same-ISN')
   check(0,tcp(0,seq=123),36,'differentSYN-ISN-rejected')
   check(1,tcp(1,seq=9000,ack=1,flags=18),36,'wrongSYNACK-ack')
   check(1,tcp(1,seq=9000,ack=0,flags=18),label='SYNACK-accepted-wrap')
   check(1,tcp(1,seq=9000,ack=0,flags=18),label='SYNACK-retransmit')
   check(0,tcp(0,seq=0,ack=9001,flags=16),label='handshake-finalACK')
   assert int.from_bytes(memory(0x58000,8),'little')==3
   check(0,tcp(0,seq=0,ack=9002,flags=16),36,'wrongACK-state-preserved')
   check(0,tcp(0,seq=1,ack=9001,flags=16),36,'outOfOrder-state-preserved')
   check(0,tcp(0,seq=0,ack=9001,flags=24,payload=b'hello'),label='outbound-data-exact')
   check(1,tcp(1,seq=9001,ack=5,flags=24,payload=b'world'),label='inbound-data-exact')
   check(0,tcp(0,seq=5,ack=9006,flags=16),label='dataACK-exact')
   check(0,tcp(0,seq=6,ack=9006,flags=17),36,'FINwrongSequence')
   check(0,tcp(0,seq=5,ack=9006,flags=0),33,'null-flags-denied')
   check(0,tcp(0,seq=5,ack=9006,flags=0xff),33,'invalid-flags-denied')
   check(0,tcp(0,seq=5,ack=9006,flags=16,dport=80),33,'default-deny-other-port')
   for label,at,xor,expected_code in [('TCPchecksum',50,1,35),('IPchecksum',24,1,35),('TCPoptions',46,16,32),('fragment',20,32,32)]:
    bad=bytearray(tcp(0,seq=5,ack=9006,flags=16));bad[at]^=xor;check(0,bytes(bad),expected_code,label)
   for ip in [bytes([198,51,100,255]),bytes([198,51,100,0]),bytes([10,77,0,255]),bytes([224,0,0,1]),bytes([127,0,0,1])]:
    check(0,tcp(0,sport=25001,dip=ip),33,'specialDestination-'+ip.hex())
   check(0,tcp(0,sport=0),33,'zeroTCPsourcePort')
   check(0,tcp(0,seq=5,ack=9006,flags=32),33,'URG-outside-profile')
   check(0,tcp(0,seq=5,ack=9005,flags=20),36,'unmatchedRST-denied')
   check(0,tcp(0,seq=5,ack=9006,flags=20),label='checkedRST-releases-state')
   assert memory(0x58000,128)==bytes(128)
   check(1,tcp(1,seq=9006,ack=5,flags=16),36,'return-after-reset-denied')
   for i in range(8):check(0,tcp(0,seq=i,sport=24000+i),label='allocate-session-'+str(i),mapped=50000+i)
   table=memory(0x58000,1024);assert sum(struct.unpack_from('<Q',table,i*128)[0]==1 for i in range(8))==8
   check(0,tcp(0,seq=99,sport=25000),38,'ninth-session-capacity-refusal');assert memory(0x58000,1024)==table
   check(1,tcp(1,seq=400,ack=8,flags=18,dport=50007),label='full-pool-return-isolation',clientport=24007)
   before=memory(0x58000,1024);gen=int.from_bytes(memory(0x55000,8),'little')
   config(gen-1,0,0xc6336400,24,0xc6336409,False,'stale-config-preserves-all-eight-TCPsessions');assert memory(0x58000,1024)==before
   gen=int.from_bytes(memory(0x55000,8),'little');config(gen,0,0xc6336400,24,0xc6336409,label='policy-reload-clearsTCP-and-owners')
   assert memory(0x58000,8192)==bytes(8192) and memory(0x56000,8192)==bytes(8192)
   check(1,tcp(1,seq=401,ack=8,flags=16,dport=50007),33,'return-after-reload-denied')
   # Full option bytes survive NAT; FIN consumes sequence space once.
   opts=bytes([2,4,5,180,1,3,3,7,4,2,1,1]);ts=bytes([1,1,8,10])+bytes(8)
   for label,opt in [('badMSS',bytes([2,3,5,0])),('duplicateMSS',bytes([2,4,5,180,2,4,5,180])),('badScale',bytes([3,3,15,1])),('badPadding',bytes([0,1,0,0])),('badSACK',bytes([5,9])+bytes(7)+bytes([0,0,0]))]:
    check(0,tcp(0,seq=256,options=opt),32,label)
   syn=tcp(0,seq=256,options=opts);runpacket(0,syn,0,arp_probe(0xc6336409),'optionSYN-awaitsARP')
   runpacket(1,arp_reply(),42,translated(syn,0),'optionSYN-released-exactly',egress=1)
   check(1,tcp(1,seq=7000,ack=257,flags=18,options=ts),label='SYNACKtimestamp')
   check(0,tcp(0,seq=257,ack=7001,flags=16,options=ts),label='finalACKtimestamp')
   check(0,tcp(0,seq=257,ack=7001,flags=16,options=bytes([254,2,1,1])),label='boundedUnknownTLV-preserved')
   check(0,tcp(0,seq=257,ack=7001,flags=24,payload=b'abc',options=ts),label='dataWithOptions-exactPayloadLength')
   check(1,tcp(1,seq=7001,ack=260,flags=24,payload=b'xyz',options=ts),label='serverDataWithOptions')
   check(0,tcp(0,seq=260,ack=7004,flags=17,options=ts),label='clientFIN-consumesOne')
   assert int.from_bytes(memory(0x58028,8),'little')==261
   check(0,tcp(0,seq=261,ack=7004,flags=24,payload=b'bad'),33,'dataAfterOwnFIN-denied')
   check(1,tcp(1,seq=7004,ack=261,flags=24,payload=b'hi',options=ts),label='halfClosedPeerMaySend')
   check(0,tcp(0,seq=261,ack=7006,flags=16),label='halfCloseACK')
   check(1,tcp(1,seq=7006,ack=261,flags=17,options=ts),label='serverFIN-consumesOne')
   check(0,tcp(0,seq=261,ack=7007,flags=16),label='finalCloseACK')
   assert int.from_bytes(memory(0x58000,8),'little')==4 and int.from_bytes(memory(0x58058,8),'little')==15
   held=memory(0x58050,8)
   check(1,tcp(1,seq=7006,ack=261,flags=17),label='duplicateServerFIN-noAdvance')
   check(0,tcp(0,seq=260,ack=7007,flags=17),label='duplicateClientFIN-noAdvance')
   assert memory(0x58050,8)==held
   check(0,tcp(0,seq=261,ack=7007,flags=20),33,'RSTcannotEndClosingQuarantine')
   check(0,tcp(0,seq=999),36,'newSYNcannotReuseQuarantinedTuple')
   assert memory(0x58050,8)==held
   command('c',0);command('e',1);assert memory(0x56000,16384)==bytes(16384)
   p.stdin.write(b'q');p.stdin.flush();assert p.wait(timeout=5)==65
  except Exception as e:
   import traceback
   error=repr(e);(D/('TCP-FAIL-'+machine+'.json')).write_text(json.dumps({'error':error,'traceback':traceback.format_exc(),'serial':out.decode(errors='replace'),'configDiagnostic':memory(0x55000,256).hex(),'rejectedFrame':memory(0x55500,64).hex()},indent=2))
  finally:
   if p.poll() is None:p.kill();p.wait()
   for s in peers+[qs]:
    if s:s.close()
  rows.append({'machine':machine,'passed':error is None,'error':error,'cases':locals().get('CASES',[]),'wire':wire,'serial':out.decode(errors='replace')})
(D/'TCP-VERIFICATION.json').write_text(json.dumps({'passed':all(r['passed'] for r in rows),'completed':sum(len(r['cases']) for r in rows),'rows':rows},indent=2)+'\n')
assert all(r['passed'] for r in rows),[(r['machine'],r['error']) for r in rows]
print('Neighbor/pending controls:',[len(r['cases']) for r in rows])
