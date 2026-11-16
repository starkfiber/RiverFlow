"""Layer native diagnostics and explicitly inventoried 512-function tables."""
from pathlib import Path
import hashlib,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[2]

# Explicit inventory: these buffers index by function, not by local/type/token.
FUNCTION_BUFFERS={
 'functions':12288,'locals':524288,'local_scope':524288,'local_binding':524288,
 'function_result':2048,'local_types':524288,'local_ready':524288,
 'array_arena_sizes':2048,'array_payload_offsets':524288,'function_leaf':2048,
 'cleanup_count':2048,'cleanup_slots':32768,'cleanup_owned':32768,'cleanup_spans':32768,
 'function_code_ranges':4096,'reuse_units':32768,'owned_result_slots':2048,
 'owned_parameters':16384,
}
def apply_bounds(source):
    import re
    old='do require(i < 256, "function bound")'
    assert source.count(old)==1
    source=source.replace(old,'do require(i < 512, "function bound")',1)
    for name,size in FUNCTION_BUFFERS.items():
        pattern=r'(buffer\("'+re.escape(name)+r'",\s*)'+str(size)+r'(\))'
        source,n=re.subn(pattern,lambda m:m[1]+str(size*2)+m[2],source)
        assert n==1,(name,n)
    return source

def apply(source):
    def change(old,new):
        nonlocal source
        assert source.count(old)==1,(old[:100],source.count(old))
        source=source.replace(old,new,1)
    change('fn die(text)\n do write(2, text, length(text))', '''fn die(text)
 if load64(buffer("diagnostic_options",8))
  do diagnostic_json_error(text)
  do exit(1)
  return 0
 end
 do write(2, text, length(text))''')
    change(' do diagnostic_position()\n do exit(1)', ''' do diagnostic_position()
 let category=diagnostic_category(text)
 let hint=diagnostic_hint(category)
 if length(hint)
  do write(2,"hint: ",6)
  do write(2,hint,length(hint))
  do write(2,"\\n",1)
 end
 do exit(1)''')
    change('fn main(argc, argv)\n let src = 0', '''fn main(argc, argv)
 # Select output before argument validation, including malformed option failures.
 let diagnostic_option=1
 while diagnostic_option<argc
  let diagnostic_text=load64(argv+diagnostic_option*8)
  if same(diagnostic_text,length(diagnostic_text),"--diagnostic-json",17)
   do store64(buffer("diagnostic_options",8),1)
  end
  set diagnostic_option=diagnostic_option+1
 end
 let src = 0''')
    # The package layer independently extends --check to accept explicit roots.
    old='do require(argc==3,"check requires exactly one source path and no options")'
    if old in source:
        change(old,'''if argc!=3
    do require(argc==4,"check requires one source path and optional --diagnostic-json")
    do require(same(load64(argv+24),length(load64(argv+24)),"--diagnostic-json",17),"check requires one source path and optional --diagnostic-json")
   end''')
    change('    do require(same(text,length(text),"--compact",9),"unknown compiler option")', '''    if same(text,length(text),"--diagnostic-json",17)
     do require(load64(buffer("diagnostic_seen",8))==0,"duplicate compiler option")
     do store64(buffer("diagnostic_seen",8),1)
    else
    do require(same(text,length(text),"--compact",9),"unknown compiler option")''')
    change('    do store64(image_options(),1)\n   end', '    do store64(image_options(),1)\n    end\n   end')
    if 'fn module_diagnostic_root(' not in source:
        source+='\nfn module_diagnostic_root(index)\n return buffer("module_root",1024)\nend\n'
    if 'fn module_diagnostic_path(' not in source:
        source+='\nfn module_diagnostic_path(index)\n return module_path(index)\nend\n'
    source+='\n'+(R/'experiments/diagnostics-050/diagnostics.flow').read_text()
    return source

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: prepare.py NEW-DIRECTORY')
    out=Path(sys.argv[1]).resolve()
    if out.exists():raise SystemExit('Use a new directory')
    with tempfile.TemporaryDirectory(prefix='rf2-diagnostics-base-')as temporary:
        base=Path(temporary)/'base'
        subprocess.run([sys.executable,str(R/'experiments/typed-requests/prepare.py'),str(base)],check=True,capture_output=True)
        source=apply(apply_bounds((base/'compiler.flow').read_text()))
    out.mkdir(parents=True);(out/'compiler.flow').write_text(source)
    print(hashlib.sha256(source.encode()).hexdigest())
