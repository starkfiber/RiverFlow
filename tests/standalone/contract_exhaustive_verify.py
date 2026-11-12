"""Exhaustive one-byte one-operation domain; not exhaustive plan verification."""
from pathlib import Path
import subprocess,struct,hashlib,json,time
R=Path(__file__).resolve().parents[2];D=R/'artifacts/contract-next'/('exhaustive-'+str(time.time_ns()));D.mkdir(parents=True)
engine=(R/'examples/evidence-contract/lib/engine.rf2').read_text().replace('module engine','profile RF2_SYSTEM_A64_V1',1)
probe='''
fn main(argc,argv)
 let data=Data()
 let codes=Ops()
 let args=Ops()
 let p=Plan(1,1,7,2)
 let r=Run(0,0,0,0,0,0)
 let opcode=1
 let value=0
 let operand=0
 let used=0
 let out=buffer("exhaustiveout",4096)
 set data[127]=77
 while opcode<3
  set codes[0]=opcode
  set value=0
  while value<256
   set operand=0
   while operand<256
    set data[0]=value
    set args[0]=operand
    do execute(data,p,codes,args,r)
    do store64(out+used,data[0])
    do store64(out+used+8,data[127])
    do store64(out+used+16,r.code)
    do store64(out+used+24,r.step)
    do store64(out+used+32,r.index)
    do store64(out+used+40,r.expected)
    do store64(out+used+48,r.actual)
    do store64(out+used+56,r.work)
    set used=used+64
    if used==4096
     if write(1,out,used)!=used
      return 2
     end
     set used=0
    end
    set operand=operand+1
   end
   set value=value+1
  end
  set opcode=opcode+1
 end
 return used!=0
end
'''
rows=[]
for opt in [False,True]:
 src=D/('probe-opt.rf2'if opt else'probe-default.rf2');src.write_text(engine+probe);exe=src.with_suffix('');p=subprocess.run([R/'output/native-compiler/rf2c',src,exe]+(['--opt']if opt else[]),capture_output=True,timeout=60);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True)
 p=subprocess.run([exe],capture_output=True,timeout=60);assert p.returncode==0 and not p.stderr;assert len(p.stdout)==131072*64
 raw=D/(exe.name+'.results.bin');raw.write_bytes(p.stdout);records=struct.iter_unpack('<8Q',p.stdout);checks=0;refused=0
 for op in [1,2]:
  for v in range(256):
   for a in range(256):
    got=next(records)
    if op==1 and v+a>255:expected=(v,77,4,0,0,255,v+a,1);refused+=1
    else:expected=(v+a if op==1 else v^a,77,0,0,0,0,0,2)
    assert got==expected,(opt,op,v,a,got,expected);checks+=1
 rows.append({'optimized':opt,'checks':checks,'overflowRefusals':refused,'sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest(),'resultsSHA256':hashlib.sha256(p.stdout).hexdigest()})
report={'passed':True,'checks':sum(x['checks']for x in rows),'distinctInputOperationCases':131072,'modes':rows,'engineSHA256':hashlib.sha256((R/'examples/evidence-contract/lib/engine.rf2').read_bytes()).hexdigest(),'testSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Every one-byte ADD and XOR operand/input pair, plus sentinel tail byte and complete Run witness, default/optimized. Does not enumerate arbitrary multistep plans, all128byte states, arbitrary code or independent compiler implementations.'}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));print(D/'report.json')
