"""Guarded golden boundary/fault acceptance. Run only after exclusive timing release."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,tempfile
HERE=Path(__file__).resolve().parent;AI=HERE.parent
PIN='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--sdk-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--full-goldens',action='store_true');p.add_argument('--model-a',type=Path);p.add_argument('--model-b',type=Path);a=p.parse_args()
    assert os.environ.get('TMPDIR','').startswith('/Volumes/Mac Work Cache/'),'Use guarded local cache runner after status'
    assert sha(a.compiler)==PIN;assert sha(a.sdk_root/'text-report-cli.flow')==sha(AI/'text-report-cli.flow')
    d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);cache=Path(tempfile.mkdtemp(prefix='rf2-cli-boundary-',dir=os.environ['TMPDIR']));rows=[]
    result={'schema':'rf2.cli-golden-boundary.v1','compilerSHA256':PIN,'sdkFiles':{str(p.resolve()):sha(p)for p in sorted(a.sdk_root.rglob('*'))if p.is_file()},'sourceFiles':{str(p.resolve()):sha(p)for p in [AI/'reference-cli-B.flow',HERE/'callback-error.flow',HERE/'writer-error.flow',HERE/'boundary_grade.py']},'runs':rows,'stableChanged':False}
    def save():(d/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    for mode in ['plain','opt']:
        md=d/mode;md.mkdir();binaries={}
        sources=[('taskB',AI/'reference-cli-B.flow'),('callback',HERE/'callback-error.flow'),('writer',HERE/'writer-error.flow')]+([('taskA',AI/'reference-cli-A.flow')]if a.full_goldens else[])
        for label,source in sources:
            binary=cache/(mode+'-'+label);cmd=[str(a.compiler.resolve()),str(source),str(binary),'--compact',*(['--opt']if mode=='opt'else[]),'--sdk-root',str(a.sdk_root.resolve()),'--diagnostic-json']
            q=subprocess.run(cmd,capture_output=True,timeout=30);(md/(label+'.compile.stdout')).write_bytes(q.stdout);(md/(label+'.compile.stderr')).write_bytes(q.stderr)
            row={'stage':mode+'/'+label+'/build','sourceSHA256':sha(source),'command':cmd,'exit':q.returncode,'passed':q.returncode==0};rows.append(row);save()
            if q.returncode:result['allPassed']=False;save();return 1
            q=subprocess.run(['codesign','-s','-',str(binary)],capture_output=True,timeout=10);assert q.returncode==0,q.stderr
            row['binarySHA256']=sha(binary);binaries[label]=binary;save()
        if a.full_goldens:
            for task in ['A','B']:
                cmd=[sys.executable,'-B',str(AI/'grade.py'),task,'--binary',str(binaries['task'+task]),'--out',str(md/('golden-'+task))]
                q=subprocess.run(cmd,capture_output=True,timeout=120);(md/('golden-'+task+'.stdout')).write_bytes(q.stdout);(md/('golden-'+task+'.stderr')).write_bytes(q.stderr);rows.append({'stage':mode+'/golden-'+task,'exit':q.returncode,'passed':q.returncode==0,'graderSHA256':sha(AI/'grade.py')});save()
        cmd=[sys.executable,'-B',str(HERE/'boundary_grade.py'),'--binary',str(binaries['taskB']),'--callback-error',str(binaries['callback']),'--writer-error',str(binaries['writer']),'--out',str(md/'grade')]
        q=subprocess.run(cmd,capture_output=True,timeout=120);(md/'grade.stdout').write_bytes(q.stdout);(md/'grade.stderr').write_bytes(q.stderr);rows.append({'stage':mode+'/grade','exit':q.returncode,'passed':q.returncode==0,'graderSHA256':sha(HERE/'boundary_grade.py')});save()
    for label,binary in [('A',a.model_a),('B',a.model_b)]:
        if not binary:continue
        grader=HERE/('mode_grade.py'if label=='A'else'boundary_grade.py')
        cmd=[sys.executable,'-B',str(grader),'--binary',str(binary.resolve()),'--out',str(d/('model-'+label))]
        if label=='B':cmd+=['--callback-error',str(binaries['callback']),'--writer-error',str(binaries['writer'])]
        q=subprocess.run(cmd,capture_output=True,timeout=120);(d/('model-'+label+'.stdout')).write_bytes(q.stdout);(d/('model-'+label+'.stderr')).write_bytes(q.stderr)
        rows.append({'stage':'model-'+label+'/supplement','exit':q.returncode,'passed':q.returncode==0,'binarySHA256':sha(binary),'graderSHA256':sha(grader)});save()
    result['allPassed']=all(r['passed']for r in rows);save();print(json.dumps({'allPassed':result['allPassed'],'stages':len(rows),'evidence':str(d)}));return 0 if result['allPassed']else 1
if __name__=='__main__':raise SystemExit(main())
