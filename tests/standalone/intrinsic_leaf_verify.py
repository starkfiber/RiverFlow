"""Semantic ABI checks across intrinsic-only and actual-call functions, register/spill boundaries."""
from pathlib import Path
import subprocess,struct,random,json,time,hashlib,os
R=Path(__file__).resolve().parents[2];D=R/'artifacts/sha-stream'/('abi-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/rf2c-sha-prep3-self'));rng=random.Random(241113);values=[0,1,0xffffffff,0xffffffffffffffff]+[rng.getrandbits(64)for _ in range(124)];(D/'input').write_bytes(b''.join(struct.pack('<Q',x)for x in values));mask=(1<<64)-1;cases=0
for n in range(1,11):
 for nested in [False,True]:
  s='profile RF2_SYSTEM_A64_V1\nfn actual(x)\n return x ^ 12345\nend\nfn inner(seed)\n'
  for i in range(n):s+=f' let a{i}=seed+{7*i+1}\n'
  s+=' let p=buffer("abi",8)\n do store64(p,seed)\n do sha256_blocks_armv8(0,0,0,0)\n let value='+'+'.join(f'a{i}'for i in range(n))+'\n if any(seed&1,seed&4)\n  set value=value ^ 6789\n end\n'
  s+=' return bswap64('+('actual(value)'if nested else'value')+') ^ bswap32(load64(p))\nend\nfn outer(seed)\n'
  for i in range(8):s+=f' let keep{i}=seed+{i+19}\n'
  s+=' let answer=inner(seed)\n return answer+'+'+'.join('keep'+str(i)for i in range(8))+'\nend\n'
  s+='''fn main(argc,argv)
 let p=buffer("input",1024)
 let fd=open(load64(argv+8),0,0)
 let n=read(fd,p,1024)
 do close(fd)
 let i=0
 while i<n
  do store64(p+i,outer(load64(p+i)))
  set i=i+8
 end
 do write(1,p,n)
 return 0
end
'''
  expected=b''
  for seed in values:
   v=sum((seed+7*i+1)&mask for i in range(n))&mask
   if seed&5:v^=6789
   if nested:v^=12345
   v=int.from_bytes(v.to_bytes(8,'little'),'big') ^ int.from_bytes((seed&0xffffffff).to_bytes(4,'little'),'big');v=(v+sum((seed+i+19)&mask for i in range(8)))&mask;expected+=struct.pack('<Q',v)
  for opt in [False,True]:
   p=D/f'{n}-{nested}-{opt}.rf2';p.write_text(s);exe=p.with_suffix('');subprocess.run([C,p,exe,*(['--opt']if opt else[])],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True);q=subprocess.run([exe,D/'input'],capture_output=True,check=True);assert q.stdout==expected,(n,nested,opt);cases+=len(values)
report={'passed':True,'programModes':40,'semanticComparisons':cases,'callerLocalsPreserved':8,'calleeScalarLocalsRange':[1,10],'nestedActualCallsTested':True,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'scope':'Finite local ABI/call-classification checks; default/optimized register and spill boundaries. Not a complete ABI proof.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'passed':True,'comparisons':cases}))
