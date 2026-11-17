"""Source-bound diagnostic refinement; does not alter syntax or emitted app code."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[3]
BASE='5ec6f9f43d1f76e838cb4485f7f6b60dcc0319c8d381e15541a4f14552b76c82'
GUARDED='607cbca37a8965ee9fb0a4a0fb40222ccc9aefc7a8bc90e34f5df29d25af4dbe'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare(source,destination):
    assert sha(source)==BASE,'Explicit qualified 0.50 source required'
    assert not destination.exists(),'Preserve previous evidence'
    spec=importlib.util.spec_from_file_location('reviewed_guard',ROOT/'experiments/intelligence/prepare.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    text=source.read_text();start=text.index('fn module_load(');end=text.index('fn module_append(',start);section=text[start:end];assert section.count(guard.OLD)==1
    text=text[:start]+section.replace(guard.OLD,guard.NEW,1)+text[end:];assert hashlib.sha256(text.encode()).hexdigest()==GUARDED
    def change(old,new):
        nonlocal text
        assert text.count(old)==1,old[:60]
        text=text.replace(old,new,1)
    change('fn diagnostic_category(text)\n','''fn diagnostic_category(text)
 # Inspect tokens only during parser diagnostics, within the token table.
 # These hints identify actual observed invalid spellings, not automatic repairs.
 if load64(buffer("diagnostic_state",64))==2
  let current=load64(state()+24)
  if current<load64(state()+16)
   if load64(token(current))==1
    if same(text,length(text),"unsupported statement",21)
     if tmatch(current,"try")
      return 9
     end
    end
    if current>0
     if same(text,length(text),"expected newline",16)
      if tmatch(current,"if")
       if load64(token(current-1))==1
        if tmatch(current-1,"else")
         return 10
        end
       end
      end
     end
    end
   end
  end
 end
''')
    change('fn diagnostic_code(category)\n','''fn diagnostic_code(category)
 if category==9
  return "RF2E_TRY_STATEMENT"
 end
 if category==10
  return "RF2E_ELSE_IF"
 end
''')
    change('fn diagnostic_hint(category)\n','''fn diagnostic_hint(category)
 if category==9
  return "A bare try is not a statement. In an IO function use do try call(...) when discarding success, or let value=try call(...). Outside IO use handle with ok/err branches."
 end
 if category==10
  return "else requires a newline. Put a nested if on the following line and close both blocks with end. The spelling else if on one line is not supported."
 end
''')
    destination.mkdir(parents=True);out=destination/'compiler.flow';out.write_text(text)
    (destination/'SOURCE.json').write_text(json.dumps({'schema':'rf2.diagnostic-refinement.v1','baselineSourceSHA256':BASE,'guardedBaselineSHA256':GUARDED,'candidateSourceSHA256':sha(out),'preparerSHA256':sha(__file__),'scope':'Two context-specific hints/categories only; grammar and success lowering unchanged','stableChanged':False},indent=2)+'\n');return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(prepare(a.source,a.out))
