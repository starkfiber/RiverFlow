"""Emit direct calls and machine bodies without performance timing."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,struct,subprocess,tempfile
from stage_sdk import ROOT,HERE,stage
spec=importlib.util.spec_from_file_location('prior_maps',ROOT/'experiments/acceptance-20261117/sdk/r4/clock_maps.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('compiler',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();assert sha(a.compiler)==prior.EXPECTED
 d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);sdk=stage(d/'sdk');oldspec=importlib.util.spec_from_file_location('prior_stage',ROOT/'experiments/acceptance-20261117/sdk/stage_sdk.py');old=importlib.util.module_from_spec(oldspec);oldspec.loader.exec_module(old);old.stage(d/'r3-sdk');cache=Path(tempfile.mkdtemp(prefix='serializer-maps-',dir=os.environ['TMPDIR']));p=d/'probe.flow';p.write_text('profile RF2_SYSTEM_A64_V1\nuse "@rf2/v1/text.flow"\nfn main(argc,argv)\n let out=Writer(buffer("probe",1024),1024,0,0)\n do writer_json(out,"test",4)\n return out.error\nend\n');rows={}
 for mode in ['plain','opt']:
  exe=cache/mode;cmd=[str(a.compiler),str(p),str(exe),'--sdk-root',str(sdk),'--compact','--functions']+(['--opt']if mode=='opt'else[]);q=subprocess.run(cmd,capture_output=True,timeout=30);(d/(mode+'.compile.stderr')).write_bytes(q.stderr);assert q.returncode==0,q.stderr;m=d/(mode+'.functions');shutil.copyfile(Path(str(exe)+'.functions'),m);fs=prior.functions(m);b=exe.read_bytes();origin=prior.entry_offset(exe);chosen={}
  for name in ['writer_json','writer_json_large','writer_json_dense','json_emit_byte','writer_json_disjoint_spans','writer_json_scalar','writer_text','writer_bytes','io_size','io_copy']:
   f=fs[name].copy();code=b[origin+f['offset']:origin+f['offset']+f['size']];words=struct.unpack('<'+'I'*(len(code)//4),code);f.update(machineCodeSHA256=hashlib.sha256(code).hexdigest(),BLinstructions=sum((x&0xfc000000)==0x94000000 for x in words));chosen[name]=f
  assert chosen['json_emit_byte']['BLinstructions']==0;assert chosen['json_emit_byte']['directCalls']==[]
  before=cache/('r3-'+mode);oldcmd=[str(a.compiler),str(p),str(before),'--sdk-root',str(d/'r3-sdk'),'--compact','--functions']+(['--opt']if mode=='opt'else[]);q=subprocess.run(oldcmd,capture_output=True,timeout=30);(d/('r3-'+mode+'.compile.stderr')).write_bytes(q.stderr);assert q.returncode==0,q.stderr;oldmap=d/('r3-'+mode+'.functions');shutil.copyfile(Path(str(before)+'.functions'),oldmap);oldfunctions=prior.functions(oldmap)
  same_small=oldfunctions['writer_json']['sourceTokenSHA256']==chosen['writer_json']['sourceTokenSHA256'];assert same_small
  rows[mode]={'programSHA256':sha(exe),'mapSHA256':sha(m),'functions':chosen,'r3ProgramSHA256':sha(before),'r3MapSHA256':sha(oldmap),'smallWriterSourceTokensUnchanged':same_small,'r3ScalarCallDependencies':oldfunctions['writer_json_scalar']['directCalls']}

 result={'complete':True,'compilerSHA256':sha(a.compiler),'candidateSHA256':sha(HERE/'json_spans.flow'),'stagedTextSHA256':sha(sdk/'text.flow'),'modes':rows};(d/'RESULTS.json').write_text(json.dumps(result,indent=2));print('leaf emitter verified both modes')
if __name__=='__main__':main()
