"""Independent catalogue, lookalike and ABI refusal controls for compiler policy."""
from pathlib import Path
import hashlib,json,os,struct,subprocess,time,re
R=Path(__file__).resolve().parents[2];D=R/'artifacts/codebase-refresh'/('policy-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ['RF2_TEST_COMPILER']).resolve();source=(R/'native/compiler/compiler.rf2').read_text()
# Expected policy is independent of the compiler's length buckets.
arithmetic={'ror32','bswap32','bswap64','sha256_blocks_armv8','sha256_chain_armv8','fill_zero','bswap32_copy'}
inline={'buffer','load8','load32','load64','store8','store32','store64','all','any','not'}|arithmetic
raw={'sha256_blocks_armv8','sha256_chain_armv8','fill_zero','bswap32_copy','buffer','fork_process','syscall6','load8','load32','load64','store8','store32','store64','read','write','open','close','exit'}
names=sorted(arithmetic|inline|raw);cases=set(names)|{'','a','long_unknown_identifier','platform_call','vm_clock_ticks','release','buffer_get'}
for name in names:
 cases.update([name+'x','x'+name,name.upper(),name[:-1],name+'_',name.replace('_','')])
cases=sorted(cases);expected=b''.join(struct.pack('<QQ',((x in arithmetic)+2*(x in inline)+4*(x in raw)),((x in arithmetic)+2*(x in inline)+4*(x in raw)))for x in cases)
def function(name):
 m=re.search(r'^fn '+re.escape(name)+r'\(',source,re.M);assert m,name;n=re.search(r'^fn ',source[m.end():],re.M);return source[m.start():m.end()+n.start()]if n else source[m.start():]
functions=['state','die','require','length','same','token','add_token','tmatch','intrinsic_flags']
body='profile RF2_SYSTEM_A64_V1\n'+''.join(function(x)for x in functions)+'fn main(argc,argv)\n let p=buffer("policy_output",16)\n let t=0\n'
for x in cases:body+=f' set t=add_token(1,"{x}",{len(x)},0)\n do store64(p,intrinsic_flags(t))\n do store64(p+8,intrinsic_flags(t))\n do write(1,p,16)\n'
body+=' return 0\nend\n';comparisons=0
for opt in [False,True]:
 p=D/f'policy-{opt}.rf2';p.write_text(body);out=p.with_suffix('');q=subprocess.run([C,p,out,*(['--opt']if opt else[])],capture_output=True);assert q.returncode==0,q.stderr;subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True);q=subprocess.run([out],capture_output=True,timeout=10);assert q.returncode==0 and q.stdout==expected,(opt,q.stderr);comparisons+=len(cases)*2
negative=0
for name in sorted(arithmetic):
 for declaration in [f'fn {name}(x)\n return x\nend',f'record {name}(x:u64)']:
  for opt in [False,True]:
   p=D/f'reserved-{negative}.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\n'+declaration+'\nfn main(argc,argv)\nreturn 0\nend\n');out=p.with_suffix('');q=subprocess.run([C,p,out,*(['--opt']if opt else[])],capture_output=True);assert q.returncode==1 and b'reserved arithmetic name' in q.stderr and not out.exists(),(name,q.stderr);negative+=1
# Nearby legal names must remain real calls, preserving caller locals.
lookalikes=0
for name in ['load640','fill_zerox','bswap32_copycat','sha256_chain_armv8x']:
 for opt in [False,True]:
  p=D/f'call-{lookalikes}.rf2';p.write_text(f'profile RF2_SYSTEM_A64_V1\nfn {name}(x)\nreturn x+1\nend\nfn main(argc,argv)\nlet a=71\nlet b={name}(9)\nreturn a+b\nend\n');out=p.with_suffix('');subprocess.run([C,p,out,*(['--opt']if opt else[])],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True);q=subprocess.run([out],capture_output=True);assert q.returncode==81,(name,opt,q.returncode);lookalikes+=1
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'passed':True,'policyNames':len(names),'tokenCases':len(cases),'classificationComparisons':comparisons,'reservedRefusals':negative,'lookalikeExecutions':lookalikes,'bothCompilerModes':True,'sourceSHA256':sha(R/'native/compiler/compiler.rf2'),'compilerSHA256':sha(C),'controllerSHA256':sha(Path(__file__)),'limits':'Finite policy and call-classification checks, not complete intrinsic semantics or memory-safety proof.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),**report}))
