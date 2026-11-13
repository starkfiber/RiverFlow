"""Native .flow entry/import tests and unchanged local path boundaries."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();D=R/'artifacts/flow-modules'/str(time.time_ns());D.mkdir(parents=True);(D/'lib').mkdir();rows=[]
def run(args):return subprocess.run(list(map(str,args)),capture_output=True,timeout=20,env={'PATH':'/nonexistent'})
(D/'lib/math.flow').write_text('module math\nfn calculate(x)\n return x*3\nend\n');(D/'lib/other.rf2').write_text('module other\nfn offset(x)\n return x+1\nend\n')
for opt in [False,True]:
 src=D/'main.flow';src.write_text('profile RF2_SYSTEM_A64_V1\nuse "lib/math.flow"\nuse "lib/other.rf2"\nfn main(argc,argv)\n return offset(calculate(14))!=43\nend\n');out=D/('native-'+str(opt));q=run([C,src,out,'--compact',*(['--opt']if opt else[])]);assert q.returncode==0,q.stderr
 subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);assert run([out]).returncode==0;rows.append(dict(case='native .flow entry and mixed imports execute',optimized=opt))
 q=run([C,'--check',src]);assert q.returncode==0,q.stderr;rows.append(dict(case='.flow native check',optimized=opt))
 for index,path in enumerate(['../math.flow','/math.flow','lib//math.flow','lib/.flow','.flow','lib/math.FLOW','lib/math.txt','lib/x..flow','lib/math.flow/','lib/a\x00.flow']):
  src.write_bytes(('profile RF2_SYSTEM_A64_V1\nuse "'+path+'"\nfn main(argc,argv)\n return 0\nend\n').encode());out=D/f'bad-{opt}-{index}';q=run([C,src,out,*(['--opt']if opt else[])]);assert q.returncode!=0 and not out.exists(),(path,q.stderr);rows.append(dict(case='unsafe or unsupported path refuses',path=path,optimized=opt))
# A mixed-extension cycle remains a cycle, rather than a way around module budgets.
(D/'lib/math.flow').write_text('module math\nuse "lib/other.rf2"\n');(D/'lib/other.rf2').write_text('module other\nuse "lib/math.flow"\n');src=D/'cycle.flow';src.write_text('profile RF2_SYSTEM_A64_V1\nuse "lib/math.flow"\nfn main(argc,argv)\n return 0\nend\n');q=run([C,'--check',src]);assert q.returncode!=0;rows.append(dict(case='mixed-extension cycle refuses'))
# Naming a source .flow cannot silently enable an unimplemented firmware target.
src=D/'not-firmware.flow';src.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return 0\nend\n');out=D/'not-firmware';q=run([C,src,out,'--target','esp32c3']);assert q.returncode!=0 and not out.exists();rows.append(dict(case='unimplemented ESP32 target refuses'))
report=dict(passed=True,cases=rows,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Native Apple Silicon Mac source extension/import qualification. This does not establish any ESP32/Arduino/embedded target.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(D/'report.json'),cases=len(rows))))
