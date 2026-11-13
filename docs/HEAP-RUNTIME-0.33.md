# Auditable collection lowering, development0.33

This is a derived, read-only view of the exact helper source embedded in the native compiler. The compiler literal is authoritative; this page is not loaded at runtime and is not a standalone user module or a public pointer API. User calls/declarations in the private helper namespace refuse. The helper source participates in lowered-source limits and image identity.

```rf2

result __rf2heap_IO(u64,u64)
fn __rf2heap_pending(d):__rf2heap_IO
 let p = load64(d+32)
 if p==0
  return ok(0)
 end
 let status = syscall6(73,p,load64(d+40)*8,0,0,0,0)
 if status>>63
  return err(0-status)
 end
 do store64(d+32,0)
 do store64(d+40,0)
 return ok(0)
end
fn __rf2heap_grow(d,wanted,limit):__rf2heap_IO
 if wanted>limit
  return err(22)
 end
 handle __rf2heap_pending(d)
 ok cleaned
 err pending_error
  return err(pending_error)
 end
 let cap = load64(d+24)
 if wanted<=cap
  return ok(cap)
 end
 let next = cap*2
 if next<16
  set next = 16
 end
 if next>limit
  set next = limit
 end
 while next<wanted
  set next = next*2
  if next>limit
   set next = limit
  end
 end
 let fresh = syscall6(197,0,next*8,3,4098,18446744073709551615,0)
 if fresh>>63
  return err(0-fresh)
 end
 let old = load64(d+8)
 let size = load64(d+16)
 let i = 0
 while i<size
  do store64(fresh+i*8,load64(old+i*8))
  set i = i+1
 end
 if old
  let status = syscall6(73,old,cap*8,0,0,0,0)
  if status>>63
   do store64(d+32,fresh)
   do store64(d+40,next)
   return err(0-status)
  end
 end
 do store64(d+8,fresh)
 do store64(d+24,next)
 return ok(next)
end
fn __rf2heap_drop(d):__rf2heap_IO
 if load64(d)==0
  return err(9)
 end
 let first = 0
 let p = load64(d+8)
 if p
  let status = syscall6(73,p,load64(d+24)*8,0,0,0,0)
  if status>>63
   set first = 0-status
  else
   do store64(d+8,0)
   do store64(d+16,0)
   do store64(d+24,0)
  end
 end
 handle __rf2heap_pending(d)
 ok cleaned
 err pending_error
  if first==0
   set first = pending_error
  end
 end
 if (load64(d+8)==0)&(load64(d+32)==0)
  do store64(d,0)
 end
 if first
  return err(first)
 end
 return ok(0)
end
fn __rf2heap_op(d,op,a,b,limit):__rf2heap_IO
 if load64(d)==0
  return err(9)
 end
 if op==5
  handle __rf2heap_drop(d)
  ok released
   return ok(released)
  err release_error
   return err(release_error)
  end
 end
 if op==0
  handle __rf2heap_grow(d,a,limit)
  ok reserve_capacity
   return ok(reserve_capacity)
  err grow_error
   return err(grow_error)
  end
 end
 if op==1
  let length = load64(d+16)
  if length>=limit
   return err(22)
  end
  handle __rf2heap_grow(d,length+1,limit)
  ok push_capacity
  err push_error
   return err(push_error)
  end
  do store64(load64(d+8)+length*8,a)
  do store64(d+16,length+1)
  return ok(length+1)
 end
 if op==4
  do store64(d+16,0)
  return ok(0)
 end
 if a>=load64(d+16)
  return err(34)
 end
 if op==2
  return ok(load64(load64(d+8)+a*8))
 end
 do store64(load64(d+8)+a*8,b)
 return ok(b)
end

```
