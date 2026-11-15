"""Independent native Booking qualification. No physical failure claims."""
from pathlib import Path
import concurrent.futures, datetime, fcntl, hashlib, json, os, resource, signal, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[2]
COMPILER=Path(os.environ['RF2_TEST_COMPILER']).resolve()
OUT=Path(tempfile.mkdtemp(prefix='booking-qualification-',dir=ROOT/'artifacts'))
rows=[]
def check(name,ok):
 rows.append({'name':name,'passed':bool(ok)})
 (OUT/'results.json').write_text(json.dumps(rows,indent=2))
 assert ok,name
def run(exe,*args,**kw):
 return subprocess.run([str(exe),*map(str,args)],capture_output=True,timeout=15,**kw)
def build(source,dest,opt):
 p=subprocess.run(['sh',str(ROOT/'tools/build-program.sh'),str(COMPILER),str(source),str(dest),*(['--opt'] if opt else [])],capture_output=True)
 check('compile '+dest.name,p.returncode==0)
 return dest/'program'
for opt in (False,True):
 tag='opt' if opt else 'default'
 exe=build(ROOT/'examples/documents/booking.flow',OUT/tag,opt)
 db=OUT/(tag+'.db')
 def cmd(*a,**kw):return run(exe,*a,**kw)
 check(tag+' init',cmd('init',db).returncode==0)
 for date in ('1900-02-29','2100-02-29','2027-04-31','0000-01-01','2027-13-01'):
  check(tag+' invalid '+date,cmd('reserve',db,date,'09:00','10:00','Student').returncode!=0)
 check(tag+' leap 2000',cmd('reserve',db,'2000-02-29','09:00','10:00','Student').returncode==0)
 check(tag+' adjacent',cmd('reserve',db,'2000-02-29','10:00','11:00','மாணவர்').returncode==0)
 for start,end in [('09:30','10:30'),('09:00','10:00'),('08:00','12:00'),('11:00','11:00'),('12:00','11:00'),('24:00','24:00')]:
  before=db.read_bytes(); p=cmd('reserve',db,'2000-02-29',start,end,'Student')
  check(tag+' refused '+start+end,p.returncode!=0 and before==db.read_bytes())
 check(tag+' end midnight',cmd('reserve',db,'2027-01-01','23:59','24:00','Student').returncode==0)
 check(tag+' cancel',cmd('cancel',db,1).returncode==0)
 state=json.loads(cmd('list',db).stdout)
 check(tag+' restart state',state['revision']==4 and state['active']==2)
 with db.open('rb') as held:
  fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
  before=db.read_bytes(); p=cmd('reserve',db,'2027-01-02','09:00','10:00','Student')
  check(tag+' busy lock',b'35' in p.stderr and before==db.read_bytes())
 for n in range(12):
  race=OUT/f'{tag}-race-{n}.db';cmd('init',race)
  with concurrent.futures.ThreadPoolExecutor(2) as pool:
   futures=[pool.submit(cmd,'reserve',race,'2027-02-01','09:00','10:00','Student') for _ in range(2)]
   results=[f.result() for f in futures]
  check(tag+' separate process race '+str(n),sum(p.returncode==0 for p in results)==1 and json.loads(cmd('list',race).stdout)['active']==1)
 before=db.read_bytes()
 def limited():
  signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
  resource.setrlimit(resource.RLIMIT_FSIZE,(len(before)+32,len(before)+32))
 p=cmd('reserve',db,'2027-03-01','09:00','10:00','Student',preexec_fn=limited)
 check(tag+' actual short write rollback',p.returncode!=0 and before==db.read_bytes() and b'saved' not in p.stdout)
 for variant in ('torn','corrupt'):
  bad=OUT/(tag+variant+'.db'); data=bytearray(before)
  if variant=='torn':data+=b'partial'
  else:data[40]^=1
  bad.write_bytes(data);p=cmd('list',bad)
  check(tag+' '+variant+' refusal',b'9001' in p.stderr and bad.read_bytes()==data)
 link=OUT/(tag+'-link');link.symlink_to(db)
 check(tag+' symlink refused',cmd('list',link).returncode!=0)
 hard=OUT/(tag+'-hard');os.link(db,hard)
 check(tag+' multiple link refused',cmd('list',db).returncode!=0);hard.unlink()
 for name in ('','   ','bad\nname'):
  check(tag+' invalid name '+repr(name),cmd('reserve',db,'2028-01-01','09:00','10:00',name).returncode!=0)
 check(tag+' unchanged after refusals',before==db.read_bytes())
report={'compiler_sha256':hashlib.sha256(COMPILER.read_bytes()).hexdigest(),'checks':rows,'scope':'Native macOS processes, advisory locking, real file-size write limit; no power-loss or hardware validation.'}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':len(rows),'report':str(OUT/'report.json')}))
