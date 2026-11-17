from pathlib import Path
import ctypes as C,random,subprocess,json
S=Path(__file__).resolve().parent;R=S.parents[2];A=R/'artifacts/evolution-20261117/ship';r=random.Random(3117);P=(1<<130)-5
for name in ['baseline','candidate']:
 wrapper=A/(name+'-limbs.c');wrapper.write_text('#include "'+str(S/(name+'.c'))+'"\nvoid check_mulp(u64*h,const u8*r){mulp(h,r);}\n')
 subprocess.run(['clang','-O2','-dynamiclib',str(wrapper),'-o',str(A/(name+'-limbs.dylib'))],check=True)
 lib=C.CDLL(str(A/(name+'-limbs.dylib')));f=lib.check_mulp;f.argtypes=[C.POINTER(C.c_uint64),C.c_void_p]
 cases=[(h,v) for h in [0,1,P-1,P-2,(1<<129),(1<<128)-1] for v in [0,1,(1<<128)-1,int.from_bytes(bytes.fromhex('ffffff0ffcffff0ffcffff0ffcffff0f'),'little')]]
 cases += [(r.randrange(P),r.getrandbits(128)) for _ in range(12000)]
 for h,v in cases:
  buf=(C.c_uint64*3)(h&((1<<64)-1),(h>>64)&((1<<64)-1),h>>128);rb=C.create_string_buffer(v.to_bytes(16,'little'));f(buf,rb)
  got=buf[0]+(buf[1]<<64)+(buf[2]<<128);assert got==(h*v)%P,(name,h,v,got,(h*v)%P)
 print(name,len(cases),'limb arithmetic checks pass')
(A/'LIMB-CORRECTNESS.json').write_text(json.dumps({'passed':True,'casesPerImplementation':len(cases),'oracle':'Python exact integer modular arithmetic, not timed','inputRange':'all canonical h, full 128-bit r including unclamped extrema','seed':3117},indent=2)+'\n')
