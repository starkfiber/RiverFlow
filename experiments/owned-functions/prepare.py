"""Prepare cross-function owned-result candidate from the fixed 0.42 source."""
from pathlib import Path
import hashlib,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[2]
if len(sys.argv)!=2:raise SystemExit('Usage: prepare.py NEW-DIRECTORY')
D=Path(sys.argv[1]).resolve()
if D.exists():raise SystemExit('Use a new output directory')
with tempfile.TemporaryDirectory(prefix='rf2-owned-functions-')as temporary:
 p=Path(temporary)/'base';subprocess.run([sys.executable,str(R/'experiments/owned-values/prepare.py'),p],cwd=R,check=True,capture_output=True);s=(p/'compiler.flow').read_text()
if hashlib.sha256(s.encode()).hexdigest()!='6b4b79ff4308ab6ecbcc8ee0bbef2637eee2437fc5f89214151df6a8a9796b22':raise ValueError('Review changed 0.42 base')
def replace(old,new):
 global s
 if s.count(old)!=1:raise ValueError(('patch drift',old[:100],s.count(old)))
 s=s.replace(old,new,1)
old='''  set field = advance()
  if tmatch(field, "u64") == 0
   set field = record_index(field)
   do require(field != 0, "unknown result payload type")
   do require(load64(record_info(field) + 144) == 0, "result payload requires scalar record")
   do require(load64(record_info(field) + 8) <= 4, "result record payload field bound")
   do require(record_nested(field)==0,"borrowed nested record cannot escape in result")
   do store64(r + 152, field)
  end'''
new='''  set field = advance()
  let owns_payload=tmatch(field,"own")
  if owns_payload
   set field=record_index(advance())
   do require(owned_kind(field),"owned result requires owned nominal type")
   do store64(r+152,field)
  else
  if tmatch(field, "u64") == 0
   set field = record_index(field)
   do require(field != 0, "unknown result payload type")
   do require(load64(record_info(field) + 144) == 0, "result payload requires scalar record")
   do require(load64(record_info(field) + 8) <= 4, "result record payload field bound")
   do require(record_nested(field)==0,"borrowed nested record cannot escape in result")
   do store64(r + 152, field)
  end
  end'''
replace(old,new)
replace(' do store64(ftable(f) + 16, load64(state() + 24))\n do store64(function_leaf(f), 1)',''' do store64(ftable(f) + 16, load64(state() + 24))
 if owned_payload(load64(function_result(f)))
  do store64(owner_result_slot(f),load64(ftable(f)+32)+1)
  do store64(ftable(f)+32,load64(ftable(f)+32)+1)
 end
 do store64(function_leaf(f), 1)''')
replace('  if match("ok") | match("err")\n   set slot = add_local(f, i + 1)','''  if match("ok")&tmatch(i+1,"own")
   do require(tmatch(i+3,":"),"owned result requires annotation")
   set id=record_index(i+4)
   do require(owned_kind(id),"owned result binding type required")
   set slot=add_local(f,i+2)
   do owned_slot_register(f,slot,id)
  else
  if match("ok") | match("err")
   set slot = add_local(f, i + 1)''')
replace('  if match("defer")\n   do require(depth == 1','  end\n  if match("defer")\n   do require(depth == 1')
replace('do require(load64(function_result(f)) == load64(record_info(id) + 152), "owner function result type mismatch")','do require(owner_error_compatible(f,id), "owner function result type mismatch")')
replace('fn handle_result(depth)','fn handle_plain_result(depth)')
replace(' let payload = load64(record_info(id) + 152)\n if (tag == 0) & (payload != 0)',''' let payload = load64(record_info(id) + 152)
 if (tag==0)&owned_kind(payload)
  do return_owned_value(payload)
  do expect(")")
  return imm(0,0)
 end
 if (tag == 0) & (payload != 0)''')
replace('   set regs = load64(record_info(result) + 8) + 1','''   if owned_kind(result)==0
    set regs = load64(record_info(result) + 8) + 1
   end''')
replace(' set f = function_index(name)\n do require(count == load64(ftable(f) + 8), "function arity")\n do fix(1, load64(ftable(f) + 40))',''' set f = function_index(name)
 do require(count == load64(ftable(f) + 8), "function arity")
 if owned_payload(load64(function_result(f)))
  do require(load64(owned_context())==name+1,"owned call requires explicit owned result handler")
  do require(owned_payload(load64(function_result(f)))==load64(owned_context()+16),"owned call result type mismatch")
  do local_pointer(8,load64(owned_context()+8))
 end
 do fix(1, load64(ftable(f) + 40))''')
replace('  do store64(state() + 88, next_label())\n  do require(block(0)', '''  if load64(owner_result_slot(f))
   do access_local(8,load64(owner_result_slot(f))-1,1)
  end
  do store64(state() + 88, next_label())
  do require(block(0)''')
replace('    return j\n   end\n  end\n  set j = j + 1\n end\n do die("unknown local")','''    if (j<load64(ftable(f)+8))&(load64(owned_parameter(f,j))!=0)
     return load64(owned_parameter(f,j))-1
    end
    return j
   end
  end
  set j = j + 1
 end
 do die("unknown local")''')
replace('    set t = add_local(f, advance())\n    do store64(local_ready(f, t), 1)','''    let owning_parameter=match("own")
    if owning_parameter
     do advance()
    end
    set t = add_local(f, advance())
    do store64(owned_parameter(f,t),owning_parameter)
    do require((owning_parameter==0)|match(":"),"owned parameter requires nominal annotation")
    do store64(local_ready(f, t), 1)''')
replace('      do require((load64(record_info(other) + 144) < 3)|((load64(record_info(other)+144)==11)|(load64(record_info(other)+144)==13)), "result/view parameters unsupported")','''      if owning_parameter
       do require(owned_kind(other),"owned parameter requires owned type")
      else
       do require((load64(record_info(other) + 144) < 3)|((load64(record_info(other)+144)==11)|(load64(record_info(other)+144)==13)), "result/view parameters unsupported")
      end''')
replace('    set params = params + 1','''    do require((owning_parameter==0)|(load64(local_type(f,t))!=0),"owned parameter cannot be scalar")
    set params = params + 1''')
replace(' do store64(ftable(f) + 16, load64(state() + 24))\n if owned_payload', ' do store64(ftable(f) + 16, load64(state() + 24))\n do owned_parameters_prepare(f,params)\n if owned_payload')
replace('  do expression(1, depth + 1)\n  if callee == 0','''  if callee!=0
   do require(count<load64(ftable(callee-1)+8),"function arity")
  end
  if (callee!=0)&(load64(owned_parameter(callee-1,count))!=0)
   do owned_argument(callee-1,count)
  else
   do expression(1, depth + 1)
  end
  if callee == 0''')
replace('  do store64(state() + 88, next_label())\n  do require(block(0)', '  do owned_parameters_receive(f)\n  do store64(state() + 88, next_label())\n  do require(block(0)')
s+='\n'+(R/'experiments/owned-functions/compiler-extension.flow').read_text();D.mkdir(parents=True)
with(D/'compiler.flow').open('x')as out:out.write(s)
print(hashlib.sha256(s.encode()).hexdigest())
