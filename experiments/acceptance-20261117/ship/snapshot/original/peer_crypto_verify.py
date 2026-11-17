from pathlib import Path
import sys,json,subprocess,random,select,tempfile,os
sys.path.insert(0,str(Path(__file__).parent));from intent_client import *
D=Path('artifacts/rf2ship-secure-018');p=subprocess.Popen([str((D/'crypto-oracle').resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True);rng=random.Random(8439);checks=0
for i in range(150):
 key=bytes(rng.getrandbits(8) for _ in range(32));nonce=bytes(rng.getrandbits(8) for _ in range(12));aad=bytes(rng.getrandbits(8) for _ in range(i%129));data=bytes(rng.getrandbits(8) for _ in range((i*11)%129))
 p.stdin.write(json.dumps(dict(key=key.hex(),nonce=nonce.hex(),aad=aad.hex(),data=data.hex()))+'\n');p.stdin.flush();assert select.select([p.stdout],[],[],5)[0];v=json.loads(p.stdout.readline());actual=seal(key,nonce,aad,data);assert actual.hex()==v['data']+v['tag'];assert opened(key,nonce,aad,actual)==data;checks+=2
p.stdin.close();p.wait(timeout=5)
with tempfile.TemporaryDirectory(prefix='rf2-private-') as tmp:
 os.chmod(tmp,0o700);s=CredentialStore(Path(tmp)/'cred');a=os.urandom(32);b=os.urandom(32);boot=os.urandom(16);s.install(a,b,boot);assert [s.reserve()[3] for _ in range(3)]==[1,2,3];assert CredentialStore(s.path).reserve()[3]==4;checks+=2
 try:s.install(a,os.urandom(32),os.urandom(16));raise AssertionError('keyreuse')
 except ValueError:checks+=1
 os.chmod(s.path,0o644)
 try:s.reserve();raise AssertionError('publiccredentials')
 except ValueError:checks+=1
(D/'PEER-CRYPTO-VERIFICATION.json').write_text(json.dumps({'passed':True,'checks':checks,'scope':'stdlibpeer differential againstAppleCryptoKit; privatecredentialreopen/reuse/mode refusal. Not guest or independent securityaudit.'},indent=2)+'\n');print(checks,'peer/store checks passed')
