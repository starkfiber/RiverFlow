"""Execute unchanged implemented Net oracles against source-bound local variants.

Only path/binary placement is adapted. Native images are disposable in the
guarded TMPDIR; inputs, source-hook programs, stdout/stderr and receipts persist.
No live interfaces, credentials, VM, remote compute or upstream write.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys,time
H=Path(__file__).resolve().parent;R=H.parents[2]
COMPILER=Path('/Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program')
COMPILER_SHA='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
RUNTIME=Path('/Users/ik/Projects/RiverFlow/output/bin/rf2')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def adapt(variant,family,filename,evidence,binaries):
    src=H/variant/family/filename;s=src.read_text()
    s=s.replace("Path('artifacts/rf2decision-sustained/compiler-opt').resolve()",repr(COMPILER))
    # repr(Path) is not a valid imported name; spell the explicitly pinned Path.
    s=s.replace(repr(COMPILER),'Path('+repr(str(COMPILER))+')')
    s=s.replace('experiments/rf2net/',str(H/variant)+'/')
    for before,after in [('artifacts/rf2net-dhcp-final',str(evidence/'dhcp')),('artifacts/rf2net-dns-final',str(evidence/'dns')),('artifacts/rf2net-client-services',str(evidence/'mcp'))]:s=s.replace(before,after)
    s=re.sub(r'\b(exe|dhcp|dns)=D/',lambda m:m[1]+'=BIN/',s)
    s=s.replace("mut=vd/'program'","mut=BIN/(mode+'-'+name)")
    s=s.replace("exe=d/'wrong-native'","exe=BIN/('mutant-'+name)")
    s=s.replace("b=Path('output/bin/rf2').resolve()",'b=Path('+repr(str(RUNTIME))+')')
    s='from pathlib import Path\nimport os\nBIN=Path('+repr(str(binaries))+');BIN.mkdir(parents=True,exist_ok=False)\n'+s
    path=evidence/'controllers'/(family+'-'+filename);path.parent.mkdir(exist_ok=True);path.write_text(s)
    return path
def main():
    a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);args=a.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    assert sha(COMPILER)==COMPILER_SHA
    tmp=Path(os.environ.get('TMPDIR','/tmp')).resolve();assert '/Volumes/Mac Work Cache/'in str(tmp),'Run through the guarded bank with explicit disposable native output'
    binary_root=tmp/('rf2-net-accept-'+hashlib.sha256(str(out).encode()).hexdigest()[:12]);binary_root.mkdir(exist_ok=False)
    (out/'RUNNER.py').write_bytes(Path(__file__).read_bytes())
    result={'schema':'rf2.net.acceptance.v1','compilerSHA256':sha(COMPILER),'runtimeSHA256':sha(RUNTIME),'sources':{str(p.relative_to(H)):sha(p)for p in H.rglob('*')if p.is_file()and '__pycache__'not in p.parts},'suites':[],'allPassed':False,'scope':'Existing native DHCP/durable lease/DNS/loopback UDP implemented subsets only; no OS clients, guest ABI, forwarding resolver, WAN, HA or full-firewall qualification'}
    def save():(out/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    suites=[('dhcp','verify.py','dhcp'),('dhcp','mutation_verify.py',None),('dhcp','socket_verify.py','dhcp-sockets'),('dhcp-durable','verify.py','durable'),('dns','verify.py','dns'),('dns','mutation_verify.py',None),('services','socket_verify.py','services-sockets'),('services','mcp_smoke.py',None)]
    for variant in ['baseline','candidate']:
        evidence=out/variant;evidence.mkdir();(evidence/'mcp').mkdir()
        for family,name,arg in suites:
            label=family+'-'+name;script=adapt(variant,family,name,evidence,binary_root/(variant+'-'+label));command=[sys.executable,str(script)]+([str(evidence/arg)]if arg else[])
            t=time.monotonic();p=subprocess.run(command,cwd=R,capture_output=True,timeout=180)
            (evidence/(label+'.stdout')).write_bytes(p.stdout);(evidence/(label+'.stderr')).write_bytes(p.stderr)
            row={'variant':variant,'suite':label,'command':command,'controllerSHA256':sha(script),'exit':p.returncode,'elapsedSeconds':time.monotonic()-t};result['suites'].append(row);save()
            print(variant,label,p.returncode,flush=True)
            if p.returncode:raise RuntimeError('Acceptance failed; exact stdout/stderr retained: '+str(evidence/label))
    result['disposableBinaries']={str(p):sha(p)for p in binary_root.rglob('*')if p.is_file()};result['allPassed']=True
    result['liveSourceHashesStillMatch']=all(Path(p).is_file()and sha(p)==want for p,want in json.loads((H/'SOURCE-MANIFEST.json').read_text())['inputSources'].items());assert result['liveSourceHashesStillMatch']
    save();print(json.dumps({'out':str(out),'suites':len(result['suites']),'allPassed':True}))
if __name__=='__main__':main()
