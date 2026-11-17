"""Independent dense/C0/unsigned-state controls; no comparative timings."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,tempfile
from stage_sdk import ROOT,HERE,stage
spec=importlib.util.spec_from_file_location('oracle',ROOT/'experiments/acceptance-20261117/sdk/qualify.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('compiler',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();assert sha(a.compiler)==oracle.COMPILER_HASH
 d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);sdk=stage(d/'sdk');cache=Path(tempfile.mkdtemp(prefix='serializer-extra-',dir=os.environ['TMPDIR']));receipt={'complete':False,'sourceSHA256':sha(HERE/'json_spans.flow'),'compilerSHA256':sha(a.compiler),'commands':[],'checks':[]}
 def save():(d/'RESULTS.json').write_text(json.dumps(receipt,indent=2))
 def run(cmd):
  p=subprocess.run([str(x)for x in cmd],capture_output=True,timeout=30);receipt['commands'].append({'command':[str(x)for x in cmd],'exit':p.returncode,'stderr':p.stderr.decode(errors='replace')});save();assert p.returncode==0,receipt['commands'][-1];return p
 cases=[bytes([c])*257 for c in list(range(32))+[34,92]]
 cases += [(b'"\\\n\r\t'*60)+b'last',b'A'*32+b'\0'*300,b'"'*8+b'A'*24+b'\x01'*300,bytes(range(256))*3]
 (d/'inputs').mkdir();sources=[]
 for i,data in enumerate(cases):p=d/'inputs'/str(i);p.write_bytes(data);sources.append(p)
 (d/'task.flow').write_text((HERE/'task.flow.in').read_text().replace('__CANDIDATE_IMPORT__','').replace('__JSON__','writer_json'))
 for mode in ['plain','opt']:
  flags=['--opt']if mode=='opt'else[];exe=cache/mode;run([a.compiler,d/'task.flow',exe,'--sdk-root',sdk,*flags]);run(['codesign','-s','-',exe])
  for i,p in enumerate(sources):
   data=p.read_bytes()
   for cap in list(range(15))+[256,257,258,len(data),len(oracle.raw_oracle(data,16777216)[1])-1,len(oracle.raw_oracle(data,16777216)[1])]:
    for used,error in [(0,0),(3,0),(min(cap+1,16),0),(0,7)]:
     expected=oracle.raw_oracle(data,cap,used,error);q=subprocess.run([str(exe),'0',str(p),'1',str(cap),str(used),str(error),'1'],capture_output=True,timeout=30);ok=(q.returncode,q.stdout,q.stderr)==expected;receipt['checks'].append({'mode':mode,'case':i,'capacity':cap,'used':used,'error':error,'passed':ok})
     if not ok:
      receipt['failure']={'check':receipt['checks'][-1],'actual':{'exit':q.returncode,'stdoutHex':q.stdout.hex(),'stderrHex':q.stderr.hex()},'expected':{'exit':expected[0],'stdoutHex':expected[1].hex(),'stderrHex':expected[2].hex()}};save();raise AssertionError(receipt['checks'][-1])
  state=cache/('state-'+mode);run([a.compiler,HERE/'writer-state.flow',state,'--sdk-root',sdk,*flags]);run(['codesign','-s','-',state]);run([state]);receipt['checks'].append({'mode':mode,'unsignedWriterStates':16,'passed':True});save()
 receipt['complete']=True;receipt['allPassed']=all(c['passed']for c in receipt['checks']);save();print(len(receipt['checks']))
if __name__=='__main__':main()
