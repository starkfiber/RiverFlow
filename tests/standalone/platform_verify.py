from pathlib import Path
import subprocess,tempfile,os,json,hashlib,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'bootstrap'));from seed import Compiler
C=Path(os.environ.get('RF2_TEST_COMPILER',str(R/'output/native-compiler/rf2c')));report={'passed':False,'executedCases':0,'arityRefusals':0,'nativeReferenceImagesMatch':True}
programs=[('fork','let child = fork_process()\n if child == 0\n  return 7\n end\n let status = buffer("status", 4)\n let waited = syscall6(7, child, status, 0, 0, 0, 0)\n return (waited == child) & (load32(status) == 1792)',1),('pid','return syscall6(20, 0, 0, 0, 0, 0, 0) > 0',1),('uid','return syscall6(24, 0, 0, 0, 0, 0, 0) == '+str(os.getuid()),1),('errno','return syscall6(6, -1, 0, 0, 0, 0, 0) == -9',1),('registers','let p = syscall6(197, 0, 4096, 3, 4098, -1, 0)\n if p >= 9223372036854775808\n  return 9\n end\n do store64(p, 1234567)\n let v = load64(p)\n let done = syscall6(73, p, 4096, 0, 0, 0, 0)\n return (v == 1234567) & (done == 0)',1)]
with tempfile.TemporaryDirectory(prefix='rf2-platform-')as tmp:
 d=Path(tmp)
 for name,body,expected in programs:
  source='profile RF2_SYSTEM_A64_V1\nfn main(argc, argv)\n '+body+'\nend\n';src=d/(name+'.rf2');src.write_text(source);out=d/name;subprocess.run([C,src,out],check=True,capture_output=True,env={'PATH':'/nonexistent'});assert out.read_bytes()==Compiler().compile(source)[0];subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);assert subprocess.run([out],capture_output=True).returncode==expected;report['executedCases']+=1
 for n in [0,1,6,8]:
  src=d/f'bad{n}.rf2';out=d/f'bad{n}';src.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc, argv)\n return syscall6('+','.join(['0']*n)+')\nend\n');r=subprocess.run([C,src,out],capture_output=True);assert r.returncode==1 and not out.exists();report['arityRefusals']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),scope='Trusted macOS ARM64 systems-only syscall primitive; not a Core/MCP permission expansion, portable ABI or direct transistor-control proof');(R/'docs/PLATFORM-0.9-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
