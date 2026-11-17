"""Independent restricted IPv4/UDP wire oracle and echo peer. Test fixtures only."""
import struct,socket
def exact(s,n):
 out=b''
 while len(out)<n:
  b=s.recv(n-len(out))
  if not b:raise EOFError('peer closed')
  out+=b
 return out
def checksum(b):
 if len(b)%2:b+=b'\0'
 total=sum(struct.unpack('!%dH'%(len(b)//2),b))
 while total>>16:total=(total&65535)+(total>>16)
 return (~total)&65535
def validate(frame,slot,generation,sequence):
 assert len(frame)==74,len(frame)
 local=bytes.fromhex('0252463200')+bytes([2+slot*2]);peer=local[:-1]+bytes([3+slot*2])
 assert frame[:6]==peer and frame[6:12]==local
 assert frame[12:14]==b'\x08\x00'
 ip=frame[14:34];udp=frame[34:]
 assert ip[0]==0x45 and struct.unpack_from('!H',ip,2)[0]==60
 assert ip[6:8]==b'\x40\x00' and ip[8]==64 and ip[9]==17
 assert ip[12:16]==bytes([10,77+slot,0,2]) and ip[16:20]==bytes([10,77+slot,0,3])
 assert checksum(ip)==0
 assert struct.unpack('!HHH',udp[:6])==(40000,40001,40)
 pseudo=ip[12:20]+b'\0\x11'+struct.pack('!H',40)
 assert udp[6:8]!=b'\0\0' and checksum(pseudo+udp)==0
 assert udp[8:16]==b'RF2IP08!'
 assert struct.unpack_from('<Q',udp,16)[0]==generation
 assert struct.unpack_from('<I',udp,24)[0]==sequence
 assert udp[28:]==bytes(12)
def echo(frame,mode='normal'):
 out=bytearray(frame[6:12]+frame[:6]+frame[12:]);out[26:30],out[30:34]=out[30:34],out[26:30];out[34:36],out[36:38]=out[36:38],out[34:36]
 if mode=='ether-type':out[12:14]=b'\x86\xdd'
 if mode=='ihl':out[14]=0x46
 if mode=='tcp':out[23]=6
 if mode=='wrong-mac':out[11]=99
 if mode=='udp-length':out[38:40]=b'\0\x27'
 if mode=='stale':struct.pack_into('<Q',out,50,max(0,struct.unpack_from('<Q',out,50)[0]-1))
 if mode=='fragment':out[20:22]=b'\x20\x00'
 if mode=='total-length':out[16:18]=b'\0\x3b'
 if mode=='ttl-zero':out[22]=0
 if mode=='wrong-ip':out[29]^=1
 out[24:26]=b'\0\0';struct.pack_into('!H',out,24,checksum(bytes(out[14:34])))
 out[40:42]=b'\0\0';pseudo=bytes(out[26:34])+b'\0\x11'+struct.pack('!H',40);value=checksum(pseudo+bytes(out[34:]));struct.pack_into('!H',out,40,value or 65535)
 if mode=='ip-checksum':out[24]^=1
 if mode=='udp-checksum':out[40]^=1
 if mode=='udp-zero':out[40:42]=b'\0\0'
 if mode=='oversize':out+=b'X'
 return bytes(out)
def exchange(s,slot,generation,start,mode,receipt):
 frames=[]
 try:
  for i in range(4):
   size=struct.unpack('!I',exact(s,4))[0];assert size==74,size
   frame=exact(s,size);validate(frame,slot,generation,start+i);frames.append(frame)
  receipt['TX']=[f.hex() for f in frames]
  if mode=='disconnect':s.close();receipt['passed']=True;return
  replies=[echo(f,mode if i==0 else 'normal') for i,f in enumerate(frames)]
  if mode=='reorder':replies.reverse()
  if mode=='duplicate':replies[1]=replies[0]
  for f in replies:s.sendall(struct.pack('!I',len(f))+f)
  receipt.update(passed=True,RX=[f.hex() for f in replies])
 except Exception as e:receipt.update(passed=False,error=repr(e))
