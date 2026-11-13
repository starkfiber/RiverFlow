"""Shared private compiler-store controls; independent clean images are the oracle."""
from pathlib import Path
import subprocess,os,time,json,hashlib,fcntl,shutil
R=Path(__file__).resolve().parents[2];D=R/'artifacts/cold-profile-028'/('store-verify-'+str(time.time_ns()));D.mkdir(parents=True)
B=Path(os.environ['RF2_BUILD_BIN']).resolve();C=Path(os.environ['RF2_TEST_COMPILER']).resolve();store=D/'compiler-store';store.mkdir(mode=0o700);source=D/'main.rf2';source.write_text('profile RF2_SYSTEM_A64_V1\nfn helper(x)\n return x+4\nend\nfn main(argc,argv)\n return helper(6)!=10\nend\n');rows=[];serial=0
oracle=D/'clean';subprocess.run([C,source,oracle,'--opt','--compact'],capture_output=True,check=True);expected=oracle.read_bytes()
def invoke(label,store_path=store,expect='miss',cache=None,extra=None,out=None):
 global serial
 serial+=1
 if cache is None:cache=D/f'cache-{serial}';cache.mkdir(mode=0o700)
 out=out or D/f'out-{serial}';args=[B,C,source,out,cache,'--opt','--compact']
 if store_path is not None:args += ['--compiler-store',store_path]
 if extra:args+=extra
 q=subprocess.run(args,capture_output=True,timeout=15,env={'PATH':'/nonexistent'})
 if expect=='refuse':assert q.returncode!=0 and not out.exists(),(label,q.returncode,q.stdout,q.stderr)
 else:
  assert q.returncode==0,(label,q.stderr);assert json.loads(q.stdout)['cache']==expect;assert out.read_bytes()==expected,(label,'not clean-equivalent')
 rows.append({'case':label,'outcome':'refused'if expect=='refuse'else expect});return out,cache
_,a=invoke('first project cache creates compiler snapshot');name=hashlib.sha256(C.read_bytes()).hexdigest()+'.compiler';snapshot=store/name;original=snapshot.read_bytes();inode=snapshot.stat().st_ino;assert original==C.read_bytes() and snapshot.stat().st_mode&0o777==0o700
out,b=invoke('second project cache reuses identical checked compiler inode');assert snapshot.stat().st_ino==inode and not list(b.glob('*.compiler'));invoke('same project target hits with shared store',cache=b,expect='hit')
# Physical compiler-store location is outside the semantic image key.
other=D/'other-store';other.mkdir(mode=0o700);invoke('different valid store preserves image',store_path=other,cache=b,expect='hit')
# Default route still works, and explicitly selecting the same inode cannot self-deadlock.
_,same=invoke('default compiler store remains target cache',store_path=None);invoke('same store/cache inode shares the existing lock',store_path=same,cache=same,expect='hit');invoke('same inode with dot path shares existing lock',store_path=Path(str(same)+'/.'),cache=same,expect='hit');invoke('same store/cache inode supports a forced compiler execution',store_path=same,cache=same,extra=['--clean'])
store.chmod(0o755);invoke('shared-permission store refuses',expect='refuse');store.chmod(0o700)
link=D/'store-link';link.symlink_to(store);invoke('store final symlink refuses',store_path=link,expect='refuse')
fifo=D/'store-fifo';os.mkfifo(fifo);invoke('non-directory store refuses without blocking',store_path=fifo,expect='refuse')
fd=os.open(store,os.O_RDONLY);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);invoke('concurrent store lock refuses',expect='refuse');os.close(fd);invoke('store lock release allows recovery')
snapshot.write_bytes(b'bad');invoke('corrupt compiler store repairs before execution');assert snapshot.read_bytes()==original
snapshot.chmod(0o600);invoke('compiler permission mismatch repairs');assert snapshot.stat().st_mode&0o777==0o700
outside=D/'outside';outside.write_bytes(b'preserve-outside');snapshot.unlink();snapshot.symlink_to(outside);invoke('compiler snapshot symlink replaced without following');assert outside.read_bytes()==b'preserve-outside' and not snapshot.is_symlink()
snapshot.unlink();external=D/'compiler-hardlink';shutil.copy2(C,external);os.link(external,snapshot);invoke('compiler snapshot hardlink is replaced privately');assert snapshot.stat().st_ino!=external.stat().st_ino and external.read_bytes()==C.read_bytes()
invoke('missing compiler store argument refuses',store_path=None,extra=['--compiler-store'],expect='refuse');invoke('duplicate compiler store option refuses',extra=['--compiler-store',store],expect='refuse');invoke('unknown option after store refuses',extra=['--unsupported'],expect='refuse')
# Final image execution and normal compiler behavior remain intact.
subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True);q=subprocess.run([out],capture_output=True,timeout=5);assert q.returncode==0
report={'passed':True,'cases':rows,'count':len(rows),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'builderSHA256':hashlib.sha256(B.read_bytes()).hexdigest(),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'scope':'One host native compiler store integration; cache outputs match fresh clean bytes, immutable compiler inode reuse observed. UID mismatch code is present but a foreign-UID directory was not created. No shared hostile-user cache or crash-power guarantee.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'passed':True,'cases':len(rows)}))
