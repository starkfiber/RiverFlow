"""Independent review of sibling structured report API; never modifies its sources."""
from pathlib import Path
import importlib.util,subprocess,json,hashlib,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];O=ROOT/('artifacts/evolution-20261117/net/report-review-before' if len(sys.argv)>1 else 'artifacts/evolution-20261117/net/report-review');S=ROOT/'experiments/evolution-20261117/report'
spec=importlib.util.spec_from_file_location('reviewed_verify',S/'verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);sdk=v.stage(O)
if len(sys.argv)>1:
 (sdk/'report.flow').write_bytes((ROOT/'artifacts/evolution-20261117/report/run-1/sdk/report.flow').read_bytes())
 (sdk/'rf2-sdk.manifest').write_text('rf2-sdk-v1\n'+''.join(f'{v.digest(p)} {p.name}\n' for p in sorted(sdk.iterdir()) if p.suffix in ('.flow','.rf2')))

entry='''profile RF2_SYSTEM_A64_V1
use "@rf2/v1/report.flow"
fn main(argc,argv)
 let fmt=load8(load64(argv+8))-48
 let action=load8(load64(argv+16))-48
 let count=1024
 if action==1
  set count=1025
 end
 let out=Writer(buffer("probe",131072),131072,0,0)
 let r=Report(0,0,0)
 if action==2
  do report_field_end(r,out)
 else
  do report_begin(r,out,fmt,"T",1)
  if action==3
   do report_field(r,out,"k",1)
  else
   let i=0
   while i<count
    do report_number(r,out,"k",1,i)
    set i=i+1
   end
  end
  do report_end(r,out)
  if action==4
   do report_field_end(r,out)
  end
 end
 if out.error
  return 2
 end
 do write(1,out.data,out.used)
 return 0
end
'''
(O/'probe.flow').write_text(entry);results=[]
for mode in ['plain','opt']:
 exe=O/('probe-'+mode);p=subprocess.run(['/Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program',str(O/'probe.flow'),str(exe),'--compact','--sdk-root',str(sdk)]+(['--opt']if mode=='opt' else []),capture_output=True,timeout=30);assert p.returncode==0,p.stdout+p.stderr;subprocess.run(['codesign','-s','-',str(exe)],check=True,capture_output=True)
 for fmt in [0,1]:
  for action in range(5):
   p=subprocess.run([str(exe),str(fmt),str(action)],capture_output=True,timeout=5)
   if action==0:
    assert p.returncode==0
    if fmt==0:assert json.loads(p.stdout)==dict(title='T',fields=[dict(name='k',value=i)for i in range(1024)])
    else:assert p.stdout.count(b'<dt>k</dt>')==1024 and p.stdout.endswith(b'</dl></main></html>\n')
   if action==1:assert p.returncode==2 and not p.stdout
   results.append(dict(mode=mode,format=fmt,action=action,returncode=p.returncode,bytes=len(p.stdout),stdoutSHA256=hashlib.sha256(p.stdout).hexdigest(),misuseAccepted=action>=2 and p.returncode==0))
(O/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
