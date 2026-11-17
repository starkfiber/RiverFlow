"""Two active NICs, persistent rings and independent IPv4/UDP peers."""
from pathlib import Path
import subprocess,socket,os,select,time,json,tempfile,threading,re,struct,hashlib,sys
sys.path.insert(0,str(Path(__file__).parent));from wire_peer import exchange,exact,checksum
from route_oracle import route_reply,echo_reply,ip_checksum
from intent_client import CredentialStore,Client,seal,opened,REQ,REP,INNER,UnknownOutcome
D=Path('artifacts/rf2ship-secure-018');rows=[];ADVERSARIAL='--adversarial' in sys.argv
for machine in ['pc','q35']:
 with tempfile.TemporaryDirectory(prefix='rf2if-',dir='/tmp') as tmp:
  paths=[str(Path(tmp)/('p%d.sock'%i)) for i in range(2)];qpath=str(Path(tmp)/'q.sock')
  cmd=['qemu-system-x86_64','-machine',machine,'-cpu','qemu64','-accel','tcg','-m','32','-display','none','-monitor','none','-nic','none','-serial','stdio','-qmp',f'unix:{qpath},server=on,wait=off','-drive',f'file={D}/rf2ship.img,format=raw,if=floppy,readonly=on','-device','isa-debug-exit,iobase=0xf4,iosize=0x04']
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
   captures=[]
   reconnects=0
   def provision(c,s,b,expect=0):
    mark=len(out);p.stdin.write(b'B'+(c+s+b).hex().encode()+b'\n');p.stdin.flush();until(b'RF2Ship> ',mark)
    m=re.search(rb'Credentials result=0x([0-9a-f]+)',out[mark:]);assert m and int(m[1],16)==expect,'credential setup refused'
   captures=[]
   def exchange(wire,label='encryptedExchange'):
    global reconnects
    if peers[0].fileno()<0:
     endpoint=Path(paths[0]);st=endpoint.lstat();assert not endpoint.is_symlink() and endpoint.parent.stat().st_mode&0o077==0 and st.st_uid==os.getuid()
     peer=socket.socket(socket.AF_UNIX);peer.settimeout(5);peer.connect(str(endpoint));peers[0]=peer;reconnects+=1
     raise ConnectionError('private peer reconnected; fresh session required')
    b=packet(0,wire,dest_port=9000,dest_ip=bytes([10,77,0,2]));peers[0].sendall(struct.pack('!I',len(b))+b);mark=len(out);p.stdin.write(b'r');p.stdin.flush();until(b'RF2Ship> ',mark)
    m=re.search(rb'Relay result=0x([0-9a-f]+)',out[mark:]);assert m,'missing guest result'
    if int(m[1],16)!=0:raise TimeoutError('no authenticated reply')
    n=struct.unpack('!I',exact(peers[0],4))[0];actual=exact(peers[0],n)
    assert len(actual)==170 and actual[:12]==bytes.fromhex('025246320003025246320002')
    assert actual[22:24]==bytes([64,17]) and actual[26:34]==bytes([10,77,0,2,10,77,0,3])
    assert checksum(actual[14:34])==0 and checksum(actual[26:34]+b'\0\x11'+struct.pack('!H',136)+actual[34:])==0
    assert memory(0x51000,4096)==bytes(4096) and memory(0x5c000,4096)==bytes(4096)
    assert not select.select([peers[1]],[],[],.01)[0],'IntentleakedtoWAN'
    captures.append({'label':label,'RXcipher':wire.hex(),'TXcipher':actual[42:].hex()});return actual[42:]
   def refused(wire,label,code=33):
    before=memory(0x5a000,96);seq=memory(0x5b058,8)
    runpacket(0,packet(0,wire,dest_port=9000,dest_ip=bytes([10,77,0,2])),code,label=label)
    assert memory(0x5a000,96)==before and memory(0x5b058,8)==seq
    assert memory(0x5c000,4096)==bytes(4096)
   ckey=os.urandom(32);skey=os.urandom(32);boot=os.urandom(16)
   store=CredentialStore(Path(tmp)/'credentials');provision(ckey,skey,boot);store.install(ckey,skey,boot);remember('fresh-directional-credentials-provisioned-no-echo')
   client=Client(store,exchange);hello=client.connect();assert hello[2]==13;remember('authenticated-encrypted-handshake')
   result=client.call(1,1,1000,b'one');assert result[2:6]==(0,1,3,int.from_bytes(b'one','little'));remember('authenticated-encrypted-submit')
   saved=captures[-1]['RXcipher'];reply=captures[-1]['TXcipher'];refused(bytes.fromhex(saved),'exact-replay-refused')
   before=memory(0x5a028,8);result=client.call(1,1,1000,b'two');assert result[2]==3 and memory(0x5a028,8)==before;remember('new-nonce-duplicate-logical-ID-preserves-value')
   def fresh_wire(key=None):
    c,s,b,seq=store.reserve();head=REQ+b+struct.pack('<QQ',client.epoch,seq);body=INNER+struct.pack('<8Q',4,client.epoch,0,0,0,0,0,0)
    return head+seal(c if key is None else key,struct.pack('<IQ',client.epoch,seq),head,body)
   for at,label,code in [(0,'unknown-envelope',32),(8,'boot-ID-tamper',33),(24,'epoch-tamper',33),(32,'sequence-poisoning-tamper',33),(40,'ciphertext-tamper',33),(127,'tag-tamper',33)]:
    bad=bytearray(fresh_wire());bad[at]^=1;refused(bytes(bad),label,code)
   refused(fresh_wire(skey),'wrong-direction-key-refused')
   refused(fresh_wire(os.urandom(32)),'wrong-key-refused')
   reflected=bytearray.fromhex(reply);reflected[:8]=REQ;refused(bytes(reflected),'direction-reflection-refused')
   refused(b'RF2IC01!'+bytes(64),'plaintext-downgrade-refused',32)
   result=client.call(4);assert result[2]==0 and result[3]==1;remember('observation-remains-authenticated')
   for key in ['f','g','a','b','t','u','v','d','p','I','J']:
    before=memory(0x5a000,96);mark=len(out);p.stdin.write(key.encode());p.stdin.flush();until(b'RF2Ship> ',mark)
    assert b'Debug operation disabled.' in out[mark:] and memory(0x5a000,96)==before,(key,'debugbypass');remember('debug-disabled-'+key)
   oldepoch=client.epoch;peers[0].close()
   result=client.call(4);assert result[2]==0 and reconnects==1 and client.epoch>oldepoch;remember('automatic-private-socket-redial-and-authenticated-renegotiation')
   # Real local interface close/reopen invalidates the application session, not keys/counter.
   prior=client.epoch;command('c',0);command('e',1);command('o',0);command('i',1)
   result=client.call(4);assert result[2]==0 and client.epoch>prior;remember('automatic-reconnect-renegotiates-after-interface-reset')
   refused(bytes.fromhex(saved),'old-session-and-sequence-refused-after-reconnect')
   second=Client(CredentialStore(Path(tmp)/'credentials'),exchange);second.connect();assert second.epoch>client.epoch;remember('client-restart-reserves-durable-new-nonce')
   # Authenticated protocol still reports invalid caller-supplied time without changing a value.
   result=second.call(1,1,1000,b'new');assert result[2]==0;remember('new-session-submit')
   oldwire=bytes.fromhex(captures[-1]['RXcipher']);oldreply=bytes.fromhex(captures[-1]['TXcipher']);oldboot=boot
   mark=len(out);q('system_reset');until(b'RF2Ship> ',mark);command('o',0);command('i',1)
   try:second.call(4);raise AssertionError('bootwithoutcredentialsaccepted')
   except ConnectionError:remember('absent-boot-provisioner-fails-closed')
   c2=os.urandom(32);s2=os.urandom(32);boot2=os.urandom(16);provision(c2,s2,boot2);store.install(c2,s2,boot2)
   # Existing client discovers fresh credentials through the trusted provider.
   result=second.call(4);assert result[2]==0 and second.boot==boot2;remember('automatic-crossboot-reconnect-with-fresh-provisioned-credentials')
   refused(oldwire,'captured-crossboot-request-refused')
   rebound=bytearray(oldwire);rebound[8:24]=boot2;refused(bytes(rebound),'old-ciphertext-rebound-to-new-boot-refused')
   stale=Client(store,lambda wire:oldreply)
   try:stale.connect();raise AssertionError('stale-server-reply-accepted')
   except ValueError:remember('captured-crossboot-reply-not-trusted')
   mark=len(out);p.stdin.write(b'U');p.stdin.flush();until(b'RF2Ship> ',mark);assert memory(0x5b000,80)==bytes(80) and memory(0x5b050,8)==(2).to_bytes(8,'little');remember('credential-erase-refuses-further-use')
   refused(bytes.fromhex(captures[-1]['RXcipher']),'erased-credential-refuses',33)
   provision(os.urandom(32),os.urandom(32),os.urandom(16),47);remember('no-reprovision-without-fresh-boot')
   command('c',0);command('e',1);assert memory(0x56000,16384)==bytes(16384) and memory(0x5c000,4096)==bytes(4096)
   p.stdin.write(b'q');p.stdin.flush();assert p.wait(timeout=5)==65
  except Exception as e:
   import traceback
   error=repr(e);(D/('FAIL-'+machine+'.json')).write_text(json.dumps({'error':error,'traceback':traceback.format_exc(),'serial':out.decode(errors='replace')},indent=2))
  finally:
   if p.poll() is None:p.kill();p.wait()
   for s in peers+[qs]:
    if s:s.close()
  rows.append({'machine':machine,'passed':error is None,'error':error,'cases':locals().get('CASES',[]),'wire':wire,'encryptedCaptures':locals().get('captures',[]),'serial':out.decode(errors='replace')})
(D/'SECURE-VERIFICATION.json').write_text(json.dumps({'passed':all(r['passed'] for r in rows),'completed':sum(len(r['cases']) for r in rows),'rows':rows},indent=2)+'\n')
assert all(r['passed'] for r in rows),[(r['machine'],r['error']) for r in rows]
print('Neighbor/pending controls:',[len(r['cases']) for r in rows])
