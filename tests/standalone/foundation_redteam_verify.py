"""Independent finite compiler/application probes for the RF2 foundation sprint.

Controller/oracle only. No external traffic or source modifications. The native
systems compiler is trusted local compilation, not an untrusted-code sandbox.
"""
from pathlib import Path
import hashlib,json,os,random,subprocess,time
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
D=R/'artifacts/sprint-031'/('redteam-'+str(time.time_ns()));D.mkdir(parents=True)
ROWS=[];MASK=(1<<64)-1

def run(args,**kw):
 return subprocess.run(list(map(str,args)),capture_output=True,timeout=10,env={'PATH':'/nonexistent'},**kw)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compiler_case(name,body,*,valid=False,exit_code=0):
 src=D/(name+'.rf2');src.write_bytes(body);out=D/(name+'-image')
 q=run([C,src,out,'--opt','--compact'])
 if valid:
  assert q.returncode==0,(name,q.stderr)
  run(['/usr/bin/codesign','-s','-',out]).check_returncode();z=run([out]);assert z.returncode==exit_code,(name,z.returncode,z.stderr)
 else:
  assert q.returncode!=0 and not out.exists(),(name,q.returncode,q.stderr)
  if os.environ.get('RF2_REQUIRE_SOURCE_DIAGNOSTICS')=='1':assert b'near source 'in q.stderr,(name,q.stderr)
 ROWS.append(dict(case=name,accepted=valid,exit=q.returncode,stderr=q.stderr.decode(errors='replace')[:2048]))

def main():
 head=b'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n'
 bad={
 'missing-end':head+b' return 0\n',
 'unknown-variable':head+b' return unknown\nend\n',
 'embedded-nul':head+b' return 0\nend\n\x00fn extra()\n return 1\nend\n',
 'invalid-byte':head+b' return \xff\nend\n',
 'unterminated-string':head+b' return "broken\nend\n',
 'duplicate-main':head+b' return 0\nend\nfn main(argc,argv)\n return 1\nend\n',
 'return-missing-expression':head+b' return\nend\n',
 'unknown-call':head+b' return absent(1)\nend\n',
 'uninitialized-local':head+b' let x=x+1\n return x\nend\n',
 'missing-close-parenthesis':head+b' return (1+2\nend\n',
 'chained-comparison':head+b' return 1<2<3\nend\n',
 'empty-hex':head+b' return 0x\nend\n',
 }
 for name,source in bad.items():compiler_case(name,source)
 for byte in [0,1,8,9,10,13,27,31]:
  compiler_case('raw-control-string-'+str(byte),head+b' return "a'+bytes([byte])+b'b"\nend\n')
 if os.environ.get('RF2_REQUIRE_SOURCE_DIAGNOSTICS')=='1':
  # Diagnostic text cannot replay source control bytes into the terminal or
  # flood logs with an entire100k identifier. The preview is a bounded rendering.
  for label,source in [('terminal-control',head+b' return 0\nend\n\x1b[31m\n'),('terminal-bell',head+b' return 0\nend\n\x07\n'),('oversized-error-token',b'x'*100000+b'\n')]:
   src=D/(label+'.rf2');src.write_bytes(source);out=D/(label+'-image');q=run([C,src,out,'--opt','--compact'])
   assert q.returncode!=0 and not out.exists()
   assert len(q.stderr)<1024 and all(c==10 or 32<=c<=126 for c in q.stderr),(label,len(q.stderr),q.stderr[:100])
   ROWS.append(dict(case=label+'-diagnostic-sanitized-and-bounded',stderrBytes=len(q.stderr),stderr=q.stderr.decode()))
 # Runtime arithmetic tested from independently computed u64 answers, including
 # full-width operands. Small deterministic sample; not exhaustive fuzz proof.
 rng=random.Random(310031)
 for i in range(64):
  a=rng.getrandbits(64);b=rng.getrandbits(64);shift=rng.randrange(64)
  expression=f'(({a}^{b})+({a}>>{shift}))*3'
  expected=(((a^b)+(a>>shift))*3)&MASK
  compiler_case('arithmetic-'+str(i),head+f' return ({expression})!={expected}\nend\n'.encode(),valid=True)
 # Warm-cache failure must not publish templates or alter prior committed pack.
 cache=D/'units';cache.mkdir(mode=0o700)
 good=D/'cached-source.rf2';good.write_text('profile RF2_SYSTEM_A64_V1\nfn leaf(x)\n let y=x+3\n return y*7\nend\nfn main(argc,argv)\n return leaf(4)!=49\nend\n')
 for stage in ['cold','warm']:
  out=D/('cached-'+stage);q=run([C,good,out,'--opt','--compact','--reuse-pack',cache]);assert q.returncode==0,q.stderr
  data=json.loads(Path(str(out)+'.reuse.json').read_text())
  if stage=='warm':assert data['reused']==1
 before={p.name:sha(p)for p in cache.glob('*.pack')};assert before
 good.write_text(good.read_text().replace('return leaf(4)!=49','return unknown(4)'))
 out=D/'invalid-after-warm';q=run([C,good,out,'--opt','--compact','--reuse-pack',cache]);assert q.returncode!=0 and not out.exists()
 assert before=={p.name:sha(p)for p in cache.glob('*.pack')}
 ROWS.append(dict(case='invalid-source-preserves-committed-pack',refused=True,packHashes=before))
 # Expansion coordinates must not masquerade as original imported-file lines.
 project=D/'modules';project.mkdir();(project/'lib.rf2').write_text('module independent\nfn leaf(x)\n return missing\nend\n')
 source=project/'main.rf2';source.write_text('profile RF2_SYSTEM_A64_V1\nuse "lib.rf2"\nfn main(argc,argv)\n return leaf(1)\nend\n')
 out=D/'module-image';q=run([C,source,out,'--opt','--compact']);assert q.returncode!=0 and not out.exists()
 if os.environ.get('RF2_REQUIRE_SOURCE_DIAGNOSTICS')=='1':assert b'near expanded-source 'in q.stderr and b'entry 'in q.stderr
 ROWS.append(dict(case='import-error-is-labelled-expanded-source',stderr=q.stderr.decode(errors='replace')))
 # Output errors must not inherit a misleading source-cursor diagnostic.
 source=D/'valid-output-refusal.rf2';source.write_bytes(head+b' return 0\nend\n');out=D/'existing';out.write_text('do not overwrite')
 q=run([C,source,out,'--opt','--compact']);assert q.returncode!=0 and out.read_text()=='do not overwrite'
 assert b'near source 'not in q.stderr and b'near expanded-source 'not in q.stderr
 ROWS.append(dict(case='output-refusal-preserves-existing-and-no-stale-location',stderr=q.stderr.decode(errors='replace')))
 # Pure observation of old literal policy. Not a claim that this is desirable.
 src=D/'literal-overflow-observation.rf2';src.write_bytes(head+b' return 18446744073709551616\nend\n');out=D/'literal-overflow-observation'
 q=run([C,src,out,'--opt','--compact']);literal=dict(case='out-of-u64-literal-policy',compilerExit=q.returncode,stderr=q.stderr.decode(errors='replace'))
 if q.returncode==0:
  run(['/usr/bin/codesign','-s','-',out]).check_returncode();literal['programExit']=run([out]).returncode;literal['classification']='observed acceptance, policy decision still required'
 else:literal['classification']='observed rejection'
 if os.environ.get('RF2_REQUIRE_SOURCE_DIAGNOSTICS')=='1':assert q.returncode!=0 and not out.exists()
 ROWS.append(literal)
 app=os.environ.get('RF2_TEXT_SEARCH_BINARY')
 if app:
  # Exact declared byte ranges end at inaccessible guard pages. An accidental
  # read at data[n] or needle[m] would fault this disposable native process.
  library=R/'examples/text-search/lib/search.rf2'
  library_identity=sha(library);(D/'search.rf2').write_bytes(library.read_bytes())
  guard_cases=[(b'',b'',0),(b'',b'a',0),(b'a',b'',0),(b'a',b'a',0),(b'a',b'b',0),(b'aaaaa',b'aa',0),(b'aaaaa',b'aa',1),(b'abcab',b'ab',1),(b'aba',b'aba',0),(b'aba',b'abab',0)]
  # Misses across8-byte boundaries must not overread the final partial word.
  # Binary needles cover zero-byte detection with low/high first-byte values.
  for length in [9,15,16,17,23,24,25,31,32,33,63,64,65]:
   for first in [0,128,255]:
    query=bytes([first]);guard_cases.append((b'U'*length,query,0))
    guard_cases.append((b'U'*(length-1)+query,query,1))
  guard_cases.extend([(b'a'*128,b'a'*128,1),(b'U'+b'a'*128,b'a'*128,0)])
  guards='profile RF2_SYSTEM_A64_V1\nuse "search.rf2"\nfn main(argc,argv)\n let data=syscall6(197,0,32768,3,4098,18446744073709551615,0)\n let needle=syscall6(197,0,32768,3,4098,18446744073709551615,0)\n if (data==18446744073709551615)|(needle==18446744073709551615)\n  return 2\n end\n if syscall6(74,data+16384,16384,0,0,0,0)|syscall6(74,needle+16384,16384,0,0,0,0)\n  return 3\n end\n let result=ByteSearch(0,0,0)\n let prefix=SearchPrefix()\n'
  for number,(hay,query,overlap)in enumerate(guard_cases):
   for j,value in enumerate(hay):guards+=f' do store8(data+{16384-len(hay)+j},{value})\n'
   for j,value in enumerate(query):guards+=f' do store8(needle+{16384-len(query)+j},{value})\n'
   count=len(hay)+1 if not query else sum(hay.startswith(query,i)for i in range(len(hay)))if overlap else hay.count(query)
   first=hay.find(query);first=MASK if first<0 else first
   guards+=f' do byte_search(data+{16384-len(hay)},{len(hay)},needle+{16384-len(query)},{len(query)},{overlap},prefix,result)\n if result.status|(result.matches!={count})|(result.first!={first})\n  return {number+10}\n end\n'
  # Invalid declared budgets must reject without dereferencing protected pointers.
  for n,m,overlap in [(1048577,1,0),(1,129,0),(1,1,2)]:
   guards+=f' do byte_search(data+16384,{n},needle+16384,{m},{overlap},prefix,result)\n if result.status!=1\n  return 30\n end\n'
  guards+=' do syscall6(73,data,32768,0,0,0,0)\n do syscall6(73,needle,32768,0,0,0,0)\n return 0\nend\n'
  source=D/'guard-pages.rf2';source.write_text(guards)
  for mode,flags in [('plain',[]),('optimized',['--opt','--compact'])]:
   out=D/('guard-pages-'+mode);q=run([C,source,out,*flags]);assert q.returncode==0,q.stderr
   run(['/usr/bin/codesign','-s','-',out]).check_returncode();q=run([out]);assert q.returncode==0,(mode,q.returncode,q.stderr)
  assert sha(library)==library_identity,'library changed during guard-page qualification'
  ROWS.append(dict(case='text-library-page-boundaries',validCases=len(guard_cases),invalidBudgetCases=3,modes=['plain','optimized'],librarySHA256=library_identity))
  A=Path(app).resolve();app_rows=[]
  def check(query,data,overlap=False):
   needle=query.encode();expected_first=data.find(needle)
   if not needle:expected_count=len(data)+1
   elif overlap:expected_count=sum(data.startswith(needle,i)for i in range(len(data)))
   else:expected_count=data.count(needle)
   q=run([A,query,*(['--overlap']if overlap else[])],input=data);assert q.returncode==0,(query,len(data),q.returncode,q.stderr)
   got=json.loads(q.stdout);expected=dict(bytes=len(data),query_bytes=len(needle),matches=expected_count,first_byte=None if expected_first<0 else expected_first)
   assert got==expected,(query,len(data),got,expected)
   app_rows.append(dict(queryHex=needle.hex(),bytes=len(data),overlap=overlap,expected=expected))
  for query,data in [('',b''),('',b'abc'),('aa',b'aaaaa'),('aba',b'abababa'),('x',b'\x00x\xffx\x00'),('தமிழ்','தமிழ் தமிழ்'.encode()),('é','é é é'.encode()),('z',bytes(range(256))),('end',b'x'*4095+b'end'),('end',b'x'*65535+b'end')]:
   for overlap in [False,True]:check(query,data,overlap)
  for i in range(96):
   query=''.join(rng.choice('abX')for _ in range(rng.randrange(0,9)));data=bytes(rng.choice(b'abX\x00\xff')for _ in range(rng.randrange(0,2048)));check(query,data,bool(i%2))
  check('z',b'x'*(1048576-1)+b'z')
  check('a'*128,b'a'*4096,True)
  check('a'*127+'b',b'a'*4096+b'b',False)
  q=run([A,'x'],input=b'x'*1048577);assert q.returncode==4,(q.returncode,q.stderr)
  q=run([A,'x'*129],input=b'x');assert q.returncode==2,(q.returncode,q.stderr)
  q=run([A,'x','--unknown'],input=b'x');assert q.returncode==2,(q.returncode,q.stderr)
  ROWS.append(dict(case='text-search-independent-byte-oracle',cases=len(app_rows),rows=app_rows,overboundRefused=True,longQueryRefused=True,unknownFlagRefused=True,executableSHA256=sha(A)))
 if os.environ.get('RF2_REQUIRE_CHECK_ONLY')=='1':
  checkdir=D/'check-only';checkdir.mkdir();canary=checkdir/'must-not-execute';prior=checkdir/'preserve.txt';prior.write_bytes(b'KEEP ORIGINAL')
  source=checkdir/'runtime-effects.rf2'
  source.write_text('profile RF2_SYSTEM_A64_V1\nfn unused(x)\n return x+1\nend\nfn main(argc,argv)\n do open("'+str(canary)+'",3585,384)\n do exit(99)\n return unused(1)\nend\n')
  def manifest():return {str(p.relative_to(checkdir)):sha(p)for p in checkdir.rglob('*')if p.is_file()}
  before=manifest();q=run([C,'--check',source]);assert q.returncode==0 and b'no executable written'in q.stdout,(q.returncode,q.stderr)
  assert not canary.exists() and before==manifest()
  ROWS.append(dict(case='check-only-valid-runtime-effects-not-executed-and-no-artifacts',manifestUnchanged=True,stdout=q.stdout.decode()))
  # Full generation must inspect an unused malformed helper, not just main.
  source.write_text('profile RF2_SYSTEM_A64_V1\nfn unused(x)\n return absent\nend\nfn main(argc,argv)\n return 0\nend\n')
  before=manifest();q=run([C,'--check',source]);assert q.returncode!=0 and b'unknown local'in q.stderr and before==manifest()
  ROWS.append(dict(case='check-only-checks-unused-helper',refused=True,manifestUnchanged=True))
  source.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return 0\nend\n')
  for label,args in [('missing-source',['--check']),('unknown-check-option',['--check',source,'--wat']),('check-output-forbidden',['--check',source,checkdir/'new-output']),('check-cache-forbidden',['--check',source,'--reuse-pack',checkdir]),('check-opt-forbidden',['--check',source,'--opt']),('unknown-build-option',[source,checkdir/'new-output','--wat'])]:
   before=manifest();q=run([C,*args]);assert q.returncode!=0 and before==manifest() and not canary.exists(),(label,q.returncode,q.stderr)
   ROWS.append(dict(case=label,refused=True,manifestUnchanged=True))
 report=dict(passed=True,schema='rf2.foundation.redteam.v1',compilerSHA256=sha(C),controllerSHA256=sha(Path(__file__)),cases=ROWS,scope='Finite local malformed-source, actual native execution and cache-preservation probes. Optional app uses independent Python byte-search oracle. No remote traffic, universal security, coverage completeness or speed claim.')
 (D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),passed=True,cases=len(ROWS),appTested=bool(app))))
if __name__=='__main__':main()
