"""Independent hashlib oracle for the exact40byte scalar SHA teaching application."""
from pathlib import Path
import hashlib,json,os,random,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();D=R/'artifacts/sha40'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
source=R/'examples/sha40/main.rf2';module=R/'examples/sha40/rounds.rf2';rows=[];rng=random.Random(29040256)
def run(args,data=None,**kw):return subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=40,**kw)
# Generator reproducibility is distinct from digest correctness.
prior=module.read_bytes();q=run(['python3',R/'tools/generate-sha40.py']);assert q.returncode==0 and module.read_bytes()==prior
samples=[bytes(40),bytes([255])*40,bytes(range(40)),b'a'*40]+[bytes(rng.randrange(256)for _ in range(40))for _ in range(124)]
for opt in [False,True]:
 cache=D/f'units-{opt}';cache.mkdir(mode=0o700);oracle=D/f'clean-{opt}';q=run([C,source,oracle,'--compact',*(['--opt']if opt else[])]);assert q.returncode==0,q.stderr;unsigned=oracle.read_bytes()
 for route in ['cold','warm']:
  out=D/f'{route}-{opt}';q=run([C,source,out,'--compact',*(['--opt']if opt else[]),'--reuse-cache',cache]);assert q.returncode==0 and out.read_bytes()==unsigned,q.stderr;receipt=json.loads(Path(str(out)+'.reuse.json').read_text());assert receipt['reused']==(4 if route=='warm' and opt else 0),receipt
  rows.append({'case':route+' clean-byte equality','optimized':opt,'expectedReuse':4 if route=='warm' and opt else 0,'reuse':receipt,'unsignedSHA256':hashlib.sha256(unsigned).hexdigest()})
 binary=D/f'warm-{opt}';assert run(['/usr/bin/codesign','-s','-',binary]).returncode==0
 for i,data in enumerate(samples):
  q=run([binary],data);assert q.returncode==0 and q.stdout==hashlib.sha256(data).digest() and not q.stderr,(opt,i,q.returncode,q.stderr,q.stdout.hex())
  rows.append({'case':'complete digest','optimized':opt,'sample':i,'inputSHA256':hashlib.sha256(data).hexdigest(),'digest':q.stdout.hex()})
 for n in [0,1,7,8,31,39,41,42,64,4096,1048576]:
  q=run([binary],b'a'*n);assert q.returncode==4 and q.stdout==b'',(opt,n,q.returncode)
  rows.append({'case':'length refusal','optimized':opt,'bytes':n})
 assert run([binary,'unexpected'],bytes(40)).returncode==2
 assert run([binary],preexec_fn=lambda:os.close(0)).returncode==3
 assert run([binary],bytes(40),preexec_fn=lambda:os.close(1)).returncode==5
 rows.append({'case':'argument and descriptor refusals','optimized':opt,'checks':3})
report=dict(passed=True,schema='rf2.sha40.verification.v1',rows=rows,digestCases=256,lengthRefusals=22,descriptorAndArgumentRefusals=6,generatorReproducible=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),sourceFiles={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [source,module,R/'tools/generate-sha40.py']},controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits='Complete SHA-256 outputs for exactly40byte inputs, one Mac. Four scalar helpers recompute compression for separate output pairs; useful as readable/compiler reuse workload, not a recommended cryptographic library or runtime speed improvement. No protection against side channels or other-length SHA API promised.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'passed':True,'digestCases':256,'lengthRefusals':22}))
