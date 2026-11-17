from pathlib import Path
import ctypes as C,struct,random,subprocess,json,hashlib
R=Path(__file__).resolve().parents[3]; A=R/'artifacts/evolution-20261117/ship'
libs=[C.CDLL(str(A/(n+'.dylib'))) for n in ['baseline','candidate']]
for lib in libs:lib.rf2_aead.argtypes=[C.c_void_p];lib.rf2_aead.restype=C.c_int
p=subprocess.Popen([str(A/'crypto-oracle')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
def run(lib,key,nonce,aad,data,tag=None,an=None,n=None):
 a=C.create_string_buffer(aad or b'\0');b=C.create_string_buffer(data or b'\0');t=C.create_string_buffer(tag or bytes(16),16)
 raw=struct.pack('<Q',tag is not None)+key+nonce+bytes(4)+struct.pack('<5Q',C.addressof(a),len(aad) if an is None else an,C.addressof(b),len(data) if n is None else n,C.addressof(t))
 ctx=C.create_string_buffer(raw);status=lib.rf2_aead(ctx);return status,b.raw[:len(data)],t.raw
r=random.Random(181711);checks=0
lengths=[0,1,15,16,17,31,32,63,64,65,127,128]
for i in range(1100):
 key=r.randbytes(32);nonce=r.randbytes(12);aad=r.randbytes(lengths[i%12] if i<144 else r.randrange(129));data=r.randbytes(lengths[(i//12)%12] if i<144 else r.randrange(129))
 p.stdin.write(json.dumps(dict(op='seal',key=key.hex(),nonce=nonce.hex(),aad=aad.hex(),data=data.hex()))+'\n');p.stdin.flush();q=json.loads(p.stdout.readline())
 expected=(0,bytes.fromhex(q['data']),bytes.fromhex(q['tag']))
 for lib in libs:
  sealed=run(lib,key,nonce,aad,data);assert sealed==expected,(i,sealed,expected);checks+=1
  opened=run(lib,key,nonce,aad,sealed[1],sealed[2]);assert opened[:2]==(0,data);checks+=1
  bad=bytearray(sealed[2]);bad[i%16]^=1
  failed=run(lib,key,nonce,aad,sealed[1],bytes(bad));assert failed==(1,sealed[1],bytes(bad));checks+=1
  if aad:
   bad_aad=bytearray(aad);bad_aad[0]^=1
   assert run(lib,key,nonce,bytes(bad_aad),sealed[1],sealed[2])[:2]==(1,sealed[1]);checks+=1
  for an,n in [(129,len(data)),(len(aad),129),(2**64-1,len(data))]:
   assert run(lib,key,nonce,aad,data,an=an,n=n)==(2,data,bytes(16));checks+=1
p.stdin.close();p.wait(timeout=5);assert p.returncode==0
out={'passed':True,'checks':checks,'independentOracle':'Apple CryptoKit ChaChaPoly','seed':181711,'randomAndBoundaryInputs':1100,'lengthCrossProduct':144,'scope':'host-native compiled C component, not guest integration or constant-time certification','sources':{n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in ['baseline.c','candidate.c','CryptoOracle.swift']}}
(A/'CORRECTNESS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
