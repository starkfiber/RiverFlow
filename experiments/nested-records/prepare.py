from pathlib import Path
import sys,hashlib
r=Path.cwd();raw=(r/'native/compiler/compiler.rf2').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='3d2e7d65cc545c116b9c75aaabb10b0906f5b3cb7cdf9a3c29fa5c3ab51665d7','baseline compiler source changed; review patch'
s=raw.decode()
s=s.replace('fn scan_record()','fn field_type(id,field)\n return buffer("record_field_types",4096)+((id-1)*16+field)*8\nend\nfn record_nested(id)\n let i=0\n while i<load64(record_info(id)+8)\n  if load64(field_type(id,i))!=0\n   return 1\n  end\n  set i=i+1\n end\n return 0\nend\nfn scan_record()',1)
s=s.replace('do require(load64(record_info(field) + 8) <= 4, "result record payload field bound")','do require(load64(record_info(field) + 8) <= 4, "result record payload field bound")\n   do require(record_nested(field)==0,"borrowed nested record cannot escape in result")',1)
s=s.replace('  do expect(":")\n  do expect("u64")\n  do store64(r + 16 + n * 8, field)','  do expect(":")\n  if match("u64")\n   do advance()\n  else\n   let child=record_index(advance())\n   do require((child!=0)&(child<id),"nested record requires earlier type")\n   do require(load64(record_info(child)+144)==0,"nested field requires plain borrowed record")\n   do store64(field_type(id,n),child)\n  end\n  do store64(r + 16 + n * 8, field)',1)
s=s.replace('  do scalar_expression(1, 0)\n  do access_local(0, target + 1 + i, 1)','  let child_type=load64(field_type(id,i))\n  if child_type\n   do expression(1,0)\n   do require(load64(state()+136)==child_type,"nested constructor type mismatch")\n  else\n   do scalar_expression(1,0)\n  end\n  do access_local(0, target + 1 + i, 1)',1)
s=s.replace(' while match(".") | match("[")\n  set id',' while match(".") | match("[")\n  let next_type=0\n  set id',1)
s=s.replace('    set slot = field_index(id, advance())\n    do emit(4181721088 | (slot << 10))','    set slot = field_index(id, advance())\n    set next_type=load64(field_type(id,slot))\n    do emit(4181721088 | (slot << 10))',1)
s=s.replace('  do store64(state() + 136, 0)\n  do store64(state() + 232, 0)\n end\n set i = load64(state() + 24)','  do store64(state() + 136, next_type)\n  do store64(state() + 232, 0)\n end\n set i = load64(state() + 24)',1)
# Keep nested child binding immutable; support leaf mutation via a typed helper borrow.
old_assignment='     do advance()\n     set field = field_index(id, advance())\n     do expect("=")\n     do scalar_expression(1, 0)\n     do access_local(1, target, 0)\n     do emit(4177526816 | (field << 10))'
new_assignment='     do access_local(0,target,0)\n     do advance()\n     set field=field_index(id,advance())\n     while match(".")\n      set id=load64(field_type(id,field))\n      do require(id!=0,"nested path traverses a scalar")\n      do emit(4181721088 | (field<<10))\n      do advance()\n      set field=field_index(id,advance())\n     end\n     do require(load64(field_type(id,field))==0,"nested child binding is immutable")\n     do push()\n     do expect("=")\n     do scalar_expression(1,0)\n     do pop1()\n     do emit(4177526816 | (field<<10))'
assert s.count(old_assignment)==1,'assignment patch drift'
s=s.replace(old_assignment,new_assignment,1)
destination=Path(sys.argv[1]) if len(sys.argv)>1 else r/'artifacts/nested-039'
destination.mkdir(parents=True,exist_ok=True)
with (destination/'compiler.flow').open('x') as output:output.write(s)
