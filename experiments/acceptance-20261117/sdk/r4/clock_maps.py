"""Reproducible monotonic-clock controls and source-bound call-map proof.

Native binaries are rebuildable TMPDIR output; all receipts/maps stay in out.
Requires root permission for native preparation, never comparative timing.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,struct,subprocess,tempfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
EXPECTED='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def functions(p):
 out={};current=None
 for line in p.read_text().splitlines():
  x=line.split()
  if x and x[0]=='F':
   current={'offset':int(x[2]),'size':int(x[3]),'sourceTokenSHA256':x[4],'directCalls':[]};out[x[1]]=current
  elif x and x[0]=='C':current['directCalls'].append(x[1])
 return out

def entry_offset(binary):
 b=binary.read_bytes();h=struct.unpack_from('<8I',b);assert h[0]==0xfeedfacf and h[1]==0x100000c
 off=32
 for _ in range(h[4]):
  command,size=struct.unpack_from('<II',b,off)
  if command==0x80000028:return struct.unpack_from('<Q',b,off+8)[0]
  off+=size
 raise ValueError('Missing LC_MAIN')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--compiler',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert sha(a.compiler)==EXPECTED
 d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);cache=Path(tempfile.mkdtemp(prefix='sdk-clock-maps-',dir=os.environ['TMPDIR']));rows=[]
 def run(cmd):
  p=subprocess.run([str(x)for x in cmd],capture_output=True,timeout=30);row={'command':[str(x)for x in cmd],'exit':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')};rows.append(row);(d/'COMMANDS.json').write_text(json.dumps(rows,indent=2));assert p.returncode==0,row
  return p
 result={'schema':'rf2.sdk.monotonic-clock-and-map.v1','compilerSHA256':EXPECTED,'controllerSHA256':sha(Path(__file__)),'clockSourceSHA256':sha(HERE/'clock.flow'),'controlsSourceSHA256':sha(HERE/'clock-controls.flow'),'controls':{},'maps':{},'complete':False}
 for mode in ['plain','opt']:
  b=cache/('clock-'+mode);run([a.compiler,HERE/'clock-controls.flow',b,'--compact','--sdk-root',ROOT/'sdk/v1']+(['--opt']if mode=='opt'else[]));run(['codesign','-s','-',b]);run([b]);result['controls'][mode]={'programSHA256':sha(b),'arithmeticGuards':11,'liveMonotonicProbePassed':True}
 p=d/'probe.flow';p.write_text('profile RF2_SYSTEM_A64_V1\nuse "@rf2/v1/text.flow"\nfn main(argc,argv)\n let w=Writer(buffer("probe",1024),1024,0,0)\n do writer_json(w,"test",4)\n return w.error\nend\n')
 for v,sdk in [('r3',ROOT/'artifacts/acceptance-20261117/sdk/complete-r3'),('r4',ROOT/'artifacts/acceptance-20261117/sdk/r4-integration/sdk')]:
  b=cache/v;run([a.compiler,p,b,'--compact','--opt','--functions','--sdk-root',sdk]);m=d/(v+'.functions');shutil.copyfile(Path(str(b)+'.functions'),m);fs=functions(m);data=b.read_bytes();origin=entry_offset(b);assert origin==16384,'Recheck function-map origin against compiler image layout'
  selected={}
  for name in ['writer_json','writer_json_large','json_span_eligible','writer_json_scalar']:
   if name not in fs:continue
   row=fs[name].copy();code=data[origin+row['offset']:origin+row['offset']+row['size']];assert len(code)==row['size'];words=struct.unpack('<'+'I'*(len(code)//4),code);row.update(A64BLInstructionCount=sum((x&0xfc000000)==0x94000000 for x in words),machineCodeSHA256=hashlib.sha256(code).hexdigest());selected[name]=row
  result['maps'][v]={'programSHA256':sha(b),'mapSHA256':sha(m),'sdkTextSHA256':sha(sdk/'text.flow'),'codeFileOffset':origin,'functions':selected}
 assert result['maps']['r4']['functions']['json_span_eligible']['directCalls']==[]
 assert result['maps']['r4']['functions']['json_span_eligible']['A64BLInstructionCount']==0
 result['complete']=True;(d/'RESULTS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
