"""Apply the reviewed import guard to exact 0.50 source; frozen builders stay intact."""
from pathlib import Path
import hashlib, importlib.util, json, sys, tempfile
R = Path(__file__).resolve().parents[2]
BASE_SOURCE = '5ec6f9f43d1f76e838cb4485f7f6b60dcc0319c8d381e15541a4f14552b76c82'
OLD = ''' let flags=256
 if from_sdk
  set flags=260
 end
 let fd = open(full, flags, 0)
 do require(fd < 9223372036854775808, "module open failed")
 if from_sdk
  let metadata=buffer("sdk_module_stat",144)
  let status=syscall6(339,fd,metadata,0,0,0,0)
  if (status>>63)|((load32(metadata+4)&61440)!=32768)
   do close(fd)
   do die("SDK module must be a regular file")
  end
 end
'''
NEW = ''' # Darwin O_NOFOLLOW | O_NONBLOCK: do not wait for a special-file peer.
 let fd = open(full, 260, 0)
 do require(fd < 9223372036854775808, "module open failed")
 let file_stat = buffer("module_file_stat",144)
 let stat_result = syscall6(339,fd,file_stat,0,0,0,0)
 if stat_result!=0
  do close(fd)
  do require(0,"module stat failed")
 end
 if (load32(file_stat+4)&61440)!=32768
  do close(fd)
  if from_sdk
   do die("SDK module must be a regular file")
  end
  do require(0,"module source must be a regular file")
 end
'''
def prepare(destination):
 destination = Path(destination).resolve()
 if destination.exists(): raise ValueError('Use a new directory')
 spec = importlib.util.spec_from_file_location('rf2_sdk_composer', R/'experiments/sdk-packages/compose.py')
 module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
 with tempfile.TemporaryDirectory(prefix='rf2-intelligence-source-') as tmp:
  base = module.prepare(Path(tmp)/'baseline')
  source = (base/'compiler.flow').read_text()
 if hashlib.sha256(source.encode()).hexdigest() != BASE_SOURCE: raise ValueError('0.50 source identity changed')
 a=source.index('fn module_load('); b=source.index('fn module_append(',a)
 section=source[a:b]
 if section.count(OLD)!=1: raise ValueError('module guard patch drift')
 result=source[:a]+section.replace(OLD,NEW,1)+source[b:]
 destination.mkdir(parents=True)
 (destination/'compiler.flow').write_text(result)
 (destination/'SOURCE.json').write_text(json.dumps(dict(schema='rf2.import-guard.source.v1',baselineSourceSHA256=BASE_SOURCE,sourceSHA256=hashlib.sha256(result.encode()).hexdigest(),preparerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),authority='Trusted Darwin CLI compiler only; stable runtime unchanged'),indent=2)+'\n')
 return destination
if __name__=='__main__':
 if len(sys.argv)!=2: raise SystemExit('prepare.py NEW-DIRECTORY')
 print(prepare(sys.argv[1]))
