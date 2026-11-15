"""Execute native typed persistence against independent schema/hash and interval oracles."""
from pathlib import Path
import concurrent.futures,fcntl,hashlib,json,os,random,shutil,struct,subprocess,tempfile,time
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_STORE_COMPILER']).resolve();D=Path(tempfile.mkdtemp(prefix='typed-booking-',dir=R/'artifacts'));CHECKS=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,passed,detail=None):
 CHECKS.append(dict(name=name,passed=bool(passed),detail=detail))
 if not passed:
  (D/'FAILED.json').write_text(json.dumps(CHECKS,indent=2)+'\n');raise AssertionError((name,detail))
def run(exe,*args):return subprocess.run(list(map(str,[exe,*args])),capture_output=True,timeout=20,env={'PATH':'/nonexistent'})
def expect(exe,path,cmd,*args,error=None):
 before=path.read_bytes()if path.is_file()else None;q=run(exe,path,cmd,*args)
 if error is not None:
  check(cmd+' error '+str(error),q.returncode==2 and q.stdout==b''and q.stderr==f'Error {error}\n'.encode(),dict(exit=q.returncode,stdout=q.stdout.decode(errors='replace')[:100],stderr=q.stderr.decode(errors='replace')[:200]))
  if before is not None:check(cmd+' failed request preserves file',path.read_bytes()==before)
  return None
 check(cmd+' success',q.returncode==0 and q.stderr==b'',dict(exit=q.returncode,stdout=q.stdout.decode(errors='replace')[:100],stderr=q.stderr.decode(errors='replace')[:200]));return json.loads(q.stdout)
def snapshot(version,revision,rows,previous=b'\0'*32):
 raw=b''.join(struct.pack('<'+('5Q'if version==2 else'4Q'),*(row if version==2 else(row[0],*row[2:])))for row in rows)
 magic=f'RF2BK0{version}\n'.encode();schema=f'BKG0000{version}'.encode();header=magic+struct.pack('<Q',version)+schema+struct.pack('<QQQ',revision,len(rows),len(raw))+previous
 assert len(header)==80
 return header+raw+hashlib.sha256(header+raw).digest()+b'BKCOMMIT'
def decode(raw):
 pos=0;revision=0;previous=b'\0'*32;frames=[]
 while pos<len(raw):
  version=struct.unpack_from('<Q',raw,pos+8)[0];assert version in(1,2)
  magic,ver,schema,rev,count,size=struct.unpack_from('<8sQ8sQQQ',raw,pos);assert magic==f'RF2BK0{version}\n'.encode()and ver==version and schema==f'BKG0000{version}'.encode()and rev==revision+1
  assert raw[pos+48:pos+80]==previous and size==count*(40 if version==2 else 32)
  end=pos+80+size;assert raw[end+32:end+40]==b'BKCOMMIT'
  digest=hashlib.sha256(raw[pos:end]).digest();assert digest==raw[end:end+32]
  fmt='<5Q'if version==2 else'<4Q';rows=[struct.unpack_from(fmt,raw,pos+80+i*(40 if version==2 else 32))for i in range(count)]
  if version==1:rows=[(row[0],1,*row[1:])for row in rows]
  frames.append(dict(version=version,revision=rev,rows=rows,start=pos,end=end+40,digest=digest));pos=end+40;revision=rev;previous=digest
 return frames
def build(name,opt,changes=None):
 root=D/name;(root/'lib').mkdir(parents=True)
 for p in(R/'experiments/typed-booking/lib').iterdir():shutil.copy2(p,root/'lib'/p.name)
 for name2 in('io.flow','storage.flow'):shutil.copy2(R/'examples/documents/lib'/name2,root/'lib'/name2)
 shutil.copy2(R/'examples/evidence-contract/lib/sha256.rf2',root/'lib/sha256.rf2');shutil.copy2(R/'examples/collection-tools/lib/output.rf2',root/'lib/output.rf2');shutil.copy2(R/'experiments/typed-booking/main.flow',root/'main.flow')
 for file,old,new in changes or[]:
  p=root/file;s=p.read_text();assert s.count(old)==1,(file,old);p.write_text(s.replace(old,new,1))
 exe=root/'program';q=subprocess.run(list(map(str,[C,root/'main.flow',exe,'--functions',*(['--opt']if opt else[])])),capture_output=True,timeout=20)
 check('compile '+str(name),q.returncode==0,(q.stdout+q.stderr).decode(errors='replace')[:600]);subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],capture_output=True,check=True);return exe

def as_json(row):return dict(id=str(row[0]),room=row[1],day=row[2],start=row[3],finish=row[4])

for opt in(False,True):
 exe=build('app-'+str(opt),opt);db=D/f'normal-{opt}.db'
 check('initial empty schema',expect(exe,db,'init')==dict(revision=1,version=2,bookings=[]));check('independent initial bytes',db.read_bytes()==snapshot(2,1,[]));expect(exe,db,'init',error=17)
 rows=[(1,1,739935,540,600),(2,2,739935,540,600),(3,1,739935,600,660),(18446744073709551615,1,739936,540,600)]
 for i,row in enumerate(rows):
  result=expect(exe,db,'add',i+1,*row);check('typed committed JSON',result==dict(revision=i+2,version=2,bookings=[as_json(r)for r in rows[:i+1]]));frames=decode(db.read_bytes());check('independent bytes and digest chain',frames[-1]['rows']==rows[:i+1])
 expect(exe,db,'add',1,5,1,739935,700,720,error=409);expect(exe,db,'add',5,5,1,739935,599,610,error=409);expect(exe,db,'add',5,1,3,739935,700,720,error=17)
 for bad in[(0,1,739935,0,1),(6,0,739935,0,1),(6,17,739935,0,1),(6,1,0,0,1),(6,1,3652060,0,1),(6,1,739935,600,599),(6,1,739935,1400,1441)]:expect(exe,db,'add',5,*bad,error=22)
 check('reopen complete snapshot',expect(exe,db,'list')==dict(revision=5,version=2,bookings=[as_json(r)for r in rows]));expect(exe,db,'cancel',5,99,error=404)
 result=expect(exe,db,'cancel',5,2);expected=[r for r in rows if r[0]!=2];check('typed cancel snapshot',result==dict(revision=6,version=2,bookings=[as_json(r)for r in expected]));expect(exe,db,'cancel',5,1,error=409)
 # Native version1 codec and explicit migration; not the published RF2BOOK1 event format.
 legacy=D/f'compat-{opt}.db';expect(exe,legacy,'init-v1');r=(7,1,739935,400,450);expect(exe,legacy,'add',1,*r);expect(exe,legacy,'add',2,8,2,739935,400,450,error=426)
 legacy_bytes=legacy.read_bytes();check('v1 typed bytes',legacy_bytes==snapshot(1,1,[])+snapshot(1,2,[r],hashlib.sha256(snapshot(1,1,[])[:-40]).digest()))
 migrated=expect(exe,legacy,'migrate',2);check('migration preserves fields and supplies room',migrated==dict(revision=3,version=2,bookings=[as_json(r)]));check('migration preserves old prefix',legacy.read_bytes().startswith(legacy_bytes));expect(exe,legacy,'migrate',3,error=22);expect(exe,legacy,'add',3,8,2,739935,400,450)
 # Independently constructed version1 file is accepted and migrates too.
 independent=D/f'python-v1-{opt}.db';independent.write_bytes(snapshot(1,1,[r]));expect(exe,independent,'migrate',1);check('independent v1 roundtrip',decode(independent.read_bytes())[-1]['rows']==[r])
 # Full-frame corruption must never be called an incomplete tail or automatically discarded.
 valid=db.read_bytes();frames=decode(valid);genesis=snapshot(2,1,[]);last=frames[-1];base=valid[:last['start']]
 corruptions={
  'payload-bit':valid[:last['start']+80]+bytes([valid[last['start']+80]^1])+valid[last['start']+81:],
  'digest-bit':valid[:-40]+bytes([valid[-40]^1])+valid[-39:],
  'marker':valid[:-8]+b'BADMARK!',
  'unknown-version':genesis+snapshot(2,2,[])[0:8]+struct.pack('<Q',3)+snapshot(2,2,[])[16:],
  'schema':genesis+snapshot(2,2,[],frames[0]['digest'])[:16]+b'UNKNOWN!'+snapshot(2,2,[],frames[0]['digest'])[24:],
  'wrong-chain':genesis+snapshot(2,2,[r],b'X'*32),
  'revision-jump':genesis+snapshot(2,3,[r],frames[0]['digest']),
  'downgrade':genesis+snapshot(1,2,[r],frames[0]['digest']),
  'row-count-overflow':genesis+(lambda b:b[:32]+struct.pack('<Q',2**64-1)+b[40:])(snapshot(2,2,[],frames[0]['digest'])),
  'payload-length-overflow':genesis+(lambda b:b[:40]+struct.pack('<Q',2**64-1)+b[48:])(snapshot(2,2,[],frames[0]['digest'])),
  'bad-row-with-valid-digest':genesis+snapshot(2,2,[(0,1,739935,400,450)],frames[0]['digest']),
  'conflict-with-valid-digest':genesis+snapshot(2,2,[(1,1,739935,400,450),(2,1,739935,420,470)],frames[0]['digest']),
  'original-published-format':b'RF2BOOK1'+b'\0'*24,
 }
 for name,raw in corruptions.items():
  p=D/f'{name}-{opt}.db';p.write_bytes(raw);expect(exe,p,'list',error=9001);expect(exe,p,'recover',1,error=9001)
 # Every cut of a valid next frame: no commit before complete bytes; explicit recovery.
 next_frame=snapshot(2,7,expected,frames[-1]['digest'])
 for cut in sorted(set([1,6,7,8,9,15,16,23,24,31,32,39,40,47,48,63,79,80,119,120,len(next_frame)-41,len(next_frame)-40,len(next_frame)-9,len(next_frame)-8,len(next_frame)-1])):
  p=D/f'cut-{opt}-{cut}.db';p.write_bytes(valid+next_frame[:cut]);expect(exe,p,'list',error=9003);result=expect(exe,p,'recover',6);check('recovery truncates only verified incomplete suffix',p.read_bytes()==valid and result=={'recovered_revision':6});expect(exe,p,'list')
 for suffix in(b'garbage',b'RF2BK03\n',b'RF2BK02\n'+struct.pack('<Q',9),b'RF2BK02\n'+struct.pack('<Q',2)+b'UNKNOWN!'):
  p=D/f'unknown-tail-{opt}-{suffix.hex()}.db';p.write_bytes(valid+suffix);expect(exe,p,'recover',6,error=9001)
 # Filesystem boundaries, closed output and cooperative locks.
 symlink=D/f'symlink-{opt}';symlink.symlink_to(db);expect(exe,symlink,'list',error=62)
 hardlink=D/f'hardlink-{opt}';os.link(db,hardlink);expect(exe,db,'list',error=79);hardlink.unlink()
 with db.open('rb')as held:
  fcntl.flock(held.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);expect(exe,db,'list',error=35);expect(exe,db,'cancel',6,1,error=35)
 q=subprocess.run([str(exe),str(db),'list'],capture_output=True,preexec_fn=lambda:os.close(1));check('closed output no false success',q.returncode==2 and q.stdout==b'')
 print('typed storage functional mode',opt,'passed',flush=True)

# Failed-save controls patch explicit private fixture sources or disposable native bytes.
# These are controlled outcomes, not actual OS/power-loss claims.
for opt in(False,True):
 normal=D/('app-'+str(opt))/'program'
 partial=('lib/io.flow','fn io_write_all(fd,p,n):IO\n','fn io_write_all(fd,p,n):IO\n let injected_write=write(fd,p,17)\n if injected_write>>63\n  return err(0-injected_write)\n end\n return err(5)\n')
 sync_once=('lib/storage.flow','fn storage_sync(fd)\n','fn storage_sync(fd)\n let injected_sync=buffer("injected_sync_calls",8)\n if load64(injected_sync)==0\n  do store64(injected_sync,1)\n  return -5\n end\n')
 truncate_fail=('lib/storage.flow','fn storage_truncate(fd,size)\n','fn storage_truncate(fd,size)\n return -5\n')
 directory_fail=('lib/store.flow','fn store_parent_sync(path):IO\n','fn store_parent_sync(path):IO\n return err(5)\n')
 close_fail=('lib/store.flow',' let closed=close(fd)\n if closed>>63\n  if (request.action!=0)|(state.committed!=0)',' let actually_closed=close(fd)\n let closed=-5\n if closed>>63\n  if (request.action!=0)|(state.committed!=0)')
 cases=[('partial-write-rollback',[partial],5,False),('sync-rollback',[sync_once],5,False),('partial-rollback-uncertain',[partial,truncate_fail],9002,'partial'),('full-rollback-uncertain',[sync_once,truncate_fail],9002,True),('postcommit-close',[close_fail],9002,True)]
 for name,changes,error,committed in cases:
  fixture=build('fault-'+name+'-'+str(opt),opt,changes);db=D/f'fault-{name}-{opt}.db';expect(normal,db,'init');before=db.read_bytes();q=run(fixture,db,'add',1,1,1,739935,540,600)
  check('injected '+name+' outcome '+str(opt),q.returncode==2 and q.stdout==b''and q.stderr==f'Error {error}\n'.encode(),dict(exit=q.returncode,stderr=q.stderr.decode(errors='replace'),kind='Explicit test-source hook, not actual host failure',sourceSHA256=sha(fixture.parent/'lib/store.flow')))
  if name in('partial-write-rollback','sync-rollback'):
   new_file=D/f'new-file-rollback-{name}-{opt}.db';first=run(fixture,new_file,'init');check('failed first save safely removes its own empty file '+name+' '+str(opt),first.returncode==2 and first.stderr==b'Error 5\n'and not new_file.exists(),dict(exit=first.returncode,stderr=first.stderr.decode(errors='replace')));expect(normal,new_file,'init')
  if committed=='partial':
   check('partial failed rollback retains uncertain suffix',db.read_bytes().startswith(before)and len(db.read_bytes())==len(before)+17);expect(normal,db,'list',error=9003);expect(normal,db,'recover',0,error=409);expect(normal,db,'recover',1);check('explicit recovery restores exact prefix',db.read_bytes()==before)
  elif committed:
   check('uncertain outcome can contain complete next snapshot',decode(db.read_bytes())[-1]['revision']==2);expect(normal,db,'add',1,1,1,739935,540,600,error=409)
  else:check('failed save confirmed rollback equality',db.read_bytes()==before)
 fixture=build('fault-directory-'+str(opt),opt,[directory_fail]);db=D/f'directory-uncertain-{opt}.db';q=run(fixture,db,'init');check('directory sync failure is uncertain',q.returncode==2 and q.stdout==b''and q.stderr==b'Error 9002\n'and decode(db.read_bytes())[-1]['revision']==1)
 # Response delivery failure after confirmed mutation must not be called a clean failed save.
 db=D/f'closed-response-{opt}.db';expect(normal,db,'init');q=subprocess.run([str(normal),str(db),'add','1','1','1','739935','540','600'],capture_output=True,preexec_fn=lambda:os.close(1));check('mutating closed response is uncertain',q.returncode==2 and q.stdout==b''and q.stderr==b'Error 9002\n'and decode(db.read_bytes())[-1]['revision']==2)
 # Inject unmap refusal into the exact compiled heap helper after successful save.
 raw=bytearray(normal.read_bytes());pos=32;entry=None
 for unused in range(struct.unpack_from('<I',raw,16)[0]):
  cmd,size=struct.unpack_from('<II',raw,pos)
  if cmd==0x80000028:entry=struct.unpack_from('<Q',raw,pos+8)[0]
  pos+=size
 assert entry is not None
 fns={line.split()[1]:(entry+int(line.split()[2]),int(line.split()[3]))for line in Path(str(normal)+'.functions').read_text().splitlines()if line.startswith('F ')}
 start,size=fns['__rf2heap_drop'];sites=[i for i in range(start,start+size-3,4)if struct.unpack_from('<I',raw,i)[0]==0xd4001001];assert len(sites)==1
 at=sites[0];assert bytes(raw[at+4:at+12])==struct.pack('<II',0x54000043,0xcb0003e0)
 raw[at:at+12]=struct.pack('<III',0x92800160,0xd503201f,0xd503201f);fixture=normal.with_name('program-unmap-fault');fixture.write_bytes(raw);fixture.chmod(0o700);subprocess.run(['/usr/bin/codesign','-s','-','--force',str(fixture)],capture_output=True,check=True)
 db=D/f'unmap-uncertain-{opt}.db';expect(normal,db,'init');q=run(fixture,db,'add',1,1,1,739935,540,600);check('postcommit cleanup failure is uncertain',q.returncode==2 and q.stdout==b''and q.stderr==b'Error 9002\n'and decode(db.read_bytes())[-1]['revision']==2,dict(kind='Disposable test binary; persistent unmap refusal until exit',function='__rf2heap_drop',offset=at,inputSHA256=sha(normal),outputSHA256=sha(fixture)))
 print('typed storage fault mode',opt,'passed',flush=True)

# Real independent native processes share the same file lock/CAS implementation.
for opt in(False,True):
 exe=D/('app-'+str(opt))/'program';db=D/f'race-overlap-{opt}.db';expect(exe,db,'init')
 with concurrent.futures.ThreadPoolExecutor(max_workers=12)as pool:replies=list(pool.map(lambda i:run(exe,db,'add',1,i+1,1,739935,540,600),range(12)))
 winners=[q for q in replies if q.returncode==0];errors=[q.stderr for q in replies if q.returncode!=0]
 check('same-revision overlap has exactly one winner '+str(opt),len(winners)==1 and all(e in(b'Error 35\n',b'Error 409\n')for e in errors),dict(winners=len(winners),errors=[e.decode()for e in errors]));check('one physical committed row',len(decode(db.read_bytes())[-1]['rows'])==1)
 db=D/f'race-rooms-{opt}.db';expect(exe,db,'init')
 def client(i):
  for attempt in range(500):
   read=run(exe,db,'list')
   if read.returncode:
    if read.stderr!=b'Error 35\n':raise AssertionError(read.stderr)
   else:
    revision=json.loads(read.stdout)['revision'];q=run(exe,db,'add',revision,i+1,i+1,739935,540,600)
    if q.returncode==0:return json.loads(q.stdout)
    if q.stderr not in(b'Error 35\n',b'Error 409\n'):raise AssertionError(q.stderr)
   time.sleep(.003)
  raise AssertionError('bounded client retry budget exhausted')
 with concurrent.futures.ThreadPoolExecutor(max_workers=12)as pool:results=list(pool.map(client,range(12)))
 final=expect(exe,db,'list');check('all independent nonconflicting clients commit '+str(opt),final['revision']==13 and len(final['bookings'])==12 and {r['id']for r in final['bookings']}=={str(i+1)for i in range(12)})
 frames=decode(db.read_bytes());check('concurrent journal has complete ordered commits',len(frames)==13 and all(len(f['rows'])==f['revision']-1 for f in frames))
 # A parent directory symlink is supported without claiming path containment.
 directory=D/f'real-dir-{opt}';directory.mkdir();alias=D/f'dir-link-{opt}';alias.symlink_to(directory,target_is_directory=True);expect(exe,alias/'new.db','init');check('directory entry actually created', (directory/'new.db').is_file())
 print('typed storage process race mode',opt,'passed',flush=True)

# Fresh stateful requests execute a new native process for every operation.
for opt in(False,True):
 exe=D/('app-'+str(opt))/'program';rng=random.Random(45151126);db=D/f'fresh-stateful-{opt}.db';expect(exe,db,'init');rows=[];revision=1
 for iteration in range(120):
  stale=iteration%11==0;expected_revision=revision-1 if stale else revision
  cancel=bool(rows)and iteration%4==0
  if cancel:
   id=rng.choice(rows)[0]if iteration%8==0 else 10000+iteration
   error=409 if stale else(None if any(r[0]==id for r in rows)else 404)
   result=expect(exe,db,'cancel',expected_revision,id,error=error)
   if error is None:rows=[r for r in rows if r[0]!=id];revision+=1
  else:
   start=rng.randrange(1440);row=(iteration+1,rng.randrange(1,5),739935+rng.randrange(3),start,min(1440,start+rng.randrange(1,121)))
   if iteration%13==0 and rows:row=(rows[0][0],*row[1:])
   if iteration%17==0:row=(*row[:3],800,700)
   id,room,day,start,finish=row;error=409 if stale else None
   if error is None:
    if start>=finish:error=22
    else:
     for old in rows:
      if old[0]==id:error=17;break
      if old[1]==room and old[2]==day and old[3]<finish and start<old[4]:error=409;break
   result=expect(exe,db,'add',expected_revision,*row,error=error)
   if error is None:rows.append(row);revision+=1
  if error is None:check('fresh stateful exact JSON '+str(opt)+' '+str(iteration),result==dict(revision=revision,version=2,bookings=[as_json(r)for r in rows]))
  # Independent frame parser and fresh process agree after every rejected/successful change.
  check('fresh persisted rows '+str(opt)+' '+str(iteration),decode(db.read_bytes())[-1]['rows']==rows)
 final=expect(exe,db,'list');check('fresh final state',final==dict(revision=revision,version=2,bookings=[as_json(r)for r in rows]))
 # Full record capacity is tested with an independently encoded, semantically valid snapshot.
 maximum=[(i+1,i//16+1,739935,(i%16)*10,(i%16)*10+5)for i in range(256)];db=D/f'maximum-rows-{opt}.db';db.write_bytes(snapshot(2,1,maximum));result=expect(exe,db,'list');check('all 256 rows decoded',result['bookings']==[as_json(r)for r in maximum]);expect(exe,db,'add',1,257,1,739936,0,1,error=22);expect(exe,db,'cancel',1,1)
 # Explicit file-size limit: no short read of an oversized journal may look valid.
 db=D/f'oversized-{opt}.db';db.write_bytes(b'x'*1048577);expect(exe,db,'list',error=27)
 # Near-full but valid digest chain must refuse an oversized next snapshot before writing.
 raw=bytearray();previous=b'\0'*32
 for revision in range(1,8737):
  frame=snapshot(2,revision,[],previous);raw.extend(frame);previous=frame[-40:-8]
 db=D/f'journal-limit-{opt}.db';db.write_bytes(raw);expect(exe,db,'add',8736,1,1,739935,0,1);expect(exe,db,'add',8737,2,2,739935,0,1,error=27)
 print('typed storage fresh and budget mode',opt,'passed',flush=True)

(D/'report.json').write_text(json.dumps(dict(checks=len(CHECKS),compilerSHA256=sha(C),results=CHECKS),indent=2)+'\n');print(json.dumps(dict(checks=len(CHECKS),report=str(D/'report.json'))))
