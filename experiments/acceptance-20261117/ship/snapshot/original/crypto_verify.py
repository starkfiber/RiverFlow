from pathlib import Path
import ctypes,subprocess,json,random,struct,hashlib,select
D=Path('artifacts/rf2ship-secure-018');lib=ctypes.CDLL(str((D/'aead-host.dylib').resolve()));f=lib.rf2_aead;f.argtypes=[ctypes.c_void_p];f.restype=ctypes.c_int
p=subprocess.Popen([str((D/'crypto-oracle').resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
def oracle(key,nonce,aad,data):
 p.stdin.write(json.dumps(dict(op='seal',key=key.hex(),nonce=nonce.hex(),aad=aad.hex(),data=data.hex()))+'\n');p.stdin.flush();assert select.select([p.stdout],[],[],5)[0],'oracle response timeout';return json.loads(p.stdout.readline())
def run(key,nonce,aad,data,tag=None):
 a=ctypes.create_string_buffer(aad or b'\0');b=ctypes.create_string_buffer(data or b'\0');t=ctypes.create_string_buffer(tag or bytes(16),16)
 ctx=ctypes.create_string_buffer(96);raw=struct.pack('<Q',tag is not None)+key+nonce+bytes(4)+struct.pack('<5Q',ctypes.addressof(a),len(aad),ctypes.addressof(b),len(data),ctypes.addressof(t));assert len(raw)==96;ctypes.memmove(ctx,raw,96)
 status=f(ctx);return status,b.raw[:len(data)],t.raw
r=random.Random(8439);cases=0
for i in range(300):
 key=r.randbytes(32) if hasattr(r,'randbytes') else bytes(r.getrandbits(8) for _ in range(32));nonce=bytes(r.getrandbits(8) for _ in range(12));aad=bytes(r.getrandbits(8) for _ in range(i%129));plain=bytes(r.getrandbits(8) for _ in range((i*17)%129))
 q=oracle(key,nonce,aad,plain);status,c,tag=run(key,nonce,aad,plain);assert status==0 and c.hex()==q['data'] and tag.hex()==q['tag'],i
 status,opened,_=run(key,nonce,aad,c,tag);assert status==0 and opened==plain
 bad=bytearray(tag);bad[i%16]^=1;status,unchanged,_=run(key,nonce,aad,c,bytes(bad));assert status==1 and unchanged==c
 cases+=3
p.stdin.close();p.wait(timeout=5);assert p.returncode==0
(D/'CRYPTO-HOST-VERIFICATION.json').write_text(json.dumps({'passed':True,'checks':cases,'oracle':'AppleCryptoKitChaChaPoly','scope':'Boundedoriginalreferenceport, independenthostdifferential; notguestqualification orconstanttimecertification','sourceSHA256':hashlib.sha256(Path('experiments/rf2ship/secure-transport-018/aead_reference.c').read_bytes()).hexdigest()},indent=2)+'\n');print(cases,'host crypto differential checks passed')
