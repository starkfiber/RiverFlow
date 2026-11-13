"""Controlled emitted-instruction failures, not real kernel OOM or physical-release proof."""
from pathlib import Path
import subprocess,struct,json,time,hashlib,os
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/mappings-0.21-qualified/rf2c-self'));D=R/'artifacts/mappings-0.21'/('faults-'+str(time.time_ns()));D.mkdir(parents=True);rows=[]
for kind,primary,expected in [('mmap',0,12),('munmap',0,65548),('munmap',42,42)]:
 src=D/(kind+str(primary)+'.rf2');src.write_text('''profile RF2_SYSTEM_A64_V1
result IO(u64,u64)
resource Machine(IO,vm)
resource Pages(IO,mapping)
fn work():IO
 own vm=Machine()
 own page=Pages(vm,65536,16384,3)
 return '''+('err(42)'if primary else'ok(0)')+'''
end
fn main(argc,argv)
 let tag=0
 let payload=0
 handle work()
 ok value
  set payload=value
 err cause
  set tag=1
  set payload=cause
 end
 let p=buffer("observations",16)
 do store64(p,tag)
 do store64(p+8,payload)
 do write(1,p,16)
 return 0
end
''')
 for opt in [[],['--opt']]:
  exe=D/(kind+str(primary)+('-opt'if opt else'-plain'));subprocess.run([C,src,exe,*opt],check=True,capture_output=True);before=exe.read_bytes();raw=bytearray(before);number=197 if kind=='mmap'else 73;pattern=struct.pack('<2I',0xd2800000|(number<<5)|16,0xd4001001);positions=[];offset=0
  while True:
   pos=before.find(pattern,offset)
   if pos<0:break
   offset=pos+8;positions.append(pos+4);raw[pos+4:pos+8]=struct.pack('<I',0xd2800000|(12<<5))
   if kind=='mmap':raw[pos+8:pos+12]=struct.pack('<I',0xd503201f)
  assert positions,(kind,'no exact syscall sequence')
  exe.write_bytes(raw);subprocess.run(['/usr/bin/codesign','-s','-','--force','--entitlements',R/'examples/hypervisor/entitlements.plist',exe],check=True,capture_output=True);p=subprocess.run([exe],capture_output=True,timeout=5);assert p.returncode==0 and struct.unpack('<2Q',p.stdout)==(1,expected),(kind,primary,p.returncode,p.stdout.hex(),p.stderr)
  rows.append({'kind':kind,'primaryError':primary,'optimized':bool(opt),'expectedError':expected,'observed':list(struct.unpack('<2Q',p.stdout)),'instructionOffsets':positions,'originalUnsignedSHA256':hashlib.sha256(before).hexdigest(),'patchedSignedSHA256':hashlib.sha256(exe.read_bytes()).hexdigest()})
report={'passed':True,'cases':rows,'scope':'Controlled native binary substitutions: mmap path skips success branch, returns errno12; munmap is replaced by errno12. Not an actual kernel OOM, syscall interception or physical-memory reclamation measurement.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(rows),'report':str(D/'report.json')}))
