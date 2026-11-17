"""Bounded replay of retained failed empty-file case, not a performance benchmark."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,time
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--golden',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False)
    source=next((a.golden/'D-cli-plain/grade').glob('valid-0-*'));assert source.read_bytes()==b''
    binaries={name:(a.golden/('D-'+name+'-plain/program')).resolve()for name in ['cli','manual']};before={k:sha(p)for k,p in binaries.items()}
    spec=importlib.util.spec_from_file_location('oracle',HERE/'grade.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);expected=m.expected('D',source,b'');rows=[]
    for i in range(10):
        for mode in ['json','html']:
            for condition in ['cli','manual']:
                start=time.monotonic()
                try:q=subprocess.run([str(binaries[condition]),mode,str(source)],capture_output=True,timeout=8);row={'exit':q.returncode,'stdoutHex':q.stdout.hex(),'stderr':q.stderr.decode(errors='replace'),'timedOut':False,'passed':q.returncode==0 and q.stdout==expected[mode]}
                except subprocess.TimeoutExpired as e:row={'exit':None,'timedOut':True,'stdoutHex':(e.stdout or b'').hex(),'passed':False}
                row.update(condition=condition,mode=mode,iteration=i,elapsedSeconds=time.monotonic()-start);rows.append(row)
    assert before=={k:sha(p)for k,p in binaries.items()}
    record={'schema':'rf2.refinement.empty-case-replay.v1','allPassed':all(x['passed']for x in rows),'binarySHA256':before,'inputPath':str(source),'inputPathUTF8SHA256':hashlib.sha256(str(source).encode()).hexdigest(),'inputBytesSHA256':sha(source),'inputSize':0,'perConditionLaunches':20,'observationTimeoutSeconds':8,'rows':rows,'scope':'Bounded exact-case replay, no performance or transient-failure root cause claim'}
    (d/'RESULTS.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'allPassed':record['allPassed'],'launches':len(rows)}));return 0 if record['allPassed']else 1
if __name__=='__main__':raise SystemExit(main())
