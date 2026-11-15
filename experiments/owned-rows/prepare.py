"""Prepare owned structured-row candidate; preserves the pinned 0.44 baseline."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[2]
if len(sys.argv)!=2:raise SystemExit('Usage: prepare.py NEW-DIRECTORY')
D=Path(sys.argv[1]).resolve()
if D.exists():raise SystemExit('Use a new output directory')
with tempfile.TemporaryDirectory(prefix='rf2-owned-rows-')as temporary:
 p=Path(temporary)/'base';subprocess.run([sys.executable,str(R/'experiments/nested-owned/prepare.py'),p],cwd=R,check=True,capture_output=True);s=(p/'compiler.flow').read_text()
if hashlib.sha256(s.encode()).hexdigest()!='65d729395929b8766b5f3d96aa0730a558004e74964fb31e9022bdd02065d0c7':raise ValueError('Review changed 0.44 base')
def replace(old,new):
 global s
 if s.count(old)!=1:raise ValueError(('patch drift',old[:100],s.count(old)))
 s=s.replace(old,new,1)
replace('   do require((load64(record_info(row)+144)==0)&(record_nested(row)==0),"record collection requires flat scalar row")\n   do require(n<=65536//load64(record_info(row)+8),"record collection word bound")\n   do store64(r+144,14)', '''   if owned_kind(row)
    do require(n<=65536//owned_storage_size(row),"owned row collection word bound")
    do require(load64(record_info(row)+152)==load64(r+152),"owned row error type mismatch")
    do store64(r+144,15)
   else
    do require((load64(record_info(row)+144)==0)&(record_nested(row)==0),"record collection requires flat scalar row")
    do require(n<=65536//load64(record_info(row)+8),"record collection word bound")
    do store64(r+144,14)
   end''')
# Extend exact leaf-owner admission sites, not arbitrary numeric comparisons.
for v in ('id','other'):
 s=s.replace('(load64(record_info('+v+')+144)==14)', '((load64(record_info('+v+')+144)==14)|(load64(record_info('+v+')+144)==15))')
# Undo specialized row dispatch/property sites: new operations have different semantics.
replace(' if load64(record_info(id)+144)==14\n  do store64(state()+24,owned_arg_start)', ' if load64(record_info(id)+144)==15\n  do store64(state()+24,owned_arg_start)\n  return invoke_own_rows(name,depth)\n end\n if load64(record_info(id)+144)==14\n  do store64(state()+24,owned_arg_start)')
replace(' if load64(record_info(id)+144)==14\n  return records_property(id)', ' if load64(record_info(id)+144)==15\n  return own_rows_property(id)\n end\n if load64(record_info(id)+144)==14\n  return records_property(id)')
replace('return (kind==11)|(kind==12)|(kind==13)|(kind==14)','return (kind==11)|(kind==12)|(kind==13)|(kind==14)|(kind==15)')
replace('-((load64(record_info(id)+144)==14)|(load64(record_info(id)+144)==15))*3','-(((load64(record_info(id)+144)==14)|(load64(record_info(id)+144)==15)))*3-(load64(record_info(id)+144)==15)')
replace('    if load64(record_info(id)+144)==12\n     set count=aggregate_slots(id)','    if load64(record_info(id)+144)==15\n     set count=10\n    end\n    if load64(record_info(id)+144)==12\n     set count=aggregate_slots(id)')
replace(' let slots=6\n if load64(record_info(id)+144)==12',' let slots=owned_storage_size(id)-1\n if load64(record_info(id)+144)==12')
replace('fn owned_storage_size(id)\n if','fn owned_storage_size(id)\n if load64(record_info(id)+144)==15\n  return 11\n end\n if')
replace('  while word<6\n   do emit(4181721088 | ((offset+1+word)<<10)', '  while word<owned_storage_size(id)-1\n   do emit(4181721088 | ((offset+1+word)<<10)')
replace('fn collection_construct_value(f,slot,id)\n let i = 0','fn collection_construct_value(f,slot,id)\n if load64(record_info(id)+144)==15\n  return construct_own_rows(f,slot,id)\n end\n let i = 0')
replace('fn heap_intrinsic(t)\n if records_intrinsic(t)','fn heap_intrinsic(t)\n if own_rows_intrinsic(t)\n  return 1\n end\n if records_intrinsic(t)')
replace('if same(p,9,"__rf2heap",9)','if same(p,9,"__rf2heap",9)|same(p,9,"__rf2rows",9)')
replace(' if records_intrinsic(name)\n  return invoke_records(name,depth)',' if own_rows_intrinsic(name)\n  return invoke_own_rows(name,depth)\n end\n if records_intrinsic(name)\n  return invoke_records(name,depth)')
# Private metadata objects occupy the zero-filled region without user buffer-name aliases.
s=s.replace('(load64(obj)==2))','((load64(obj)==2)|(load64(obj)==4)))')
m=re.search(r'fn heap_runtime_source\(\)\n return (".*")\nend',s)
if not m:raise ValueError('heap runtime literal drift')
base=json.loads(m.group(1))
needle='fn __rf2heap_op(d,op,a,b,limit):__rf2heap_IO\n'
assert base.count(needle)==1
base=base.replace(needle,needle+''' if load64(d)==2
  handle __rf2rows_op(d,op,a,b)
  ok value
   return ok(value)
  err cause
   return err(cause)
  end
 end
''')
combined=json.dumps(base+'\n'+(R/'experiments/owned-rows/runtime.flow').read_text(),ensure_ascii=False)
s=s[:m.start(1)]+combined+s[m.end(1):]
s+='\n'+(R/'experiments/owned-rows/compiler-extension.flow').read_text()
D.mkdir(parents=True);(D/'compiler.flow').write_text(s);print(hashlib.sha256(s.encode()).hexdigest())
