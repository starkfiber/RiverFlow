"""Explicit source-injected storage failures, separate from real OS failures."""
from pathlib import Path
import json,os,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2];HOME=Path(os.environ['RF2_TEST_HOME']).resolve()
OUT=Path(tempfile.mkdtemp(prefix='booking-faults-',dir=ROOT/'artifacts'));rows=[]
def check(name,ok):
 rows.append(dict(name=name,passed=bool(ok)));(OUT/'results.json').write_text(json.dumps(rows,indent=2));assert ok,name
for mode in ('sync-once','sync-always','truncate-fails'):
 source=OUT/mode;shutil.copytree(ROOT/'examples/documents',source)
 p=source/'lib/storage.flow';s=p.read_text()
 if mode=='sync-once':
  s=s.replace(' return syscall6(95,fd,0,0,0,0,0)',' let seen=buffer("test_sync_count",8)\n let count=load64(seen)\n do store64(seen,count+1)\n if count==0\n  return 18446744073709551611\n end\n return syscall6(95,fd,0,0,0,0,0)')
 else:s=s.replace(' return syscall6(95,fd,0,0,0,0,0)',' return 18446744073709551611')
 if mode=='truncate-fails':s=s.replace(' return syscall6(201,fd,size,0,0,0,0)',' return 18446744073709551611')
 p.write_text(s);dest=OUT/(mode+'-bin')
 q=subprocess.run(['sh',str(ROOT/'tools/build-program.sh'),str(HOME/'rf2c'),str(source/'booking.flow'),str(dest),'--opt'],capture_output=True)
 check(mode+' compile',q.returncode==0)
 db=OUT/(mode+'.db');db.write_bytes(b'RF2BOOK1'+bytes(24));before=db.read_bytes()
 q=subprocess.run([str(dest/'program'),'reserve',str(db),'2027-01-01','09:00','10:00','Test'],capture_output=True,timeout=10)
 check(mode+' no success',q.returncode!=0 and b'saved' not in q.stdout)
 if mode=='sync-once':check(mode+' verified rollback',db.read_bytes()==before and b'9002' not in q.stderr)
 else:check(mode+' uncertain explicit',b'9002' in q.stderr)
 if mode=='truncate-fails':check(mode+' not falsely rolled back',len(db.read_bytes())==160)
(OUT/'report.json').write_text(json.dumps({'checks':rows,'scope':'Fault-injected disposable source copies. Simulated fsync/truncate errors, not an actual disk fault or power-cut qualification.'},indent=2))
print(json.dumps({'passed':len(rows),'report':str(OUT/'report.json')}))
