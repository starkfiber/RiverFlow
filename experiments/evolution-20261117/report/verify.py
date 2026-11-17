"""Independent native report oracle; creates a new private local evidence directory."""
import argparse,hashlib,html,importlib.util,json,random,shutil,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
COMPILER_SHA='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stage(out,accelerated=False):
    out.mkdir(parents=True,exist_ok=False)
    sdk=out/'sdk'
    if accelerated:
        path=Path(__file__).resolve().parents[1]/'sdk/stage_sdk.py'
        spec=importlib.util.spec_from_file_location('reviewed_sdk_stage',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.stage(sdk)
    else:shutil.copytree(ROOT/'sdk/v1',sdk)
    shutil.copyfile(Path(__file__).with_name('report.flow'),sdk/'report.flow')
    (sdk/'rf2-sdk.manifest').write_text('rf2-sdk-v1\n'+''.join(f'{digest(p)} {p.name}\n' for p in sorted(sdk.iterdir()) if p.suffix in ('.flow','.rf2')))
    return sdk

ENTRY='''profile RF2_SYSTEM_A64_V1
use "@rf2/v1/report.flow"
fn decimal(p)
 let n=0
 let i=0
 while load8(p+i)
  set n=n*10+load8(p+i)-48
  set i=i+1
 end
 return n
end
fn main(argc,argv)
 if argc!=8
  return 2
 end
 let format=decimal(load64(argv+8))
 let title=load64(argv+16)
 let key=load64(argv+24)
 let value=load64(argv+32)
 let count=decimal(load64(argv+40))
 let capacity=decimal(load64(argv+48))
 let action=decimal(load64(argv+56))
 let out=Writer(buffer("report_probe",32768),capacity,0,0)
 let report=Report(0,0,0)
 if action==1
  do report_end(report,out)
 end
 do report_begin(report,out,format,title,io_size(title))
 if action==2
  do report_begin(report,out,format,title,io_size(title))
 end
 do report_text(report,out,key,io_size(key),value,io_size(value))
 do report_number(report,out,"Count",5,count)
 do report_end(report,out)
 if action==3
  do report_end(report,out)
 end
 if action==4
  do report_number(report,out,"Late",4,1)
 end
 if out.error
  return 2
 end
 handle io_write_no_sigpipe(1,out.data,out.used)
 ok written
  return 0
 err cause
  return 2
 end
 return 2
end
'''

def expected(fmt,title,key,value,count):
    if fmt==0:return (json.dumps({'title':title,'fields':[{'name':key,'value':value},{'name':'Count','value':count}]},ensure_ascii=False,separators=(',',':'))+'\n').encode()
    e=lambda s:html.escape(s,quote=True).replace('&#x27;','&#39;')
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><title>{e(title)}</title><main><h1>{e(title)}</h1><dl><dt>{e(key)}</dt><dd>{e(value)}</dd><dt>Count</dt><dd>{count}</dd></dl></main></html>\n'.encode()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--compiler',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--accelerated',action='store_true');a=ap.parse_args()
    assert digest(a.compiler)==COMPILER_SHA,'Select the qualified0.50 compiler'
    out=a.out.resolve();sdk=stage(out,a.accelerated);entry=out/'probe.flow';entry.write_text(ENTRY)
    rng=random.Random(20261117);alphabet='abc\"\\<>&\'\t\r\né中😀'
    samples=[('Title','Name','hello',0),('','', '',18446744073709551615),('<&','quote\"',"'<>&\\\n",42)]
    samples += [('T'+str(i),'K'+str(i),''.join(rng.choice(alphabet)for _ in range(rng.randrange(100))),rng.randrange(1<<64))for i in range(80)]
    checks=[]
    for mode in ('plain','opt'):
        binary=out/f'probe-{mode}';cmd=[str(a.compiler),str(entry),str(binary),'--compact','--sdk-root',str(sdk)]+(['--opt']if mode=='opt'else[])
        p=subprocess.run(cmd,capture_output=True,timeout=30);assert p.returncode==0,p.stderr.decode()
        subprocess.run(['codesign','-s','-',str(binary)],check=True,capture_output=True)
        for fmt in (0,1):
            for title,key,value,count in samples:
                wanted=expected(fmt,title,key,value,count)
                for cap in (32768,len(wanted),len(wanted)-1,0):
                    p=subprocess.run([str(binary),str(fmt),title,key,value,str(count),str(cap),'0'],capture_output=True,timeout=10)
                    okay=cap>=len(wanted)
                    assert (p.returncode==0 and p.stdout==wanted)if okay else(p.returncode==2 and p.stdout==b''),(mode,fmt,cap,p.stdout,wanted)
                    checks.append([mode,fmt,cap,okay])
            for action in (1,2,3,4):
                p=subprocess.run([str(binary),str(fmt),'T','K','V','1','32768',str(action)],capture_output=True,timeout=3);assert p.returncode==2 and not p.stdout
                checks.append([mode,fmt,'state',action])
        for fmt in (2,99):
            p=subprocess.run([str(binary),str(fmt),'T','K','V','1','32768','0'],capture_output=True,timeout=3);assert p.returncode==2 and not p.stdout
            checks.append([mode,fmt,'invalid-mode'])
        for invalid in (b'\xff',b'\xc0\x80',b'\xed\xa0\x80',b'\x01'):
            p=subprocess.run([bytes(binary),'0','T','K',invalid,'1','32768','0'],capture_output=True,timeout=3);assert p.returncode==2 and not p.stdout
            checks.append([mode,'invalid-utf8',invalid.hex()])
    result={'schema':'rf2.report.verify.v1','checks':len(checks),'modes':['plain','opt'],'acceleratedWriter':a.accelerated,'compilerSHA256':digest(a.compiler),'moduleSHA256':digest(sdk/'report.flow'),'cases':checks,'scope':'Typed text/u64 JSON and HTML report, bounded bytes, state refusals, no partial success on validation/capacity failure. Not generic nested JSON or a sandbox.'}
    (out/'RESULTS.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='cases'}))
if __name__=='__main__':main()
