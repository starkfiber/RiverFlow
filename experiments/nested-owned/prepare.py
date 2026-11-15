"""Prepare recursive owned-record candidate atop the source-pinned 0.43 compiler."""
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[2]
if len(sys.argv)!=2:raise SystemExit('Usage: prepare.py NEW-DIRECTORY')
D=Path(sys.argv[1]).resolve()
if D.exists():raise SystemExit('Use a new output directory')
with tempfile.TemporaryDirectory(prefix='rf2-nested-owned-')as temporary:
 p=Path(temporary)/'base';subprocess.run([sys.executable,str(R/'experiments/owned-functions/prepare.py'),p],cwd=R,check=True,capture_output=True);s=(p/'compiler.flow').read_text()
if hashlib.sha256(s.encode()).hexdigest()!='0049834076477f08e6cf6da3b0696797b686fad07b9497fc798b829afdfd3d62':raise ValueError('Review changed 0.43 base')
def replace(old,new):
 global s
 if s.count(old)!=1:raise ValueError(('patch drift',old[:100],s.count(old)))
 s=s.replace(old,new,1)
# Types are declared in order, preventing recursive ownership cycles.
replace('do require((load64(record_info(child)+144)==11)|(load64(record_info(child)+144)==13),"owned field requires collection or text")','do require(owned_kind(child),"owned field requires collection or text or owned record")')
replace('do require((load64(record_info(owned_child)+144)==11)|(load64(record_info(owned_child)+144)==13),"owned aggregate cannot contain borrowed fields")','do require(owned_kind(owned_child),"owned aggregate cannot contain borrowed fields")')
old='''    if tmatch(i+6,".")
     do require(tmatch(i+8,")"),"move requires one owner or owned field")
     do require((id!=0)&(load64(record_info(id)+144)==12),"move field requires aggregate")
     let moved_field=field_index(id,i+7)
     set id=load64(field_type(id,moved_field))
    else
     do require(tmatch(i+6,")"),"move requires one local or owned field")
    end'''
replace(old,'''    let move_path=i+6
    while tmatch(move_path,".")
     do require((id!=0)&(load64(record_info(id)+144)==12),"move field requires aggregate")
     set id=load64(field_type(id,field_index(id,move_path+1)))
     set move_path=move_path+2
    end
    do require(tmatch(move_path,")"),"move requires one owner or owned field")''')
old='''      if id!=0
       if load64(record_info(id)+144)==12
        do require(match("."),"aggregate is not a value; use own move")
        do aggregate_guard(load64(state()+32),slot)
       end
      end
      do access_local(0, slot, 0)
      do store64(state() + 136, id)
      do store64(state() + 232, load64(local_binding(load64(state() + 32), slot)))'''
replace(old,'''      if nested_owned_kind(id)
       do nested_owned_expression(load64(state()+32),slot,id)
      else
       do access_local(0, slot, 0)
       do store64(state() + 136, id)
       do store64(state() + 232, load64(local_binding(load64(state() + 32), slot)))
      end''')
old='''     if load64(record_info(id)+144)==12
      do aggregate_guard(load64(state()+32),target)
     end
     do access_local(0,target,0)'''
replace(old,'''     if load64(record_info(id)+144)==12
      do nested_owned_assignment(load64(state()+32),target,id)
     else
     do access_local(0,target,0)''')
replace('     do emit(4177526816 | (field<<10))\n    else','     do emit(4177526816 | (field<<10))\n     end\n    else')
# These two owning admission sites also contain aggregate kind12 between heap kinds.
for message in ('own requires resource type','resource type required'):
 old='(load64(record_info(id)+144)==12)|(load64(record_info(id)+144)==13)), "'+message+'")'
 new='(load64(record_info(id)+144)==12)|(load64(record_info(id)+144)==13)|(load64(record_info(id)+144)==14)), "'+message+'")'
 replace(old,new)

# Structured rows use a distinct nominal collection kind. The heap remains bounded.
replace('  do expect(")")\n  return newline()\n end\n if is_resource','''  if is_collection&match(",")
   do advance()
   let row=record_index(advance())
   do require(row!=0,"record collection row type required")
   do require((load64(record_info(row)+144)==0)&(record_nested(row)==0),"record collection requires flat scalar row")
   do require(n<=65536//load64(record_info(row)+8),"record collection word bound")
   do store64(r+144,14)
   do store64(field_type(id,0),row)
  end
  do expect(")")
  return newline()
 end
 if is_resource''')
# Extend the exact heap-owner admission sites, preserving every other owner kind.
for var in ('id','other'):
 old='(load64(record_info('+var+')+144)==11)|(load64(record_info('+var+')+144)==13)'
 s=s.replace(old,'('+old+'|(load64(record_info('+var+')+144)==14))')
replace('return (kind==11)|(kind==12)|(kind==13)','return (kind==11)|(kind==12)|(kind==13)|(kind==14)')
replace('do require((id!=0)&((load64(record_info(id)+144)==11)|(load64(record_info(id)+144)==12)|(load64(record_info(id)+144)==13)),"move requires collection, text or aggregate owner")','do require(owned_kind(id),"move requires collection, text or aggregate owner")')
replace('load64(record_info(id) + 144) - 5-(load64(record_info(id)+144)==13)*2','load64(record_info(id) + 144) - 5-(load64(record_info(id)+144)==13)*2-(load64(record_info(id)+144)==14)*3')
replace('(load64(record_info(id)+144)==12)|(load64(record_info(id)+144)==13)), "owner cannot be used as a value")','(load64(record_info(id)+144)==12)|(load64(record_info(id)+144)==13)|(load64(record_info(id)+144)==14)), "owner cannot be used as a value")')
replace('fn heap_intrinsic(t)\n return ','fn heap_intrinsic(t)\n if records_intrinsic(t)\n  return 1\n end\n return ')
replace(' if heap_intrinsic(name)\n  return parse_collection(name,depth)',' if records_intrinsic(name)\n  return invoke_records(name,depth)\n end\n if heap_intrinsic(name)\n  return parse_collection(name,depth)')
replace(' let id = load64(local_type(f, slot))\n do require(id != 0, "owned resource required")',' let id = load64(local_type(f, slot))\n do require(id != 0, "owned resource required")\n if load64(record_info(id)+144)==14\n  do store64(state()+24,load64(state()+24)-1)\n  return invoke_records(name,depth)\n end')
# release already parsed a path: rewind its start rather than a fixed token distance.
replace('fn invoke_owned(name, depth)\n let f = load64(state() + 32)','fn invoke_owned(name, depth)\n let owned_arg_start=load64(state()+24)\n let f = load64(state() + 32)')
replace('do store64(state()+24,load64(state()+24)-1)','do store64(state()+24,owned_arg_start)')
replace('fn collection_property(id)\n do emit','fn collection_property(id)\n if load64(record_info(id)+144)==14\n  return records_property(id)\n end\n do emit')
# Return the source of ordinary heap helpers plus the reviewed row operations.
match=re.search(r'fn heap_runtime_source\(\)\n return (".*")\nend',s)
if not match:raise ValueError('heap runtime literal drift')
base=__import__('json').loads(match.group(1));combined=__import__('json').dumps(base+'\n'+(R/'experiments/nested-owned/records-runtime.flow').read_text(),ensure_ascii=False)
s=s[:match.start(1)]+combined+s[match.end(1):]

# Replace whole reviewed helper definitions; compile code remains RF2.
new=(R/'experiments/nested-owned/compiler-extension.flow').read_text()
for match in re.finditer(r'^fn ([a-z_][a-z_0-9]*)\(',new,re.M):
 name=match.group(1);start=match.start();following=re.search(r'^fn ',new[match.end():],re.M);end=match.end()+following.start()if following else len(new);body=new[start:end].rstrip()+'\n'
 pattern=re.compile(r'^fn '+re.escape(name)+r'\(.*?(?=^fn |\Z)',re.S|re.M)
 if pattern.search(s):s,count=pattern.subn(lambda _:body,s);assert count==1
 else:s+='\n'+body
D.mkdir(parents=True);(D/'compiler.flow').write_text(s);print(hashlib.sha256(s.encode()).hexdigest())
