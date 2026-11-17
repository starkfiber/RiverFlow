"""Replay self-contained public offline Net regressions, excluding private history."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
H=Path(__file__).resolve().parent;S=H/'public-regressions';R=H.parents[2]
C=Path('/Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False)
    assert sha(C)=='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
    tmp=Path(os.environ['TMPDIR']).resolve();assert '/Volumes/Mac Work Cache/'in str(tmp)
    b=tmp/('net-public-'+hashlib.sha256(str(d).encode()).hexdigest()[:12]);b.mkdir()
    support=d/'definition-source';shutil.copytree(S,support)
    for p in support.rglob('*.py'):p.write_text(p.read_text().replace('experiments/rf2net/',str(support)+'/'))
    result={'scope':'Implemented public-role offline IPv4/frame/checksum/binding/bridge/owned queue/packet queue/Intent subsets; excludes private-recovered company modules, WAN/HA and broader24gates','sources':{str(p.relative_to(H)):sha(p)for p in S.rglob('*')if p.is_file()},'builds':[],'suites':[]}
    def save():(d/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    def build(src,name,mode):
        out=b/(name+'-'+mode);cmd=[str(C),str(src),str(out),'--compact']+(['--opt']if mode=='opt'else[]);p=subprocess.run(cmd,capture_output=True,timeout=40);(d/(name+'-'+mode+'.build.log')).write_bytes(p.stdout+p.stderr);assert p.returncode==0,(name,p.stderr)
        subprocess.run(['codesign','-s','-',str(out)],check=True,capture_output=True);result['builds'].append({'command':cmd,'binarySHA256':sha(out)});save();return out
    def invoke(label,s,args=()):
        p=d/'controllers'/(label+'.py');p.parent.mkdir(exist_ok=True);p.write_text(s);t=time.monotonic();q=subprocess.run([sys.executable,str(p),*map(str,args)],cwd=R,capture_output=True,timeout=180)
        (d/(label+'.stdout')).write_bytes(q.stdout);(d/(label+'.stderr')).write_bytes(q.stderr);result['suites'].append({'name':label,'exit':q.returncode,'controllerSHA256':sha(p),'elapsedSeconds':time.monotonic()-t});save();print(label,q.returncode,flush=True);assert q.returncode==0,(label,q.stderr[-2000:])
    def common(s):return s.replace('experiments/rf2net/',str(support)+'/')
    for mode in ['plain','opt']:
        ip=build(S/'main.flow','ipv4',mode);frame=build(S/'ethernet.flow','frame',mode);bound=build(S/'bound_main.flow','binding',mode)
        packet_dir=d/('ipv4-'+mode);packet_dir.mkdir()
        s=common((S/'verify.py').read_text()).replace("Path('artifacts/rf2net-first-build/program')",'Path('+repr(str(ip))+')').replace("Path('artifacts/rf2net-first-build/RESULTS.json')",'Path('+repr(str(packet_dir/'RESULTS.json'))+')')
        invoke('ipv4-'+mode,s)
        frame_dir=d/('frame-'+mode);frame_dir.mkdir()
        s=common((S/'frames_verify.py').read_text()).replace("(exe.parent/'RESULTS.json')",'Path('+repr(str(frame_dir/'RESULTS.json'))+')');invoke('frame-'+mode,s,[frame])
        s=common((S/'checksum_verify.py').read_text()).replace("(exe.parent/'CHECKSUM-RESULTS.json')",'Path('+repr(str(frame_dir/'CHECKSUM-RESULTS.json'))+')');invoke('checksum-'+mode,s,[frame])
        bound_dir=d/('binding-'+mode);bound_dir.mkdir()
        s=common((S/'binding_verify.py').read_text()).replace("D=Path(sys.argv[1]);exe=D/'program'",'D=Path('+repr(str(bound_dir))+');exe=Path('+repr(str(bound))+')').replace("Path('artifacts/rf2decision-vector/regression/opt/net/program').resolve()",'Path('+repr(str(frame))+')');invoke('binding-'+mode,s,[bound_dir])
    # Bridge verifier generates a state-probe source. Work on our artifact-owned
    # source copy, never its original/live tree or disposable bank.
    bridge=d/'bridge-source';shutil.copytree(S/'bridge',bridge);bridge_out=d/'bridge'
    s=(bridge/'verify.py').read_text().replace("Path('experiments/rf2net/bridge')",'Path('+repr(str(bridge))+')').replace("Path('artifacts/rf2decision-sustained/compiler-opt').resolve()",'Path('+repr(str(C))+')')
    s='from pathlib import Path\nBIN=Path('+repr(str(b))+')\n'+s;s=s.replace("exe=D/('program-'+mode)","exe=BIN/('bridge-'+mode)").replace("probe=D/('state-probe-'+mode)","probe=BIN/('state-probe-'+mode)");invoke('bridge',s,[bridge_out])
    s=(bridge/'mutation_verify.py').read_text().replace("Path('experiments/rf2net/bridge')",'Path('+repr(str(bridge))+')').replace("Path('artifacts/rf2net-bridge/qualification-4')",'Path('+repr(str(bridge_out))+')').replace("Path('artifacts/rf2decision-sustained/compiler-opt').resolve()",'Path('+repr(str(C))+')').replace("exe=folder/'program'","exe=Path("+repr(str(b))+')/(\'bridge-mutant-\'+name)');invoke('bridge-mutants',s)
    for family,module,entry in [('owned-queues','queues.flow','main.flow'),('packet-queues','packets.flow','main.flow')]:
        binaries={mode:build(S/family/entry,family,mode)for mode in ['plain','opt']}
        filename='verify_v2.py'if family=='packet-queues'else'verify.py';s=(S/family/filename).read_text();s=s.replace("ROOT=Path(__file__).resolve().parents[3]",'ROOT=Path('+repr(str(R))+')')
        for mode,prior in [('opt',f'artifacts/rf2net-{ "packet"if family=="packet-queues"else"owned-queues"}-opt/program'),('plain',f'artifacts/rf2net-{ "packet"if family=="packet-queues"else"owned-queues"}-plain/program')]:
            # The owned opt path uses a historical -b directory name.
            if family=='owned-queues'and mode=='opt':prior='artifacts/rf2net-owned-queues-opt-b/program'
            s=s.replace(prior,str(binaries[mode]))
        old='artifacts/rf2net-packet-verification-v2'if family=='packet-queues'else'artifacts/rf2net-owned-queues-verification'
        s=s.replace(old,str(d/family))
        # Evidence filenames beside the adapted verifier must bind exact source.
        s=s.replace("Path(__file__).with_name('main.flow')",'Path('+repr(str(S/family/'main.flow'))+')').replace("Path(__file__).with_name('"+module+"')",'Path('+repr(str(S/family/module))+')')
        invoke(family,s)
    intent=S/'intent-channel';s=(intent/'verify.py').read_text();s=s.replace("R=Path(__file__).resolve().parents[3];V=Path(__file__).parent;D=R/'artifacts/rf2net-intent-channel'",'R=Path('+repr(str(R))+');V=Path('+repr(str(intent))+');D=Path('+repr(str(d/'intent'))+')')
    s=s.replace("compiler=R/'artifacts/rf2decision-sustained/compiler-opt'",'compiler=Path('+repr(str(C))+')').replace("b=D/('admission-'+label)",'b=Path('+repr(str(b))+')/(\'intent-\'+label)');invoke('intent',s)
    result['allPassed']=True;result['binaries']={str(p):sha(p)for p in b.iterdir()if p.is_file()};result['liveSourcesStillMatch']=all(sha(p)==want for p,want in json.loads((H/'PUBLIC-REGRESSION-SOURCES.json').read_text())['sources'].items());assert result['liveSourcesStillMatch'];save();print('Public offline regressions passed')
if __name__=='__main__':main()
