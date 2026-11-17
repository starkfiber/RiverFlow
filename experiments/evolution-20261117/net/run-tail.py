"""Isolated native DHCP parser correctness and same-task timings; no networking."""
from pathlib import Path
import hashlib,json,subprocess,sys,random,time,statistics,platform
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'artifacts/evolution-20261117/net/tail-scan'
COMP=Path('/Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program')
assert hashlib.sha256(COMP.read_bytes()).hexdigest()=='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
OUT.mkdir(parents=True,exist_ok=True)
# Existing independent dictionary/byte-slice oracle, loaded without executing campaigns.
ns={};oracle_src=(HERE/'original-verify.py').read_text();prefix=oracle_src[:oracle_src.index('for c in range(1,6):')]
prefix=prefix[prefix.index('SERVER='):] if 'SERVER=' in prefix else prefix
# Strip original module setup, retaining constant declaration and independent oracle.
prefix='SERVER=0x0a4d0002;BASE=0x0a4d0064\ncases=[]\n'+oracle_src[oracle_src.index('def packet('):oracle_src.index('for c in range(1,6):')]
exec(prefix,dict(Path=Path,struct=__import__('struct'),hashlib=hashlib),ns)
# Functions created by exec require common globals.
ns={ 'Path':Path,'struct':__import__('struct'),'hashlib':hashlib }
exec(prefix,ns)
rng=random.Random(171126)
packet=ns['packet'];Oracle=ns['Oracle']
for variant in ['baseline','candidate']:
 d=OUT/variant;d.mkdir(exist_ok=True)
 (d/'dhcp.flow').write_bytes((HERE/(variant+'.flow')).read_bytes())
 (d/'main.flow').write_bytes((HERE/'original-main.flow').read_bytes())
 # Full unchanged oracle and stream campaign with only source/compiler paths redirected.
 verify=oracle_src.replace("V=Path('experiments/rf2net/dhcp')",'V=Path('+repr(str(d))+')').replace("Path('artifacts/rf2decision-sustained/compiler-opt').resolve()",'Path('+repr(str(COMP))+')')
 (d/'verify.py').write_text(verify)
 subprocess.run([sys.executable,str(d/'verify.py'),str(d/'acceptance')],check=True)
bench='''profile RF2_SYSTEM_A64_V1
use "dhcp.flow"
fn main(argc,argv)
 let raw=buffer("input",576)
 let n=read(0,raw,576)
 if any(n>>63,n>576)
  return 2
 end
 let p=DhcpPacket()
 let m=DhcpMeta()
 let j=0
 while j<n
  set p[j]=load8(raw+j)
  set j=j+1
 end
 let i=0
 let checksum=0
 while i<150000
  let result=dhcp_parse(p,n,m)
  set checksum=checksum+result
  if result==0
   set checksum=checksum+m[0]+m[1]+m[5]
  end
  set i=i+1
 end
 let out=buffer("out",8)
 do store64(out,checksum)
 do write(1,out,8)
 return 0
end
'''
profiles={
 'short-valid':lambda:packet(xid=rng.randrange(2**32))[:244],
 'normal-300':lambda:packet(xid=rng.randrange(2**32)),
 'max-576':lambda:packet(xid=rng.randrange(2**32)).ljust(576,b'\0'),
 'bad-last-byte':lambda:packet(xid=rng.randrange(2**32)).ljust(575,b'\0')+b'\x01',
 'early-reject':lambda:b'\x02'+packet(xid=rng.randrange(2**32))[1:],
}
results=[]
for mode in ['plain','opt']:
 exes={}
 for variant in ['baseline','candidate']:
  d=OUT/variant;(d/'bench.flow').write_text(bench);exe=d/('bench-'+mode)
  subprocess.run([str(COMP),str(d/'bench.flow'),str(exe),'--compact']+(['--opt'] if mode=='opt' else []),check=True,capture_output=True)
  subprocess.run(['codesign','-s','-',str(exe)],check=True,capture_output=True);exes[variant]=exe
 for profile,gen in profiles.items():
  pairs=[]
  for repeat in range(15):
   blob=gen();code,m=Oracle().parse(blob);expected=code*150000 if code else (m[0]+m[1]+m[5])*150000
   expected=(expected%(2**64)).to_bytes(8,'little');times={};order=list(exes);rng.shuffle(order)
   for variant in order:
    start=time.perf_counter_ns();p=subprocess.run([str(exes[variant])],input=blob,capture_output=True,timeout=20);elapsed=(time.perf_counter_ns()-start)/1e6
    assert p.returncode==0 and p.stdout==expected,(variant,mode,profile,p.returncode,p.stdout.hex(),expected.hex())
    times[variant]=elapsed
   pairs.append(dict(repeat=repeat,inputSHA256=hashlib.sha256(blob).hexdigest(),order=order,ms=times))
  b=statistics.median(x['ms']['baseline'] for x in pairs);c=statistics.median(x['ms']['candidate'] for x in pairs)
  row=dict(mode=mode,profile=profile,iterationsPerProcess=150000,pairs=pairs,baselineMedianMs=b,candidateMedianMs=c,speedup=b/c)
  results.append(row);print(mode,profile,round(b,3),round(c,3),'speedup',round(b/c,3),flush=True)
(OUT/'RESULTS.json').write_text(json.dumps(dict(platform=platform.platform(),machine=platform.machine(),compilerSHA256=hashlib.sha256(COMP.read_bytes()).hexdigest(),results=results),indent=2)+'\n')
