"""Execute explicit SDK-root controls against a supplied native compiler."""
from pathlib import Path
import hashlib, importlib.util, json, os, shutil, subprocess, sys, tempfile

R=Path(__file__).resolve().parents[2]
C=Path(sys.argv[1]).resolve()
D=Path(tempfile.mkdtemp(prefix='sdk-packages-checks-',dir=R/'artifacts'))
rows=[]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('rf2_test_sdk_package',R/'experiments/sdk-packages/package.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
SDK=pack.create(D/'shared-sdk')
def record(name,good,detail=''):
    row=dict(name=name,passed=bool(good),detail=str(detail));rows.append(row)
    (D/'RESULTS.json').write_text(json.dumps(dict(compiler=str(C),compilerSHA256=sha(C),checks=rows,allPassed=all(x['passed'] for x in rows)),indent=2)+'\n')
    if not good:raise AssertionError(row)
def compile_at(name,source,mode,sdk=SDK,files=None,expected=None,extra=()):
    w=D/(name+'-'+mode);w.mkdir()
    (w/'main.flow').write_text(source)
    for p,s in (files or {}).items():
        q=w/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s)
    out=w/'program'
    command=[str(C),str(w/'main.flow'),str(out)]
    if mode=='opt':command+=['--opt']
    if sdk is not None:command+=['--sdk-root',str(sdk)]
    command+=list(extra)
    p=subprocess.run(command,capture_output=True,timeout=30)
    (w/'COMPILE.log').write_bytes(p.stdout+p.stderr)
    (w/'COMMAND.json').write_text(json.dumps(command)+'\n')
    if expected is not None:
        record(name+' '+mode+' refused',p.returncode!=0 and not out.exists() and expected in p.stderr.decode(errors='replace'),p.stderr.decode(errors='replace'))
        return None
    record(name+' '+mode+' compiled',p.returncode==0,p.stderr.decode(errors='replace'))
    subprocess.run(['/usr/bin/codesign','-s','-',str(out)],check=True,capture_output=True)
    return out
def run(out,expected=0):
    p=subprocess.run([str(out)],capture_output=True,timeout=10,env=dict(os.environ,PATH='/nonexistent'))
    record(str(out.parent.relative_to(D))+' native result',p.returncode==expected,(p.returncode,p.stdout,p.stderr))
def custom(name,modules,header='rf2-sdk-v1\n',tail=''):
    d=D/name;d.mkdir();lines=[]
    for n,s in modules.items():
        p=d/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
        lines.append(sha(p)+' '+n+'\n')
    (d/'rf2-sdk.manifest').write_text(header+''.join(lines)+tail)
    return d
base='module shared\nfn answer()\n return 7\nend\n'
simple=custom('simple-sdk',{'shared.flow':base})
entry='profile RF2_SYSTEM_A64_V1\nuse "@rf2/v1/shared.flow"\nfn main(argc,argv)\n return answer()-7\nend\n'
text='profile RF2_SYSTEM_A64_V1\nuse "@rf2/v1/text.flow"\nfn main(argc,argv)\n let t=TextInfo(0,0,0,0)\n do text_measure("hello world",11,t)\n return (t.words-2)|(t.scalars-11)\nend\n'
collection='profile RF2_SYSTEM_A64_V1\nuse "@rf2/v1/collections.flow"\nfn sample():IO\n own xs=Items()\n do try collection_push(xs,7)\n do try collection_push(xs,8)\n let a=try collection_get(xs,0)\n let b=try collection_get(xs,1)\n return ok(a+b-15)\nend\nfn main(argc,argv)\n handle sample()\n ok value\n  return value\n err cause\n  return 2\n end\n return 2\nend\n'
bad_digest=custom('bad-digest',{'shared.flow':base});(bad_digest/'shared.flow').write_text(base.replace('7','8'))
unlisted=custom('unlisted',{'other.flow':base});(unlisted/'shared.flow').write_text(base)
wrong_version=custom('wrong-version',{'shared.flow':base},header='rf2-sdk-v2\n')
duplicate=custom('duplicate',{'shared.flow':base});manifest=(duplicate/'rf2-sdk.manifest').read_text();(duplicate/'rf2-sdk.manifest').write_text(manifest+manifest.splitlines(keepends=True)[1])
traversal=custom('traversal',{'shared.flow':base},tail='0'*64+' ../outside.flow\n')
bad_hex=custom('uppercase',{'shared.flow':base});(bad_hex/'rf2-sdk.manifest').write_text('rf2-sdk-v1\n'+'A'*64+' shared.flow\n')
no_lf=custom('no-final-lf',{'shared.flow':base});(no_lf/'rf2-sdk.manifest').write_text((no_lf/'rf2-sdk.manifest').read_text().rstrip('\n'))
too_big=custom('oversized-manifest',{'shared.flow':base});(too_big/'rf2-sdk.manifest').write_bytes(b'rf2-sdk-v1\n'+b'x'*32758)
entries32=custom('entries-32',{'file'+str(i)+'.flow':'module module'+str(i)+'\n' for i in range(32)})
entries33=custom('entries-33',{'file'+str(i)+'.flow':'module module'+str(i)+'\n' for i in range(33)})
cycle=custom('cycle',{'a.flow':'module a\nuse "@rf2/v1/b.flow"\n','b.flow':'module b\nuse "@rf2/v1/a.flow"\n'})
missing=D/'missing-sdk';missing.mkdir()
symlink_manifest=custom('symlink-manifest',{'shared.flow':base});(symlink_manifest/'real.manifest').write_bytes((symlink_manifest/'rf2-sdk.manifest').read_bytes());(symlink_manifest/'rf2-sdk.manifest').unlink();(symlink_manifest/'rf2-sdk.manifest').symlink_to('real.manifest')
symlink_module=custom('symlink-module',{'shared.flow':base});(symlink_module/'other.flow').write_text(base);(symlink_module/'shared.flow').unlink();(symlink_module/'shared.flow').symlink_to('other.flow')
fifo_manifest=D/'fifo-manifest';fifo_manifest.mkdir();os.mkfifo(fifo_manifest/'rf2-sdk.manifest')
directory_manifest=D/'directory-manifest';directory_manifest.mkdir();(directory_manifest/'rf2-sdk.manifest').mkdir()
fifo_module=custom('fifo-module',{'shared.flow':base});(fifo_module/'shared.flow').unlink();os.mkfifo(fifo_module/'shared.flow')
directory_module=custom('directory-module',{'shared.flow':base});(directory_module/'shared.flow').unlink();(directory_module/'shared.flow').mkdir()
diagnostic=custom('diagnostic-sdk',{'bad.flow':'module bad\nfn broken()\n return missing_value\nend\n'})
overlap='''profile RF2_SYSTEM_A64_V1
use "@rf2/v1/text.flow"
fn main(argc,argv)
 let prefix=TextPrefix()
 let found=TextMatches(17,18,19,20)
 let raw=buffer("search_input",1048576)
 let i=0
 while i<1048576
  do store8(raw+i,97)
  set i=i+1
 end
 if text_search("aaa",3,"aa",2,0,prefix,found)==0
  return 1
 end
 if found.count!=1
  return 2
 end
 if text_search_overlapping("aaa",3,"aa",2,0,prefix,found)==0
  return 3
 end
 if (found.count!=2)|(found.first!=0)|(found.last!=1)
  return 4
 end
 if text_search_overlapping("தமிழ் தமிழ்",31,"தமிழ்",15,0,prefix,found)==0
  return 5
 end
 if (found.count!=2)|(found.first!=0)|(found.last!=16)
  return 6
 end
 if text_search_overlapping(raw,1048576,"aa",2,0,prefix,found)==0
  return 7
 end
 if (found.count!=1048575)|(found.first!=0)|(found.last!=1048574)
  return 8
 end
 if text_search_overlapping(raw,1048576,raw,128,0,prefix,found)==0
  return 9
 end
 if (found.count!=1048449)|(found.first!=0)|(found.last!=1048448)
  return 10
 end
 set found.status=17
 set found.count=18
 set found.first=19
 set found.last=20
 set prefix[0]=71
 if text_search_overlapping(0,1048577,0,2,0,prefix,found)
  return 11
 end
 if text_search_overlapping(0,2,0,0,0,prefix,found)
  return 12
 end
 if text_search_overlapping(0,2,0,129,0,prefix,found)
  return 13
 end
 if text_search_overlapping(0,2,0,1,2,prefix,found)
  return 14
 end
 if (found.status!=17)|(found.count!=18)|(found.first!=19)|(found.last!=20)|(prefix[0]!=71)
  return 15
 end
 if load8(raw)!=97
  return 16
 end
 return 0
end
'''
for mode in ('plain','opt'):
    run(compile_at('text-app',text,mode))
    run(compile_at('collection-app',collection,mode))
    run(compile_at('overlapping-search',overlap,mode))
    run(compile_at('simple',entry,mode,sdk=simple))
    run(compile_at('deduplicated',entry.replace('fn main','use "@rf2/v1/shared.flow"\nfn main'),mode,sdk=simple))
    run(compile_at('local-unchanged',entry.replace('@rf2/v1/shared.flow','local.flow'),mode,sdk=None,files={'local.flow':base}))
    for name,sdk,needle in [('bad-digest',bad_digest,'SHA256 mismatch'),('unlisted',unlisted,'not listed'),('wrong-version',wrong_version,'manifest version'),('duplicate',duplicate,'duplicate SDK manifest path'),('traversal',traversal,'local identifier segments'),('missing',missing,'manifest open failed'),('symlink-manifest',symlink_manifest,'manifest open failed'),('symlink-module',symlink_module,'module open failed'),('uppercase-digest',bad_hex,'lowercase hex'),('missing-final-lf',no_lf,'final newline'),('manifest-too-big',too_big,'manifest size bound'),('manifest-33-entries',entries33,'manifest entry bound'),('fifo-manifest',fifo_manifest,'must be a regular file'),('directory-manifest',directory_manifest,'must be a regular file'),('fifo-module',fifo_module,'must be a regular file'),('directory-module',directory_module,'must be a regular file')]:
        compile_at(name,entry,mode,sdk=sdk,expected=needle)
    count_entry='profile RF2_SYSTEM_A64_V1\n'+''.join('use "@rf2/v1/file'+str(i)+'.flow"\n' for i in range(31))+'fn main(argc,argv)\n return 0\nend\n'
    run(compile_at('32-source-files',count_entry,mode,sdk=entries32))
    compile_at('33-source-files',count_entry.replace('fn main','use "@rf2/v1/file31.flow"\nfn main'),mode,sdk=entries32,expected='module count bound')
    compile_at('no-root',entry,mode,sdk=None,expected='requires --sdk-root')
    compile_at('relative-root',entry,mode,sdk=Path('relative'),expected='explicit absolute')
    compile_at('root-path-bound',entry,mode,sdk=Path('/'+'a'*767),expected='SDK root path bound')
    compile_at('wrong-import-version',entry.replace('@rf2/v1/','@rf2/v2/'),mode,sdk=simple,expected='SDK import version')
    compile_at('import-traversal',entry.replace('shared.flow','../shared.flow'),mode,sdk=simple,expected='local identifier segments')
    compile_at('duplicate-root',entry,mode,sdk=simple,extra=['--sdk-root',str(simple)],expected='duplicate SDK root')
    compile_at('cycle',entry.replace('shared.flow','a.flow'),mode,sdk=cycle,expected='module import cycle')
    compile_at('local-shadow',entry.replace('fn main','use "local.flow"\nfn main'),mode,sdk=simple,files={'local.flow':base},expected='duplicate function')
    no_fallback=entry.replace('shared.flow','absent.flow')
    compile_at('no-fallback',no_fallback,mode,sdk=simple,files={'absent.flow':base},expected='module open failed')
    compile_at('diagnostic',entry.replace('shared.flow','bad.flow'),mode,sdk=diagnostic,expected=str(diagnostic/'bad.flow'))
    # A package root is explicit even for a check-only compile, with no output.
    w=D/('check-'+mode);w.mkdir();p=w/'main.flow';p.write_text(entry)
    q=subprocess.run([str(C),'--check',str(p),'--sdk-root',str(simple)],capture_output=True,timeout=30)
    record('check-only SDK '+mode,q.returncode==0,q.stderr.decode(errors='replace'))
    # Warm function reuse must include actual imported package bytes, not just paths.
    mutable=custom('mutable-'+mode,{'shared.flow':base});cache=D/('cache-'+mode);cache.mkdir(mode=0o700)
    out=compile_at('cache-initial',entry,mode,sdk=mutable,extra=['--reuse-pack',str(cache)]);run(out)
    changed=base.replace('return 7','return 9');(mutable/'shared.flow').write_text(changed)
    (mutable/'rf2-sdk.manifest').write_text('rf2-sdk-v1\n'+sha(mutable/'shared.flow')+' shared.flow\n')
    # Keep the application source unchanged: only the package bytes/manifest vary.
    out=compile_at('cache-changed',entry,mode,sdk=mutable,extra=['--reuse-pack',str(cache)]);run(out,expected=2)
    clean=compile_at('cache-clean',entry,mode,sdk=mutable)
    record('changed SDK matches clean '+mode,out.read_bytes()==clean.read_bytes())
result=json.loads((D/'RESULTS.json').read_text());result['sdkManifestSHA256']=sha(SDK/'rf2-sdk.manifest');result['sharedSDK']=str(SDK);result['count']=len(rows);(D/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(directory=str(D),checks=len(rows),allPassed=result['allPassed'])))
