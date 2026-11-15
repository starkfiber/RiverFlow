"""Replay the public 0.47 app after five mechanical field-try simplifications."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys,tarfile
R=Path(__file__).resolve().parents[2]
def study_snapshot(destination):
    archive=R/'docs/evidence/APP-EFFORT-0.47-SOURCES.tar.gz'
    assert hashlib.sha256(archive.read_bytes()).hexdigest()=='af5b956e72352a8d1edbeb4af9f0c14aa0f0b54f5d0a6786840caffd9e58ddd1'
    destination=Path(destination);destination.mkdir(parents=True)
    prefix='rf2-app-effort-0.47/v3/attempts/3-newRF2/'
    with tarfile.open(archive)as bundle:
        for member in bundle.getmembers():
            if member.name.startswith(prefix):
                relative=Path(member.name[len(prefix):])
                if not member.isfile()or '..'in relative.parts or relative.is_absolute():raise ValueError(member.name)
                if relative.parts[0]=='lib'or str(relative)in('main.flow','README.md'):
                    out=destination/relative;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(bundle.extractfile(member).read())
        grader=bundle.extractfile('rf2-app-effort-0.47/v3/grade.py').read()
    return grader
def main():
    if len(sys.argv)!=4:raise SystemExit('replay.py COMPILER DRIVER NEW-DIRECTORY')
    compiler,driver=map(lambda p:Path(p).resolve(),sys.argv[1:3]);d=Path(sys.argv[3]).resolve()
    if d.exists():raise SystemExit('Use a new directory')
    grader=study_snapshot(d);s=(d/'main.flow').read_text();original=s
    pattern=r'(?m)^( *)let (parsed_value\d+)=try ([^\n]+)\n\1set (req\.[A-Za-z_]+)=\2$'
    assert len(re.findall(pattern,s))==5
    s=re.sub(pattern,lambda m:m[1]+'set '+m[4]+'=try '+m[3],s)
    (d/'main.flow').write_text(s);(d/'launch.json').write_text('["./app"]\n');(d/'grade.py').write_bytes(grader)
    build=d/'native';build.mkdir(mode=0o700)
    q=subprocess.run([str(driver),str(compiler),str(d/'main.flow'),str(build)],capture_output=True,timeout=60)
    (d/'BUILD.log').write_bytes(q.stdout+q.stderr);q.check_returncode();shutil.copy2(build/'program',d/'app')
    q=subprocess.run([sys.executable,str(d/'grade.py'),str(d),str(d/'GRADE.json')],capture_output=True,timeout=120)
    (d/'GRADE.log').write_bytes(q.stdout+q.stderr)
    receipt=dict(originalSourceSHA256=hashlib.sha256(original.encode()).hexdigest(),candidateSourceSHA256=hashlib.sha256(s.encode()).hexdigest(),compilerSHA256=hashlib.sha256(compiler.read_bytes()).hexdigest(),driverSHA256=hashlib.sha256(driver.read_bytes()).hexdigest(),removedTemporaryPairs=5,originalBytes=len(original.encode()),candidateBytes=len(s.encode()),grade=json.loads((d/'GRADE.json').read_text()),scope='Mechanical parent edit and fresh acceptance replay. No new autonomous authoring, model-usage or runtime-speed result.')
    (d/'RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(d),grade=receipt['grade']['passed'],checks=receipt['grade']['checks'])))
    assert receipt['grade']['allPassed']
if __name__=='__main__':main()
