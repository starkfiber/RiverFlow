"""Native HMAC construction vs RFC4231 and Python hashlib; no certification."""
from pathlib import Path
import hashlib,hmac,random,subprocess,time,json,re
R=Path(__file__).resolve().parents[2];D=R/'artifacts/trust-0.18'/('hmac-'+str(time.time_ns()));D.mkdir(parents=True);L=R/'examples/evidence-contract/lib'
parts=['profile RF2_SYSTEM_A64_V1\n','fn copy_bytes(dst,src,n)\n let i=0\n while i<n\n  do store8(dst+i,load8(src+i))\n  set i=i+1\n end\n return 0\nend\n']
for name in ['sha256.rf2','auth.rf2']:parts.append(re.sub(r'^module .*\n','', (L/name).read_text()))
parts.append('''fn main(argc,argv)
 let key=buffer("probe-key",4097)
 let msg=buffer("probe-msg",16385)
 let kn=read_file(load64(argv+8),key,4096)
 let n=read_file(load64(argv+16),msg,16384)
 if any(kn>4096,n>16384)
  return 2
 end
 let digest=hmac256(key,kn,msg,n)
 return write(1,digest,32)!=32
end
''');source=D/'probe.rf2';source.write_text(''.join(parts));rows=[]
cases=[(bytes([0x0b])*20,b'Hi There','b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7'),(b'Jefe',b'what do ya want for nothing?','5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843'),(b'\xaa'*20,b'\xdd'*50,'773ea91e36800e46854db8ebd09181a72959098b3ef8c122d9635514ced565fe'),(bytes(range(1,26)),b'\xcd'*50,'82558a389a443c0ea4cc819899f2083a85f0faa3e578f8077a2e3ff46729665b'),(b'\x0c'*20,b'Test With Truncation','a3b6167473100ee06e0c796c2955552b'),(b'\xaa'*131,b'Test Using Larger Than Block-Size Key - Hash Key First','60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54'),(b'\xaa'*131,b'This is a test using a larger than block-size key and a larger than block-size data. The key needs to be hashed before being used by the HMAC algorithm.','9b09ffa71b942fcb27635fbcd5b0e944bfdc63644f0713938a7f51535c3a35e2')]
rng=random.Random(184231)
for i in range(90):
 k=bytes(rng.randrange(256)for _ in range(rng.choice([0,1,20,32,63,64,65,131,256])));m=bytes(rng.randrange(256)for _ in range(rng.choice([0,1,55,56,63,64,65,127,1024,16384])));cases.append((k,m,None))
for opt in [False,True]:
 exe=D/('probe-opt'if opt else'probe-default');p=subprocess.run([R/'output/native-compiler/rf2c',source,exe]+(['--opt']if opt else[]),capture_output=True,timeout=60);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True)
 for i,(key,msg,official)in enumerate(cases):
  kf=D/'key';mf=D/'message';kf.write_bytes(key);mf.write_bytes(msg);p=subprocess.run([exe,kf,mf],capture_output=True,timeout=10);expected=hmac.new(key,msg,hashlib.sha256).digest();assert p.returncode==0 and p.stdout==expected,(opt,i,p.stdout.hex(),expected.hex());assert official is None or p.stdout.hex().startswith(official)
  rows.append({'optimized':opt,'case':i+1,'rfc4231':i<7,'passed':True,'keyBytes':len(key),'messageBytes':len(msg),'tag':p.stdout.hex()})
report={'date':'2026-11-13','passed':True,'checks':len(rows),'rfcCases':7,'freshSeededCases':90,'seed':184231,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'primarySource':'https://www.rfc-editor.org/rfc/rfc4231.txt','results':rows,'scope':'Native default/optimized sevenRFCvectors plus90seeded cases. Full256bit tags; RFCcase5compares supplied128bit prefix plus fullPython result. Conformance evidence, not cryptographic certification or sidechannel proof.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(rows),'report':str(D/'report.json')},indent=2))
