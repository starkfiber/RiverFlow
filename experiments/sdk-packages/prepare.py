"""Add explicit source SDK roots to the corrected 0.49 native compiler."""
from pathlib import Path
import hashlib, subprocess, sys, tempfile

R = Path(__file__).resolve().parents[2]

def apply(source):
    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, (old[:100], source.count(old))
        source = source.replace(old, new, 1)

    replace('fn module_load(name, n)\n do module_path_check(name, n)',
            'fn module_load(name, n)\n let from_sdk=sdk_import(name,n)')
    replace(' set path = module_path(count)\n do cp(path, name, n)',
            ' do require(count<32,"module count bound")\n set path = module_path(count)\n do cp(path, name, n)')
    replace(' let full = buffer("module_full_path", 1024)\n do require(root + n < 1024, "module full path bound")\n do cp(full, buffer("module_root", 1024), root)\n do cp(full + root, name, n)\n do store8(full + root + n, 0)',
            ' let full = buffer("module_full_path", 1024)\n let relative=name\n let relative_n=n\n let base=buffer("module_root",1024)\n if from_sdk\n  set root=load64(sdk_state())\n  set base=sdk_root()\n  set relative=name+8\n  set relative_n=n-8\n end\n do store64(buffer("module_sdk_kind",256)+count*8,from_sdk)\n do require(root + relative_n < 1024, "module full path bound")\n do cp(full, base, root)\n do cp(full + root, relative, relative_n)\n do store8(full + root + relative_n, 0)')
    replace('   do close(fd)\n   do store64(module_info(count), arena + start)',
            '   do close(fd)\n   if from_sdk\n    do sdk_verify(name+8,n-8,arena+start,used-start)\n   end\n   do store64(module_info(count), arena + start)')
    replace(' let fd = open(full, 256, 0)\n do require(fd < 9223372036854775808, "module open failed")',
            ' let flags=256\n if from_sdk\n  set flags=260\n end\n let fd = open(full, flags, 0)\n do require(fd < 9223372036854775808, "module open failed")\n if from_sdk\n  let metadata=buffer("sdk_module_stat",144)\n  let status=syscall6(339,fd,metadata,0,0,0,0)\n  if (status>>63)|((load32(metadata+4)&61440)!=32768)\n   do close(fd)\n   do die("SDK module must be a regular file")\n  end\n end')
    replace('   do require(argc==3,"check requires exactly one source path and no options")',
            '   do require(argc>=3,"check requires a source path")')
    replace('(argc<=8)', '(argc<=12)')
    replace(' let text = load64(argv+option*8)\n  if same(text,length(text),"--reuse-cache",13)',
            ' let text = load64(argv+option*8)\n  if same(text,length(text),"--sdk-root",10)\n   do require(option+1<argc,"SDK root option requires one absolute directory")\n   set option=option+1\n   do sdk_select(load64(argv+option*8))\n  else\n  if same(text,length(text),"--reuse-cache",13)')
    replace('  set option = option+1\n end\n set source_path = load64(argv+8)',
            '  end\n  set option = option+1\n end\n do sdk_initialize()\n set source_path = load64(argv+8)')
    replace(' do diagnostic_path(buffer("module_root",1024))\n do diagnostic_path(module_path(index))',
            ' do diagnostic_path(module_diagnostic_root(index))\n do diagnostic_path(module_diagnostic_path(index))')
    replace('[--reuse-cache directory | --reuse-pack directory]"',
            '[--reuse-cache directory | --reuse-pack directory] [--sdk-root absolute-directory]"')
    return source + '\n' + (R/'experiments/sdk-packages/sdk.flow').read_text()

def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: prepare.py NEW-DIRECTORY')
    destination=Path(sys.argv[1]).resolve()
    if destination.exists():
        raise SystemExit('Use a new directory')
    with tempfile.TemporaryDirectory(prefix='rf2-sdk-base-') as temporary:
        base=Path(temporary)/'base'
        subprocess.run([sys.executable,str(R/'experiments/typed-requests/prepare.py'),str(base)],check=True,capture_output=True)
        source=(base/'compiler.flow').read_text()
    assert hashlib.sha256(source.encode()).hexdigest()=='39f4944fa001397cf4977322d89f322316ee21f5105cbe3d75bdddd886820009'
    destination.mkdir(parents=True)
    (destination/'compiler.flow').write_text(apply(source))
    print(hashlib.sha256((destination/'compiler.flow').read_bytes()).hexdigest())

if __name__=='__main__':main()
