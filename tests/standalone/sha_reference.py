"""Independent scalar SHA-256 compression oracle for development tests."""
import struct
def rot(x,n):return ((x>>n)|(x<<(32-n)))&0xffffffff
def compress(state,data,k):
 for off in range(0,len(data),64):
  w=list(struct.unpack('>16I',data[off:off+64]))
  for i in range(16,64):
   x=w[i-15];y=w[i-2];w.append((w[i-16]+(rot(x,7)^rot(x,18)^(x>>3))+w[i-7]+(rot(y,17)^rot(y,19)^(y>>10)))&0xffffffff)
  a,b,c,d,e,f,g,h=state
  for i in range(64):
   t1=(h+(rot(e,6)^rot(e,11)^rot(e,25))+((e&f)^((~e)&g))+k[i]+w[i])&0xffffffff;t2=((rot(a,2)^rot(a,13)^rot(a,22))+((a&b)^(a&c)^(b&c)))&0xffffffff
   a,b,c,d,e,f,g,h=(t1+t2)&0xffffffff,a,b,c,(d+t1)&0xffffffff,e,f,g
  state=[(x+y)&0xffffffff for x,y in zip(state,[a,b,c,d,e,f,g,h])]
 return state
