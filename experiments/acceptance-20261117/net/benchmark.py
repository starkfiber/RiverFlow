"""Prepare source-bound native probes; root exclusively schedules one timing run.

Launch-inclusive repeated parsing, matched bytes, exact independent oracle.
No timings are run in prepare mode. All paired observations remain retained.
"""
from pathlib import Path
import argparse,ast,hashlib,json,os,platform,random,statistics,struct,subprocess,time
H=Path(__file__).resolve().parent;R=H.parents[2]
C=Path('/Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program')
CSHA='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ENTRY='''profile RF2_SYSTEM_A64_V1
use "dhcp.flow"
fn main(argc,argv)
 let input=buffer("bench_input",587)
 let got=0
 let eof=0
 while eof==0
  let count=read(0,input+got,587-got)
  if count>>63
   return 2
  end
  if count==0
   set eof=1
  else
   set got=got+count
   if got==587
    return 2
   end
  end
 end
 if got<10
  return 2
 end
 let repetitions=load64(input)
 let n=load8(input+8)+load8(input+9)*256
 if any(n>576,any(n+10!=got,any(repetitions==0,repetitions>100000000)))
  return 2
 end
 let p=DhcpPacket()
 let m=DhcpMeta()
 let j=0
 while j<n
  set p[j]=load8(input+10+j)
  set j=j+1
 end
 let i=0
 let checksum=0
 while i<repetitions
  let result=dhcp_parse(p,n,m)
  set checksum=checksum+result
  if result==0
   set checksum=checksum+m[0]+m[1]+m[5]
  end
  set i=i+1
 end
 let out=buffer("bench_out",8)
 do store64(out,checksum)
 if write(1,out,8)!=8
  return 3
 end
 return 0
end
'''
def prepare(out):
    assert sha(C)==CSHA
    out.mkdir(parents=True,exist_ok=False)
    (out/'PREPARED-CONTROLLER.py').write_bytes(Path(__file__).read_bytes())
    tmp=Path(os.environ['TMPDIR']).resolve();assert '/Volumes/Mac Work Cache/'in str(tmp)
    binary_root=tmp/('net-timing-'+hashlib.sha256(str(out).encode()).hexdigest()[:12]);binary_root.mkdir()
    manifest={'compilerSHA256':CSHA,'controllerSHA256':sha(Path(__file__)),'probes':[],'plan':{'pairs':31,'warmupsPerVariant':2,'seed':1711202602,'bootstrapSamples':10000,'profiles':{'short-valid':1500000,'normal-300':750000,'max-576':250000,'bad-last-byte':250000,'early-reject':30000000},'smallCaseGate':{'candidateBaselinePointMaximum':1.03,'upperPairedBootstrap95Maximum':1.05},'scope':'Launch-inclusive repeated parser work. Minimum intended useful duration~50ms; actual observed duration retained, not auto tuned after results.'}}
    for family in ['dhcp','dhcp-durable']:
      for variant in ['baseline','candidate']:
        source=out/'source'/family/variant;source.mkdir(parents=True);(source/'dhcp.flow').write_bytes((H/variant/family/'dhcp.flow').read_bytes());(source/'bench.flow').write_text(ENTRY)
        for mode in ['plain','opt']:
            binary=binary_root/(family+'-'+variant+'-'+mode);command=[str(C),str(source/'bench.flow'),str(binary),'--compact']+(['--opt']if mode=='opt'else[])
            p=subprocess.run(command,capture_output=True,timeout=30);(source/('build-'+mode+'.log')).write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr
            subprocess.run(['codesign','-s','-',str(binary)],capture_output=True,check=True)
            manifest['probes'].append({'family':family,'variant':variant,'mode':mode,'binary':str(binary),'binarySHA256':sha(binary),'sourceSHA256':sha(source/'dhcp.flow'),'entrySHA256':sha(source/'bench.flow'),'command':command})
    (out/'PREPARED.json').write_text(json.dumps(manifest,indent=2));print('Native probes prepared; no timing executed:',out)
def run(out):
    assert os.environ.get('RF2_EXCLUSIVE_TIMING')=='1','Root must explicitly grant exclusive timing after other tests finish'
    manifest=json.loads((out/'PREPARED.json').read_text());assert manifest['compilerSHA256']==sha(C)==CSHA
    assert manifest['controllerSHA256']==sha(Path(__file__)), 'Prepared controller changed; prepare a new campaign'
    with (out/'RUN-RESERVED.json').open('x')as f:json.dump({'at':time.time(),'plan':manifest['plan']},f)
    for p in manifest['probes']:assert sha(p['binary'])==p['binarySHA256'],'Disposable native output missing/drifted; rebuild into a fresh preparation directory'
    ns={'struct':struct,'hashlib':hashlib,'SERVER':0x0a4d0002,'BASE':0x0a4d0064}
    src=H/'snapshot/dhcp/verify.py'
    for node in ast.parse(src.read_text()).body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef))and node.name in ['packet','Oracle']:exec(compile(ast.Module([node],type_ignores=[]),str(src),'exec'),ns)
    result={'schema':'rf2.net.paired-benchmark.v2','host':platform.platform(),'architecture':platform.machine(),'plan':manifest['plan'],'compilerSHA256':CSHA,'oracleSourceSHA256':sha(src),'rows':[]}
    rng=random.Random(manifest['plan']['seed']);mask=(1<<64)-1
    def fixture(profile):
        packet=ns['packet'](xid=rng.randrange(1<<32))
        if profile=='short-valid':return packet[:244]
        if profile=='normal-300':return packet
        if profile=='max-576':return packet.ljust(576,b'\0')
        if profile=='bad-last-byte':return packet.ljust(575,b'\0')+b'\1'
        return b'\2'+packet[1:]
    def invoke(probe,data,repetitions):
        code,meta=ns['Oracle']().parse(data);want=((code*repetitions)if code else((meta[0]+meta[1]+meta[5])*repetitions))&mask
        wire=struct.pack('<QH',repetitions,len(data))+data;t=time.perf_counter_ns();p=subprocess.run([probe['binary']],input=wire,capture_output=True,timeout=20);duration=(time.perf_counter_ns()-t)/1e6
        if p.returncode!=0 or p.stdout!=struct.pack('<Q',want):
            (out/'FAILURE-input.bin').write_bytes(wire);(out/'FAILURE-stdout.bin').write_bytes(p.stdout);(out/'FAILURE-stderr.bin').write_bytes(p.stderr)
            (out/'FAILURE.json').write_text(json.dumps({'probe':probe,'inputSHA256':hashlib.sha256(wire).hexdigest(),'returncode':p.returncode,'expectedChecksum':want,'phase':'invoke'},indent=2))
            raise AssertionError('Native checksum/framing failed; exact receipt preserved')
        return duration
    for family in ['dhcp','dhcp-durable']:
      for mode in ['plain','opt']:
       probes={p['variant']:p for p in manifest['probes']if p['family']==family and p['mode']==mode}
       for profile,repetitions in manifest['plan']['profiles'].items():
        warm=[]
        for _ in range(2):
            data=fixture(profile)
            for v,p in probes.items():warm.append({'variant':v,'ms':invoke(p,data,repetitions)})
        pairs=[]
        for i in range(31):
            data=fixture(profile);order=list(probes);rng.shuffle(order);observed={v:invoke(probes[v],data,repetitions)for v in order};pairs.append({'pair':i,'order':order,'inputSHA256':hashlib.sha256(data).hexdigest(),'ms':observed})
        baseline=[p['ms']['baseline']for p in pairs];candidate=[p['ms']['candidate']for p in pairs];br=random.Random(171127);ratios=[]
        for _ in range(10000):
            indexes=[br.randrange(31)for _ in range(31)];ratios.append(statistics.median(candidate[i]for i in indexes)/statistics.median(baseline[i]for i in indexes))
        ratios.sort();point=statistics.median(candidate)/statistics.median(baseline);lo,hi=ratios[249],ratios[9749]
        row={'family':family,'mode':mode,'profile':profile,'repetitions':repetitions,'baselineMedianMs':statistics.median(baseline),'candidateMedianMs':statistics.median(candidate),'candidateBaselineRatio':point,'speedup':1/point,'pairedBootstrap95':[lo,hi],'smallCaseNonregressionPass':point<=1.03 and hi<=1.05,'warmups':warm,'pairs':pairs}
        result['rows'].append(row);(out/'TIMING.json').write_text(json.dumps(result,indent=2));print(family,mode,profile,round(point,4),[round(lo,4),round(hi,4)],flush=True)
    result['completed']=True;(out/'TIMING.json').write_text(json.dumps(result,indent=2));print('Timing complete; retain every observation')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['prepare','run']);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();(prepare if args.phase=='prepare'else run)(args.out.resolve())
