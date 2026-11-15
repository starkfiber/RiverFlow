"""Build an isolated native compiler source; Python is development tooling only."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
if len(sys.argv)!=2:
    raise SystemExit('Usage: prepare.py NEW-DIRECTORY (isolated development compiler source)')
DEST=Path(sys.argv[1]).resolve()
if DEST.exists():
    raise SystemExit('Use a new output directory; existing evidence is never overwritten')
with tempfile.TemporaryDirectory(prefix='rf2-owned-prepare-') as temporary:
    seed=Path(temporary)/'borrowed'
    subprocess.run([sys.executable,str(ROOT/'experiments/nested-records/prepare.py'),str(seed)],cwd=ROOT,check=True)
    s=(seed/'compiler.flow').read_text()

def replace(old,new):
    global s
    if s.count(old)!=1:
        raise ValueError(('compiler patch drift',old[:120],s.count(old)))
    s=s.replace(old,new,1)

replace(' let is_collection = match("collection")',' let is_collection = match("collection")\n let is_owned_text = match("text")')
replace(' if is_vector | is_collection\n',' if is_vector | is_collection | is_owned_text\n')
replace('1048576-is_collection*983040','1048576-(is_collection|is_owned_text)*983040')
replace('7+is_collection*4','7+is_collection*4+is_owned_text*6')
replace('match("vector") | match("collection")\n    do scan_record()', 'match("vector") | match("collection") | match("text")\n    do scan_record()')
replace('  if match("u64")\n   do advance()\n  else\n   let child=record_index(advance())\n   do require((child!=0)&(child<id),"nested record requires earlier type")\n   do require(load64(record_info(child)+144)==0,"nested field requires plain borrowed record")\n   do store64(field_type(id,n),child)\n  end', '''  if match("u64")
   do advance()
  else
   let owning=match("own")
   if owning
    do advance()
   end
   let child=record_index(advance())
   do require((child!=0)&(child<id),"nested record requires earlier type")
   if owning
    do require((load64(record_info(child)+144)==11)|(load64(record_info(child)+144)==13),"owned field requires collection or text")
    do store64(r+144,12)
   else
    do require(load64(record_info(child)+144)==0,"nested field requires plain borrowed record")
   end
   do store64(field_type(id,n),child)
  end''')
replace(' do require(n > 0, "empty record")\n do store64(r + 8, n)', ''' do require(n > 0, "empty record")
 if load64(r+144)==12
  let x=0
  while x<n
   let owned_child=load64(field_type(id,x))
   if owned_child
    do require((load64(record_info(owned_child)+144)==11)|(load64(record_info(owned_child)+144)==13),"owned aggregate cannot contain borrowed fields")
    do require((load64(record_info(owned_child)+152)==load64(r+152))|(load64(r+152)==0),"aggregate result types differ")
    do store64(r+152,load64(record_info(owned_child)+152))
   end
   set x=x+1
  end
 end
 do store64(r + 8, n)''')
# Plain borrowed nesting continues to be forbidden as a result payload.
# Owned aggregate kind12 already fails the existing scalar-record result rule.
replace('(load64(record_info(other)+144)==11), "result/view parameters unsupported")','((load64(record_info(other)+144)==11)|(load64(record_info(other)+144)==13)), "result/view parameters unsupported")')
replace('do require((id!=0)&(load64(record_info(id)+144)==11),"move requires collection owner")','do require((id!=0)&((load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==12)|(load64(record_info(id)+144)==13)),"move requires collection, text or aggregate owner")')
replace('if (load64(record_info(id) + 144) == 7)|(load64(record_info(id)+144)==11)\n     set count = 4+(load64(record_info(id)+144)==11)*2\n    end','''if (load64(record_info(id) + 144) == 7)|(load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==13)
     set count = 4+((load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==13))*2
    end
    if load64(record_info(id)+144)==12
     set count=aggregate_slots(id)
    end''')
replace('do require(match("own") & tmatch(i+4,"(") & tmatch(i+6,")"),"move requires own target and one local")','do require(match("own") & tmatch(i+4,"("),"move requires own target")')
replace('    set id = load64(local_type(f,source_slot))\n    do require((id!=0)','''    set id = load64(local_type(f,source_slot))
    if tmatch(i+6,".")
     do require(tmatch(i+8,")"),"move requires one owner or owned field")
     do require((id!=0)&(load64(record_info(id)+144)==12),"move field requires aggregate")
     let moved_field=field_index(id,i+7)
     set id=load64(field_type(id,moved_field))
    else
     do require(tmatch(i+6,")"),"move requires one local or owned field")
    end
    do require((id!=0)''')

# Both scan and generation ownership admission sites.
old='(load64(record_info(id)+144)==11), "own requires resource type")'
replace(old,'((load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==12)|(load64(record_info(id)+144)==13)), "own requires resource type")')
replace('    set count = load64(cleanup_count(f))\n    do require(count < 16, "resource cleanup count bound")','''    if load64(record_info(id)+144)==12
     do aggregate_register(f,slot,id)
    else
    set count = load64(cleanup_count(f))
    do require(count < 16, "resource cleanup count bound")''')
replace('do store64(cleanup_owned(f, count), load64(record_info(id) + 144) - 5)','do store64(cleanup_owned(f, count), load64(record_info(id) + 144) - 5-(load64(record_info(id)+144)==13)*2)')
replace('    do store64(cleanup_count(f), count + 1)\n   end\n  end\n  do advance()','    do store64(cleanup_count(f), count + 1)\n    end\n   end\n  end\n  do advance()')
replace('(load64(record_info(id)+144)==11), "resource type required")','((load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==12)|(load64(record_info(id)+144)==13)), "resource type required")')
replace(' if load64(record_info(id)+144)==11\n  return construct_collection(f,slot,id)\n end',''' if load64(record_info(id)+144)==12
  return aggregate_construct(f,slot,id)
 end
 if (load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==13)
  return construct_collection(f,slot,id)
 end''')
replace(' let slot = local_index(advance())\n let id = load64(local_type(f, slot))\n do require(id != 0, "owned resource required")\n if load64(record_info(id)+144)==11',' let slot = owned_field_local(f)\n let id = load64(local_type(f, slot))\n do require(id != 0, "owned resource required")\n if (load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==13)')
replace('fn construct_collection(f,slot,id)\n let i = 0','fn construct_collection(f,slot,id)\n do collection_construct_value(f,slot,id)\n return newline()\nend\nfn collection_construct_value(f,slot,id)\n let i = 0')
replace('  let source = local_index(advance())\n  do require(source>=load64(ftable(f)+8),"borrowed collection cannot be moved")','  let source = owned_field_local(f)\n  do require(source>=load64(ftable(f)+8),"borrowed collection cannot be moved")')
replace(' do store64(state()+224,load64(state()+224)+1)\n return newline()\nend\nfn collection_property',' do store64(state()+224,load64(state()+224)+1)\n return 0\nend\nfn collection_property')
replace(' let slot = local_index(advance())\n let id = load64(local_type(f,slot))\n do require((id!=0)&(load64(record_info(id)+144)==11),"collection owner required")',''' let slot = owned_field_local(f)
 let id = load64(local_type(f,slot))
 let text_op=tmatch(name,"text_append")|tmatch(name,"text_get")|tmatch(name,"text_clear")|tmatch(name,"text_reserve")
 do require((id!=0)&(load64(record_info(id)+144)==11+text_op*2),"nominal collection or text owner required")''')
replace('  if tmatch(name,"collection_push")','  if tmatch(name,"collection_push")|tmatch(name,"text_append")')
replace('   if tmatch(name,"collection_get")','   if tmatch(name,"collection_get")|tmatch(name,"text_get")')
replace('     if tmatch(name,"collection_clear")','     if tmatch(name,"collection_clear")|tmatch(name,"text_clear")')
replace('      do require(tmatch(name,"collection_reserve"),"unknown collection operation")','      do require(tmatch(name,"collection_reserve")|tmatch(name,"text_reserve"),"unknown collection operation")')
replace(' return tmatch(t,"collection_reserve")|tmatch(t,"collection_push")|tmatch(t,"collection_get")|tmatch(t,"collection_set")|tmatch(t,"collection_clear")',' return tmatch(t,"collection_reserve")|tmatch(t,"collection_push")|tmatch(t,"collection_get")|tmatch(t,"collection_set")|tmatch(t,"collection_clear")|tmatch(t,"text_append")|tmatch(t,"text_get")|tmatch(t,"text_clear")|tmatch(t,"text_reserve")')
replace('  if tmatch(i,"collection")&(load64(token(i))==1)','  if (tmatch(i,"collection")|tmatch(i,"text"))&(load64(token(i))==1)')
# Text scalar admission occurs after all arguments finish, before heap mutation.
replace(' do imm(1,operation)\n do imm(4,load64(record_info(id)+8))\n do collection_call()', ''' let done=next_label()
 if (load64(record_info(id)+144)==13)&(operation==1)
  let invalid=next_label()
  let admitted=next_label()
  do imm(4,1114111)
  do emit(3942645791 | (4<<16) | (2<<5))
  do jump(invalid,8)
  do imm(4,55296)
  do emit(3942645791 | (4<<16) | (2<<5))
  do jump(admitted,3)
  do imm(4,57343)
  do emit(3942645791 | (4<<16) | (2<<5))
  do jump(admitted,8)
  do label(invalid)
  do imm(0,1)
  do imm(1,22)
  do jump(done,16)
  do label(admitted)
 end
 do imm(1,operation)
 do imm(4,load64(record_info(id)+8))
 do collection_call()
 do label(done)''')
# Preserve owners as typed references only where the existing heap interface permits.
replace('((load64(record_info(id) + 144) < 8)|(load64(record_info(id)+144)==11)), "owner cannot be used as a value")','((load64(record_info(id) + 144) < 8)|(load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==12)|(load64(record_info(id)+144)==13)), "owner cannot be used as a value")')
replace('      do access_local(0, slot, 0)\n      do store64(state() + 136, id)','''      if id!=0
       if load64(record_info(id)+144)==12
        do require(match("."),"aggregate is not a value; use own move")
        do aggregate_guard(load64(state()+32),slot)
       end
      end
      do access_local(0, slot, 0)
      do store64(state() + 136, id)''')
replace('   if load64(record_info(id) + 144)\n    if load64(record_info(id)+144)==11','   if (load64(record_info(id) + 144)!=0)&(load64(record_info(id)+144)!=12)\n    if (load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==13)')
replace('    set slot = field_index(id, advance())\n    set next_type=load64(field_type(id,slot))','''    let owner_root=slot
    set slot = field_index(id, advance())
    set next_type=load64(field_type(id,slot))
    if (load64(record_info(id)+144)==12)&(next_type!=0)
     do require(load64(local_ready(load64(state()+32),aggregate_field_slot(owner_root,id,slot))),"owned field was moved")
    end''')

# Plain fields continue through the borrowed-record field table for aggregate slots.
replace('do require(load64(record_info(id) + 144) == 0, "field assignment requires record")','do require((load64(record_info(id) + 144) == 0)|(load64(record_info(id)+144)==12), "field assignment requires record")')
replace('     do access_local(0,target,0)\n     do advance()','''     if load64(record_info(id)+144)==12
      do aggregate_guard(load64(state()+32),target)
     end
     do access_local(0,target,0)
     do advance()''')
# Owned-field paths through ordinary record assignment must never rewrite descriptors.
replace('      do require(id!=0,"nested path traverses a scalar")','      do require((id!=0)&(load64(record_info(id)+144)==0),"nested path requires plain borrowed record")')
s+='\n'+(ROOT/'experiments/owned-values/compiler-extension.flow').read_text()
DEST.mkdir(parents=True)
with (DEST/'compiler.flow').open('x') as output:
    output.write(s)
print(hashlib.sha256(s.encode()).hexdigest())
