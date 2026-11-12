"""Executed negative control: two agreeing implementations can both be wrong."""
from pathlib import Path
import subprocess,struct,time,json,hashlib
R=Path(__file__).resolve().parents[2];D=R/'artifacts/contract-next'/('common-mode-'+str(time.time_ns()));D.mkdir(parents=True)
source=(R/'examples/evidence-contract/lib/engine.rf2').read_text().replace('module engine','profile RF2_SYSTEM_A64_V1',1)
assert source.count('set value=value^operand')==1 and source.count('set value=value^args[j]')==1
mutant=source.replace('set value=value^operand','set value=value|operand').replace('set value=value^args[j]','set value=value|args[j]')
probe='''
fn main(argc,argv)
 let data=Data()
 let codes=Ops()
 let args=Ops()
 let p=Plan(1,1,7,2)
 let r=Run(0,0,0,0,0,0)
 set data[0]=3
 set codes[0]=2
 set args[0]=1
 do execute(data,p,codes,args,r)
 let out=buffer("common-mode",24)
 do store64(out,data[0])
 do store64(out+8,r.code)
 do store64(out+16,r.work)
 return write(1,out,24)!=24
end
'''
rows=[]
for opt in [False,True]:
 for label,body,expected in [('original',source,(2,0,2)),('both-XOR-replaced-by-OR',mutant,(3,0,2))]:
  src=D/(label+('-opt'if opt else'')+'.rf2');src.write_text(body+probe);exe=src.with_suffix('');p=subprocess.run([R/'output/native-compiler/rf2c',src,exe]+(['--opt']if opt else[]),capture_output=True,timeout=60);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True)
  p=subprocess.run([exe],capture_output=True,timeout=10);got=struct.unpack('<3Q',p.stdout);assert p.returncode==0 and got==expected
  rows.append({'mode':opt,'variant':label,'observed':got,'independentExpectedByte':3^1,'agreementMissedError':got[0]!=(3^1)and got[1]==0,'sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest()})
report={'experimentCompleted':True,'checks':4,'negativeControlsAcceptedWrongOutput':2,'results':rows,'scope':'Known shared defect deliberately introduced into both isolated paths. Agreement accepts a wrong result in default and optimized modes. Original source untouched. This demonstrates a real boundary, not a production test pass or immunity to shared compiler/specification faults.'}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));print(D/'report.json')
