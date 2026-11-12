"""Independent parser/trajectory verifier: exhaustive one-byte ADD/XOR domain."""
from pathlib import Path
import subprocess,hashlib,struct,time,json
R=Path(__file__).resolve().parents[2];D=R/'artifacts/trust-0.18'/('verifier-exhaustive-'+str(time.time_ns()));D.mkdir(parents=True)
body=(R/'examples/evidence-contract/lib/verifier.rf2').read_text().replace('module verifier','profile RF2_SYSTEM_A64_V1',1)
body+='''
fn puttext(dst,text)
 let i=0
 while load8(text+i)!=0
  do store8(dst+i,load8(text+i))
  set i=i+1
 end
 return i
end
fn putnum(dst,v)
 let d=buffer("decimal",3)
 let i=3
 let n=0
 if v==0
  do store8(dst,48)
  return 1
 end
 while v!=0
  set i=i-1
  do store8(d+i,48+v-(v//10)*10)
  set v=v//10
 end
 while i<3
  do store8(dst+n,load8(d+i))
  set n=n+1
  set i=i+1
 end
 return n
end
fn main(argc,argv)
 let src=buffer("generated-plan",128)
 let data=buffer("verified-data",128)
 let report=buffer("verified-report",56)
 let out=buffer("verified-batch",4096)
 let opcode=1
 let value=0
 let operand=0
 let n=0
 let used=0
 let i=0
 do store8(data+127,77)
 while opcode<3
  set value=0
  while value<256
   set operand=0
   while operand<256
    set n=puttext(src,"RF2E1 allow 7 budget 2 input 1 ")
    set n=n+putnum(src+n,value)
    if opcode==1
     set n=n+puttext(src+n," steps 1 add ")
    else
     set n=n+puttext(src+n," steps 1 xor ")
    end
    set n=n+putnum(src+n,operand)
    if not(independent_plan(src,n,data,report))
     return 2
    end
    do store64(out+used,load8(data))
    do store64(out+used+8,load8(data+127))
    set i=0
    while i<48
     do store64(out+used+16+i,load64(report+i))
     set i=i+8
    end
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
src=D/'probe.rf2';src.write_text(body);rows=[]
for opt in [False,True]:
 exe=D/('verifier-opt'if opt else'verifier-default');p=subprocess.run([R/'output/native-compiler/rf2c',src,exe]+(['--opt']if opt else[]),capture_output=True,timeout=60);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True);p=subprocess.run([exe],capture_output=True,timeout=60);assert p.returncode==0 and len(p.stdout)==131072*64;raw=D/(exe.name+'.bin');raw.write_bytes(p.stdout);it=struct.iter_unpack('<8Q',p.stdout)
 for op in [1,2]:
  for v in range(256):
   for a in range(256):
    exp=(v,77,4,0,0,255,v+a,1)if op==1 and v+a>255 else(v+a if op==1 else v^a,77,0,0,0,0,0,2);actual=next(it);assert actual==exp,(opt,op,v,a,actual,exp)
 rows.append({'optimized':opt,'checks':131072,'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest(),'resultsSHA256':hashlib.sha256(p.stdout).hexdigest()})
report={'date':'2026-11-13','passed':True,'distinctCases':131072,'observations':262144,'modes':rows,'sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Independent parser and per-original-element trajectory algorithm; complete Run fields and sentinel for all one-byte ADD/XOR pairs, default/opt. Finite domain only, same RF2 compiler; no arbitrary-plan or independent-toolchain proof.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'observations':262144,'report':str(D/'report.json')},indent=2))
