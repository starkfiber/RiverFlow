"""Native CLI what-if matrix; independent clean builds are the output oracle."""
from pathlib import Path
import subprocess,json,hashlib,os,time,shutil,fcntl
R=Path(__file__).resolve().parents[2];D=R/'artifacts/incremental'/('verify-'+str(time.time_ns()));D.mkdir(parents=True);B=Path(os.environ['RF2_BUILD_BIN']).resolve();C=Path(os.environ['RF2_TEST_COMPILER']).resolve();OLD=Path(os.environ.get('RF2_OLD_COMPILER',C)).resolve();src=D/'project';(src/'lib').mkdir(parents=True);cache=D/'cache';cache.mkdir(mode=0o700);results=[];serial=0;EXTRA=['--compact']if os.environ.get('RF2_INCREMENTAL_COMPACT')=='1'else[]
entry=src/'main.rf2';helper=src/'lib/helper.rf2';shared=src/'lib/shared.rf2'
original='profile RF2_SYSTEM_A64_V1\nuse "lib/helper.rf2"\nfn main(argc,argv)\nreturn compute(7)\nend\n';helper_original='module helper\nuse "lib/shared.rf2"\nfn compute(x)\nreturn adjust(x)+3\nend\n';shared_original='module shared\nfn adjust(x)\nreturn x*2\nend\n';entry.write_text(original);helper.write_text(helper_original);shared.write_text(shared_original)
def invoke(label,expect='miss',compiler=C,opt=False,clean=False,cwd=R,cache_dir=cache,source=entry,out=None):
 global serial
 serial+=1;out=out or D/f'out-{serial}';args=[B,compiler,source,out,cache_dir]+(['--opt']if opt else[])+(['--clean']if clean else[])+EXTRA;q=subprocess.run(args,capture_output=True,timeout=20,cwd=cwd,env={'PATH':'/nonexistent'})
 if expect=='refuse':
  assert q.returncode!=0,(label,q.stdout);results.append({'case':label,'outcome':'refused','stderr':q.stderr.decode(errors='replace')[:300]});return out,None
 assert q.returncode==0,(label,q.stderr);receipt=json.loads(q.stdout);assert receipt['cache']==expect,(label,receipt);oracle=D/f'clean-{serial}';p=subprocess.run([compiler,source,oracle,*(['--opt']if opt else[]),*EXTRA],capture_output=True,timeout=20,env={'PATH':'/nonexistent'});assert p.returncode==0,(label,p.stderr);assert out.read_bytes()==oracle.read_bytes(),(label,'stale output');results.append({'case':label,'outcome':receipt['cache'],'key':receipt['key'],'dependencies':receipt['dependencies'],'unsignedSHA256':hashlib.sha256(out.read_bytes()).hexdigest()});return out,receipt
_,first=invoke('first complete dependency snapshot');assert first['dependencies']==3
invoke('fresh-process hit','hit');invoke('fresh-process different cwd','hit',cwd='/tmp')
other=src/'other.rf2';other.write_text('profile RF2_SYSTEM_A64_V1\nuse "lib/shared.rf2"\nfn main(argc,argv)\nreturn adjust(3)\nend\n')
invoke('second target cold',source=other)
helper.write_text(helper_original.replace('+3','+4'));invoke('private dependency rebuilds affected target');invoke('private dependency leaves second target reusable','hit',source=other)
helper.write_text(helper_original);invoke('private dependency revert reuses first target','hit')

for opt in [True,False]:invoke('option separation '+str(opt),'miss'if opt else'hit',opt=opt)
invoke('forced clean bypasses valid cache',clean=True)
(src/'unused.rf2').write_text('not imported');invoke('unrelated file leaves target reusable','hit')
st=shared.stat();shared.write_text(shared_original.replace('x*2','x*4'));os.utime(shared,ns=(st.st_atime_ns,st.st_mtime_ns));invoke('transitive same-size same-mtime change');invoke('transitive changed hit','hit')
helper.write_text(helper_original.replace('+3','+8'));invoke('direct dependency edit')
entry.write_text(original.replace('compute(7)','compute(9)'));invoke('root edit')
shared.write_text(shared.read_text()+'# conservative comment invalidation\n');invoke('dependency comment edit')
extra=src/'lib/extra.rf2';extra.write_text('module extra\nfn bonus()\nreturn 1\nend\n');helper.write_text(helper.read_text().replace('fn compute','use "lib/extra.rf2"\nfn compute').replace('+8','+bonus()'));invoke('add dependency edge')
helper.write_text(helper_original);invoke('remove dependency edge')
extra.unlink();invoke('remove unreferenced dependency file','hit')
# Reverting all bytes may safely reuse the previous successful target image.
entry.write_text(original);shared.write_text(shared_original);helper.write_text(helper_original);invoke('revert complete snapshot','hit')
if OLD!=C:invoke('changed compiler bytes',compiler=OLD);invoke('original compiler cache remains valid','hit')
copy=D/'same-compiler';shutil.copy2(C,copy);invoke('compiler path changes but bytes identical','hit',compiler=copy)
# Malformed or truncated entries must rebuild, never bless stale data.
key=first['key'];entry_file=cache/(key+'.entry');valid=entry_file.read_bytes()
for label,data in [('truncated header',b'RF2'),('wrong magic',b'BADMAGIC'+valid[8:]),('wrong key',valid[:8]+bytes(32)+valid[40:]),('wrong declared length',valid[:40]+(1).to_bytes(8,'little')+valid[48:]),('payload bit flip',valid[:-1]+bytes([valid[-1]^1])),('truncated payload',valid[:-3])]:
 entry_file.write_bytes(data);invoke(label);assert entry_file.read_bytes()==valid,label
outside=D/'outside';outside.write_bytes(b'keep-me');entry_file.unlink();entry_file.symlink_to(outside);invoke('cache symlink does not overwrite referent');assert outside.read_bytes()==b'keep-me' and not entry_file.is_symlink()
entry_file.unlink();os.mkfifo(entry_file);invoke('cache FIFO refuses read and repairs without blocking');assert entry_file.is_file()
# Incomplete unpublished temp entries cannot be used as hits.
(cache/'dead-writer.tmp').write_bytes(valid[:100]);invoke('incomplete sibling temp ignored','hit')
shared.unlink();out,_=invoke('deleted dependency cannot hit','refuse');assert not out.exists();shared.write_text(shared_original)
shared.write_text('module shared\nfn adjust(x)\nreturn unknown(x)\nend\n');before=set(cache.glob('*.entry'));out,_=invoke('invalid changed dependency cannot hit','refuse');assert not out.exists() and set(cache.glob('*.entry'))==before;shared.write_text(shared_original)
shared.write_text('module shared\nuse "main.rf2"\n'+shared_original.split('\n',1)[1]);out,_=invoke('import cycle refuses','refuse');assert not out.exists();shared.write_text(shared_original)
for label,file in [('root',entry),('dependency',shared)]:
 data=file.read_bytes();saved=file.with_suffix('.saved');file.rename(saved);file.symlink_to(saved);out,_=invoke(label+' final symlink refuses','refuse');assert not out.exists();file.unlink();file.write_bytes(data);saved.unlink()
fifo=src/'fifo.rf2';os.mkfifo(fifo);out,_=invoke('source FIFO refuses without blocking','refuse',source=fifo);assert not out.exists()
large=src/'large.rf2';large.write_bytes(b'x'*524289);out,_=invoke('source size bound','refuse',source=large);assert not out.exists()
big=D/'oversized-compiler';big.touch();big.open('r+b').truncate(16777217);out,_=invoke('compiler size bound','refuse',compiler=big);assert not out.exists()
for kind in ['file','symlink','directory']:
 target=D/('existing-'+kind)
 if kind=='file':target.write_bytes(b'preserve')
 elif kind=='symlink':target.symlink_to(outside)
 else:target.mkdir()
 invoke('existing output '+kind+' preserved','refuse',out=target)
 if kind=='file':assert target.read_bytes()==b'preserve'
 if kind=='symlink':assert target.is_symlink() and outside.read_bytes()==b'keep-me'
cache.chmod(0o755);out,_=invoke('shared-permission cache refuses','refuse');assert not out.exists();cache.chmod(0o700)
cache_link=D/'cache-link';cache_link.symlink_to(cache);invoke('cache-root final symlink refuses','refuse',cache_dir=cache_link)
fd=os.open(cache,os.O_RDONLY);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);out,_=invoke('concurrent cache lock refuses rather than racing','refuse');assert not out.exists();os.close(fd);invoke('OS lock release permits next hit','hit')
# Admission after a failed build must still preserve a previous successful image.
invoke('post-failure recovery','hit')
compiler_entry=cache/(hashlib.sha256(C.read_bytes()).hexdigest()+'.compiler')
compiler_entry.write_bytes(b'corrupt');invoke('corrupt stored compiler is replaced before execution',clean=True);assert compiler_entry.read_bytes()==C.read_bytes()
compiler_entry.chmod(0o600);invoke('stored compiler permission mismatch repairs',clean=True);assert compiler_entry.stat().st_mode&0o777==0o700
compiler_external=D/'compiler-external';shutil.copy2(C,compiler_external);compiler_entry.unlink();os.link(compiler_external,compiler_entry);invoke('stored compiler hardlink is isolated by replacement',clean=True);assert compiler_entry.stat().st_ino!=compiler_external.stat().st_ino and compiler_external.read_bytes()==C.read_bytes()
compiler_entry.unlink();compiler_entry.symlink_to(compiler_external);invoke('stored compiler symlink is replaced without following',clean=True);assert not compiler_entry.is_symlink() and compiler_external.read_bytes()==C.read_bytes()

# Exercise a real modular application as well as small semantic probes.
real=R/'examples/file-checksum.rf2';realout,_=invoke('real checksum app cold',source=real,opt=True);invoke('real checksum app warm','hit',source=real,opt=True)
subprocess.run(['/usr/bin/codesign','-s','-',realout],capture_output=True,check=True);data=D/'document';data.write_bytes('RiverFlow தமிழ்\n'.encode());q=subprocess.run([realout,data],capture_output=True,timeout=5);assert q.returncode==0 and q.stdout.strip().decode()==hashlib.sha256(data.read_bytes()).hexdigest()
invoke('signing output leaves cached unsigned image unchanged','hit',source=real,opt=True)
# A controlled native compiler wrapper edits the original tree after the builder snapshots it.
# This is a fault-injection fixture, not a supported external compiler dependency model.
old_expected=D/'snapshot-old';subprocess.run([C,entry,old_expected,'--opt',*EXTRA],capture_output=True,check=True)
changed=shared_original.replace('x*2','x*6');literal=json.dumps(changed);wrapper_source=D/'edit-original.rf2';wrapper=D/'edit-original'
wrapper_source.write_text('profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n let fd=open('+json.dumps(str(shared))+',1281,384)\n do write(fd,'+literal+','+str(len(changed.encode()))+')\n do close(fd)\n do store64(argv,'+json.dumps(str(C))+')\n let env=buffer("env",16)\n do store64(env,"PATH=/nonexistent")\n do syscall6(59,'+json.dumps(str(C))+',argv,env,0,0,0)\n return 127\nend\n')
subprocess.run([C,wrapper_source,wrapper,'--opt'],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',wrapper],capture_output=True,check=True)
snapshot_out=D/'snapshot-output';q=subprocess.run([B,wrapper,entry,snapshot_out,cache,'--opt',*EXTRA],capture_output=True,timeout=20);assert q.returncode==0,q.stderr;receipt=json.loads(q.stdout);assert receipt['cache']=='miss' and snapshot_out.read_bytes()==old_expected.read_bytes() and shared.read_text()==changed
results.append({'case':'original edited after snapshot; result equals clean captured inputs','outcome':'miss','key':receipt['key']})
invoke('next build observes original edit',compiler=wrapper,opt=True);invoke('edited snapshot fresh-process reuse','hit',compiler=wrapper,opt=True)
shared.write_text(shared_original)

# Fresh subprocess and process-wide PATH restrictions are used for every case.
leftovers=[p.name for p in cache.iterdir()if p.name.startswith('.rf2-work-')];assert not leftovers,leftovers
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'schema':'rf2.incremental.verification.v1','passed':True,'cases':results,'caseCount':len(results),'imageFlags':EXTRA,'realApplicationExecuted':True,'inputSnapshotGranularity':'whole target and all transitive modules; not function/object code reuse','normalCompletionWorkDirectoriesLeft':leftovers,'builderSHA256':sha(B),'compilerSHA256':sha(C),'builderSourceSHA256':sha(R/'native/build/incremental.rf2'),'controllerSHA256':sha(Path(__file__)),'limits':'One local Darwin host. Private cache assumes trusted same-UID owner; hashes detect accidental corruption, not a forged malicious cache. No cross-host, concurrent source transaction, function-level or universal speed claim.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'passed':True,'cases':len(results)}))
