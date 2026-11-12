"""Finite native logical guard and file-signature oracles, no speed claim."""
from pathlib import Path
import subprocess,tempfile,json,os,hashlib,random
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-logic-final'));rows=[]
def build(src,p,opt,good=True):
 source=p.with_suffix('.rf2');source.write_text(src);q=subprocess.run([C,source,p]+(['--opt']if opt else[]),capture_output=True,timeout=30)
 if not good:assert q.returncode==1 and not p.exists(),(q.returncode,q.stderr);return
 assert q.returncode==0,(source,q.stderr);subprocess.run(['/usr/bin/codesign','-s','-',p],check=True,capture_output=True)
H='profile RF2_SYSTEM_A64_V1\n'
with tempfile.TemporaryDirectory(prefix='rf2-logic-')as td:
 d=Path(td);cases=[]
 values=[0,1,2,255,65536,2**63,2**64-1]
 for a in values:
  cases.append((f'not-{a}',f'not({a})',int(not a)))
  for b in values:
   cases.extend([(f'all-{a}-{b}',f'all({a},{b})',int(bool(a)and bool(b))),(f'any-{a}-{b}',f'any({a},{b})',int(bool(a)or bool(b)))])
 rng=random.Random(16001)
 def tree(n):
  if n==0:
   v=rng.choice(values);return str(v),bool(v)
  op=rng.choice(['all','any','not']);a,av=tree(n-1)
  if op=='not':return f'not({a})',not av
  b,bv=tree(n-1);return f'{op}({a},{b})',(av and bv)if op=='all'else(av or bv)
 for i in range(60):
  s,v=tree(3);cases.append((f'tree{i}',s,int(v)))
 for opt in [False,True]:
  # Batch independent normalized expectations; process exit has only an8-bit channel.
  body='\n'.join(f' if ({s})!={v}\n return 1\n end'for _,s,v in cases)
  src=H+'fn main(argc,argv)\n'+body+'\n return 0\nend\n';p=d/f'truth{opt}';build(src,p,opt);q=subprocess.run([p],capture_output=True);assert q.returncode==0,q.stderr;rows.extend({'case':n,'opt':opt,'passed':True}for n,_,_ in cases)
  probes={
   'literal-loop-bound':H+'''fn main(argc,argv)
 let i=0
 let sum=0
 while i<true
  set sum=sum+(i&7)
  set i=i+1
 end
 while true<false
  return 2
 end
 return (i!=1)|sum
end
''',
   'sideeffects':H+'''record Count(n:u64)
fn hit(c:Count)
 set c.n=c.n+1
 return 7
end
fn main(argc,argv)
 let c=Count(0)
 let a=all(false,hit(c))
 let b=any(true,hit(c))
 if c.n!=0
  return 1
 end
 let x=all(true,hit(c))
 let y=any(false,hit(c))
 return (c.n!=2)|(a!=0)|(b!=1)|(x!=1)|(y!=1)
end
''',
   'skipped-bounds':H+'''array B(u8,1)
fn main(argc,argv)
 let b=B()
 return all(false,b[99])|not(any(true,b[99]))
end
''',
   'views':H+'''array B(u8,1)
view V(B)
fn main(argc,argv)
 let b=B()
 let v=V(b,0,1)
 return not(all(v.length==1,any(v[0]==0,false)))
end
''',
   'literal-optimizer':H+'''fn main(argc,argv)
 let x=0
 set x=x+true
 while x<true
  set x=x+1
 end
 if 1+true!=2
  return 1
 end
 return x!=1
end
'''}
  for n,src in probes.items():
   p=d/(n+str(opt));build(src,p,opt);q=subprocess.run([p],capture_output=True);assert q.returncode==0,(n,opt,q.returncode,q.stderr);rows.append({'case':n,'opt':opt,'passed':True})
  bad=['all(1)','any(1,2,3)','not(1,2)','all(false,missing)','any(true,missing(1))','all(true,R(1))']
  for i,e in enumerate(bad):build(H+'record R(x:u64)\nfn main(argc,argv)\nreturn '+e+'\nend\n',d/f'bad{opt}{i}',opt,False);rows.append({'case':f'refusal{i}','opt':opt,'passed':True})
  for n in ['true','false','all','any','not']:
   build(H+f'fn main(argc,argv)\nlet {n}=1\nreturn 0\nend\n',d/f'reserved{opt}{n}',opt,False);rows.append({'case':'reserved-'+n,'opt':opt,'passed':True})
  for label,body in [('typed-dead-rhs','record R(x:u64)\nfn main(argc,argv)\nlet r=R(1)\nreturn all(false,r)\nend\n'),('view-dead-call','array B(u8,1)\nview V(B)\nfn f()\nreturn 0\nend\nfn main(argc,argv)\nlet b=B()\nlet v=V(b,0,1)\nreturn all(false,f())\nend\n')]:
   build(H+body,d/f'{label}{opt}',opt,False);rows.append({'case':label,'opt':opt,'passed':True})
  for label,expr in [('taken-all','all(true,b[99])'),('taken-any','any(false,b[99])')]:
   p=d/(label+str(opt));build(H+'array B(u8,1)\nfn main(argc,argv)\nlet b=B()\nreturn '+expr+'\nend\n',p,opt);q=subprocess.run([p],capture_output=True);assert q.returncode==2 and b'RF2 bounds' in q.stderr;rows.append({'case':label,'opt':opt,'passed':True})
  app=d/f'kind{opt}';q=subprocess.run([C,R/'examples/file-kind/main.rf2',app]+(['--opt']if opt else[]),capture_output=True);assert q.returncode==0,q.stderr;subprocess.run(['/usr/bin/codesign','-s','-',app],check=True,capture_output=True)
  signatures=[(b'\x89PNG\r\n\x1a\n','png'),(b'%PDF-','pdf'),(b'\x7fELF','elf'),(b'GIF87a','gif'),(b'GIF89a','gif'),(b'\xff\xd8\xff','jpeg'),(b'PK\x03\x04','zip'),(b'PK\x05\x06','zip'),(b'PK\x07\x08','zip'),(bytes.fromhex('cffaedfe'),'macho64'),(bytes.fromhex('feedfacf'),'macho64')]
  inputs=[b'',b'hello',bytes(range(256))]+[bytes(rng.randrange(256)for _ in range(rng.randrange(60)))for _ in range(50)]
  for s,_ in signatures:inputs.extend([s,s+b'payload']+[s[:i]for i in range(len(s))])
  for i,data in enumerate(inputs):
   expected=next((v for s,v in signatures if data.startswith(s)),'unknown');f=d/'sample';f.write_bytes(data);q=subprocess.run([app,f],capture_output=True);assert q.returncode==0 and q.stdout==(expected+'\n').encode()and not q.stderr,(opt,i,q.stdout,q.stderr);assert f.read_bytes()==data;rows.append({'case':f'file{i}','opt':opt,'passed':True})
  for args in [[],[str(d/'missing')],[str(d)]]:
   q=subprocess.run([app]+args,capture_output=True);assert q.returncode==1 and q.stderr;rows.append({'case':'file-error','opt':opt,'passed':True})
v={'passed':True,'checks':len(rows),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'scope':'Finite native scalar logic and read-only header inspection cases, default and optimized. Prefix recognition is not file validity/security; no speed/token claim.','results':rows};out=Path(os.environ.get('RF2_TEST_REPORT',R/'artifacts/logic-verification.json'));out.write_text(json.dumps(v,indent=2)+'\n');print('logic/app checks',len(rows),'passed')
