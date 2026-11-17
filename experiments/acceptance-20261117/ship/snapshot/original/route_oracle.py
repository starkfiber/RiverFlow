"""Independent wire expectations only; no VM, network or device effects."""
import struct
def ip_checksum(b):
 if len(b)&1:b+=b'\0'
 s=sum(struct.unpack('!%dH'%(len(b)//2),b))
 while s>>16:s=(s&65535)+(s>>16)
 return (~s)&65535
def route_reply(b,kind=11,code=0):
 quote=b[14:42];icmp=bytearray(struct.pack('!BBHI',kind,code,0,0)+quote);struct.pack_into('!H',icmp,2,ip_checksum(bytes(icmp)))
 ip=bytearray(b[14:34]);ip[2:4]=struct.pack('!H',20+len(icmp));ip[6:8]=b'\0\0';ip[8:10]=bytes([64,1]);ip[10:12]=b'\0\0';ip[12:16]=bytes([10,77,0,2]);ip[16:20]=b[26:30];struct.pack_into('!H',ip,10,ip_checksum(bytes(ip)))
 return b[6:12]+b[:6]+b'\x08\x00'+bytes(ip)+bytes(icmp)
def echo_reply(b):
 out=bytearray(b);out[:6]=b[6:12];out[6:12]=b[:6];out[26:30]=b[30:34];out[30:34]=b[26:30];out[22]=64;out[24:26]=b'\0\0';struct.pack_into('!H',out,24,ip_checksum(bytes(out[14:34])));out[34]=0;out[36:38]=b'\0\0';length=int.from_bytes(out[16:18],'big')-20;struct.pack_into('!H',out,36,ip_checksum(bytes(out[34:34+length])));return bytes(out)
