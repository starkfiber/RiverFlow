"""Build controller-only C/D controls in a guarded job; never infer provider success."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PIN='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stage_sdk(destination):
    assert not destination.exists();shutil.copytree(ROOT/'sdk/v1',destination)
    sources={'report.flow':ROOT/'experiments/evolution-20261117/report/report.flow','text-report-cli.flow':ROOT/'experiments/acceptance-20261117/ai/text-report-cli.flow'}
    for name,p in sources.items():shutil.copyfile(p,destination/name)
    files=sorted(p for p in destination.iterdir()if p.suffix in ['.flow','.rf2'])
    (destination/'rf2-sdk.manifest').write_text('rf2-sdk-v1\n'+''.join(sha(p)+' '+p.name+'\n'for p in files))
    provenance={'schema':'rf2.refinement.matched-sdk.v1','base':'Unchanged default sdk/v1 plus exact reviewed Report/CLI source; same bytes for all conditions','files':{p.name:sha(p)for p in files},'additionalSources':{str(p.relative_to(ROOT)):sha(p)for p in sources.values()},'stableChanged':False}
    (destination/'REFINEMENT-PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n');return destination

def main():
    p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert os.environ.get('TMPDIR','').startswith('/Volumes/Mac Work Cache/'),'Use guarded local bank runner'
    assert sha(a.compiler)==PIN;d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);sdk=stage_sdk(d/'sdk');cache=Path(tempfile.mkdtemp(prefix='rf2-goldens-cd-',dir=os.environ['TMPDIR']));rows=[]
    result={'schema':'rf2.refinement.golden-validation.v1','compilerSHA256':PIN,'oracleSHA256':sha(HERE/'grade.py'),'SDK':str(sdk),'SDKfiles':{p.name:sha(p)for p in sdk.iterdir()if p.is_file()},'runs':rows,'scope':'Controller golden validation only; no inference, performance claim or stable replacement'}
    def save():(d/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    for task in ['C','D']:
        for condition in ['manual','cli']:
            source=HERE/('golden-'+task+'-'+condition+'.flow')
            for mode in ['plain','opt']:
                label=task+'-'+condition+'-'+mode;out=d/label;out.mkdir();binary=cache/label
                cmd=[str(a.compiler.resolve()),str(source),str(binary),'--compact',*(['--opt']if mode=='opt'else[]),'--sdk-root',str(sdk),'--diagnostic-json']
                q=subprocess.run(cmd,capture_output=True,timeout=30);(out/'compile.stdout').write_bytes(q.stdout);(out/'compile.stderr').write_bytes(q.stderr)
                row={'label':label,'sourceSHA256':sha(source),'command':cmd,'compileExit':q.returncode,'allPassed':False};rows.append(row);save()
                if q.returncode:row['error']=q.stderr.decode(errors='replace')[:2500];save();continue
                subprocess.run(['codesign','-s','-',str(binary)],capture_output=True,check=True,timeout=10);row['binarySHA256']=sha(binary);(out/'program').symlink_to(binary)
                q=subprocess.run([sys.executable,'-B',str(HERE/'grade.py'),task,'--binary',str(binary),'--out',str(out/'grade')],capture_output=True,timeout=180);(out/'grade.stdout').write_bytes(q.stdout);(out/'grade.stderr').write_bytes(q.stderr);row['gradeExit']=q.returncode
                if(out/'grade/RESULTS.json').exists():
                    x=json.loads((out/'grade/RESULTS.json').read_text());row.update(allPassed=x['allPassed'],passed=x['passed'],total=x['total'])
                save();print(label,row['allPassed'],flush=True)
    controls=[]
    for name,expected in [('manual-own-report.flow',True),('manual-undefined-report.flow',False)]:
        source=HERE/name;cmd=[str(a.compiler.resolve()),'--check',str(source),'--sdk-root',str(sdk),'--diagnostic-json'];q=subprocess.run(cmd,capture_output=True,timeout=30)
        (d/(name+'.stdout')).write_bytes(q.stdout);(d/(name+'.stderr')).write_bytes(q.stderr);controls.append({'source':str(source),'sourceSHA256':sha(source),'compileExit':q.returncode,'expectedAdmission':expected,'passed':(q.returncode==0)==expected})
    result['conditionCompilerControls']=controls
    q=subprocess.run([sys.executable,'-B',str(HERE/'controller_controls.py'),'--out',str(d/'CONDITION-CONTROLS.json')],capture_output=True,timeout=10)
    (d/'condition-controls.stdout').write_bytes(q.stdout);(d/'condition-controls.stderr').write_bytes(q.stderr);result['conditionAdmissionControlsPassed']=q.returncode==0
    result['allPassed']=all(x['allPassed']for x in rows)and all(x['passed']for x in controls)and q.returncode==0;save();print(json.dumps({'allPassed':result['allPassed'],'builds':len(rows),'evidence':str(d)}));return 0 if result['allPassed']else 1

if __name__=='__main__':raise SystemExit(main())
