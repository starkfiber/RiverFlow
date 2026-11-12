"""Finite native replay-capsule and algebraic tests; developer oracle only."""
from pathlib import Path
import subprocess,json,time,random,hashlib,struct,os
R=Path(__file__).resolve().parents[2];D=R/'artifacts/contract-next'/('capsule-'+str(time.time_ns()));D.mkdir(parents=True)
rows=[];binaries=[];rng=random.Random(20261112)
def plan(data,ops,budget=None,allow=7):
 words=['RF2E1','allow',str(allow),'budget',str(2*len(data)*len(ops)if budget is None else budget),'input',str(len(data)),*map(str,data),'steps',str(len(ops))]
 for c,a in ops:words += [c]+([]if c=='reverse'else[str(a)])
 return (' '.join(words)+'\n').encode()
def invoke(exe,args):
 p=subprocess.run([str(exe),*map(str,args)],capture_output=True,timeout=10);assert not p.stderr,p.stderr
 return p.returncode,p.stdout
try:
 for opt in [False,True]:
  exe=D/('runner-opt'if opt else'runner-default');p=subprocess.run(['python3',R/'tools/build-contract.py',exe]+(['--opt']if opt else[]),capture_output=True,timeout=60);assert p.returncode==0,p.stderr
  binaries.append(json.loads(exe.with_suffix('.build.json').read_text()));path=D/'plan';cap=D/'capsule'
  raw=plan([1,2,3],[('add',5),('reverse',0),('xor',2)]);path.write_bytes(raw)
  rc,out=invoke(exe,[path]);base=json.loads(out);assert rc==0 and base['output']==[10,5,4]
  cc,capsule=invoke(exe,['capsule',path]);assert cc==0
  tokens=capsule.split();assert tokens[:2]==[b'RF2C1',b'source']and tokens[3]==b'receipt'and tokens[5]==b'plan'and len(tokens)==7
  assert tokens[2].decode()==base['source_identity']and tokens[4].decode()==base['receipt']and bytes.fromhex(tokens[6].decode())==raw
  cap.write_bytes(capsule);rr,replay=invoke(exe,['replay',cap]);assert rr==0 and json.loads(replay)==base
  rows.append({'mode':opt,'test':'exact native export/fresh-process replay','passed':True})
  # All one-character digest mutations and every plan hex character are tested.
  for field in [2,4,6]:
   for i in range(len(tokens[field])):
    t=tokens.copy();mut=bytearray(t[field]);mut[i]=ord('0')if mut[i]!=ord('0')else ord('1');t[field]=bytes(mut);cap.write_bytes(b' '.join(t)+b'\n');rc,rep=invoke(exe,['replay',cap]);j=json.loads(rep);assert rc!=0 and j.get('published')is False,(field,i,rc,j)
    rows.append({'mode':opt,'test':f'bound-field-{field}-{i}','passed':True})
  invalid=[b'',b'RF2C2',capsule+b'extra',capsule.replace(b'plan ',b'plan f',1),capsule.replace(b'RF2C1',b'RF2C1\x00',1),b'X'*18001]
  invalid += [b' '.join(tokens[:6]+[b'a'*16386]),b' '.join(tokens[:2]+[b'0'*63]+tokens[3:]),b' '.join(tokens[:4]+[b'0'*65]+tokens[5:])]
  for i,x in enumerate(invalid):
   cap.write_bytes(x);rc,rep=invoke(exe,['replay',cap]);assert rc!=0 and json.loads(rep).get('published')is False
   rows.append({'mode':opt,'test':f'malformed-{i}','passed':True})
  # Framing whitespace is allowed, not included in the raw plan digest.
  cap.write_bytes(b'\t\r\n'.join(tokens)+b'\r\n');rc,rep=invoke(exe,['replay',cap]);assert rc==0 and json.loads(rep)==base
  rows.append({'mode':opt,'test':'allowed outer whitespace','passed':True})
  for i in range(150):
   x=bytearray(capsule);pos=rng.randrange(len(x));x[pos]=rng.randrange(256);cap.write_bytes(x);rc,rep=invoke(exe,['replay',cap]);j=json.loads(rep)
   assert (rc==0 and j==base)or(rc!=0 and j.get('published')is False),(i,pos,j)
   rows.append({'mode':opt,'test':f'fresh mutation {i}','passed':True})
  # Legitimate failure capsules preserve the exact error and original output.
  for name,raw in [('overflow',plan([250],[('xor',1),('add',10)])),('denied',plan([1],[('xor',1)],allow=0)),('budget',plan([1],[('xor',1)],budget=1)),('max-file',plan([1],[('xor',1)]).ljust(8192,b' '))]:
   path.write_bytes(raw);rc,rep=invoke(exe,[path]);cc,capsule2=invoke(exe,['capsule',path]);assert cc==rc;cap.write_bytes(capsule2);rr,replayed=invoke(exe,['replay',cap]);assert rr==rc and json.loads(rep)==json.loads(replayed)
   rows.append({'mode':opt,'test':name+' capsule','passed':True})
  # Negative security control: a sender can recompute an unsigned checksum.
  # Acceptance here demonstrates the authentication boundary, not tamper resistance.
  forged_plan=plan([9],[('xor',2)]);forged_receipt=hashlib.sha256(b'RF2-EVIDENCE-CONTRACT-1'+base['source_identity'].encode()+hashlib.sha256(forged_plan).digest()+hashlib.sha256(bytes([11])).digest()+struct.pack('<6Q',0,0,0,0,0,2)).hexdigest()
  cap.write_bytes(b'RF2C1 source '+base['source_identity'].encode()+b' receipt '+forged_receipt.encode()+b' plan '+forged_plan.hex().encode()+b'\n');rc,rep=invoke(exe,['replay',cap]);forged=json.loads(rep);assert rc==0 and forged['input']==[9]and forged['output']==[11]
  rows.append({'mode':opt,'test':'recomputed unsigned capsule accepted','passed':True,'boundary':'Integrity is not sender authentication','accepted':True})
  # A named pipe with no writer previously blocked at open; it must now refuse.
  fifo=D/'idle-fifo';os.mkfifo(fifo)
  try:
   for prefix in [[],['capsule'],['replay']]:
    result=subprocess.run([str(exe),*prefix,str(fifo)],capture_output=True,timeout=2);obj=json.loads(result.stdout);assert result.returncode!=0 and 'output'not in obj and 'error'in obj
    rows.append({'mode':opt,'test':'idle FIFO refuses '+str(prefix),'passed':True})
  finally:fifo.unlink()
  # Independent algebraic/metamorphic checks use complete results.
  families=[]
  for i in range(40):
   data=[rng.randrange(256)for _ in range(rng.randrange(129))];a=rng.randrange(256);b=rng.randrange(256)
   families.extend([(data,[('xor',a),('xor',a)],data,'xor involution'),(data,[('reverse',0),('reverse',0)],data,'reverse involution'),(data,[('xor',a),('xor',b)],[v^a^b for v in data],'xor fusion'),(data,[('reverse',0),('xor',a)],[v^a for v in data[::-1]],'reverse/map commute')])
   amount=rng.randrange(128);safe=[rng.randrange(256-2*amount)for _ in range(len(data))];families.append((safe,[('add',amount),('add',amount)],[v+2*amount for v in safe],'checked add composition'))
  families.extend([([1],[('add',1),('xor',1)],[3],'noncommuting order A'),([1],[('xor',1),('add',1)],[1],'noncommuting order B')])
  for i,(data,ops,expected,name) in enumerate(families):
   path.write_bytes(plan(data,ops));rc,rep=invoke(exe,[path]);j=json.loads(rep);assert rc==0 and j['output']==expected and j['input']==data,(name,j)
   rows.append({'mode':opt,'test':f'{name} {i}','passed':True})
 report={'passed':True,'checks':len(rows),'binaries':binaries,'testSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'seed':20261112,'results':rows,'limits':'Finite native default/opt single-host checks, not a security proof; outer framing whitespace is intentionally not bound. Source identity is not execution authentication.'}
 (D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['results','binaries']},indent=2));print(D/'report.json')
except Exception:
 (D/'partial.json').write_text(json.dumps(rows,indent=2)+'\n');raise
