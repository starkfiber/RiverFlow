"""Native bounded heap collections, ownership and borrowing controls.
Local developer controller; no provider, network or hardware effects.
"""
from pathlib import Path
import hashlib,json,os,subprocess,time,random
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']).resolve();D=R/'artifacts/heap-collections'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
HEAD='profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ncollection Numbers(IO,65536)\n'
ROWS=[];serial=0
def run(args,data=None):return subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=30,env={'PATH':'/nonexistent'})
def build(label,source,mode,good=True,expected=0):
 global serial
 serial+=1;p=D/(str(serial)+'.flow');p.write_text(source);out=D/str(serial);q=run([C,p,out,*mode]);row=dict(case=label,mode=mode,sourceSHA256=hashlib.sha256(source.encode()).hexdigest(),compileExit=q.returncode)
 if good:
  assert q.returncode==0,(label,q.stderr);assert run(['/usr/bin/codesign','-s','-',out]).returncode==0;q=run([out]);assert q.returncode==expected,(label,q.returncode,q.stdout,q.stderr);row.update(exit=q.returncode,binarySHA256=hashlib.sha256(out.read_bytes()).hexdigest())
 else:assert q.returncode!=0 and not out.exists(),(label,q.returncode,q.stderr)
 ROWS.append(row)
def program(body,helpers=''):
 return HEAD+helpers+'fn work():IO\n'+body+'\nend\nfn main(argc,argv)\n handle work()\n ok value\n  return value\n err cause\n  return cause\n end\n return 0\nend\n'
def handle(expr,ok,err,code='return err('+str(99)+')'):
 return ' handle '+expr+'\n ok '+ok+'\n err '+err+'\n  '+code+'\n end\n'
for mode in [[],['--opt'],['--compact'],['--opt','--compact']]:
 body=' own a=Numbers()\n if (a.length!=0)|(a.capacity!=0)|(a.limit!=65536)\n  return err(1)\n end\n'+handle('collection_reserve(a,1)','cap','reserve_error')+' if a.capacity!=16\n  return err(2)\n end\n let i=0\n while i<20000\n'+handle('collection_push(a,i*17)','length','push_error')+'  set i=i+1\n end\n if (a.length!=20000)|(a.capacity!=32768)\n  return err(3)\n end\n set i=0\n while i<20000\n handle collection_get(a,i)\n ok value\n  if value!=i*17\n   return err(4)\n  end\n err get_error\n  return err(get_error)\n end\n set i=i+1\n end\n'+handle('collection_set(a,19999,18446744073709551615)','set_value','set_error')+' handle collection_get(a,19999)\n ok last\n  if last!=18446744073709551615\n   return err(5)\n  end\n err last_error\n  return err(last_error)\n end\n return ok(0)'
 build('grow relocate preserve20000 values',program(body),mode)
 body=' own a=Numbers()\n'+handle('collection_push(a,41)','n','push_error')+' own b=move(a)\n'+handle('bump(b,b)','bumped','bump_error')+' handle collection_get(b,0)\n ok value\n  return ok(value!=42)\n err get_error\n  return err(get_error)\n end\n return err(90)'
 helper='fn bump(a:Numbers,b:Numbers):IO\n handle collection_get(a,0)\n ok old\n  handle collection_set(b,0,old+1)\n  ok changed\n   return ok(changed)\n  err set_error\n   return err(set_error)\n  end\n err get_error\n  return err(get_error)\n end\n return err(90)\nend\n'
 build('local move and aliased borrows',program(body,helper),mode)
 body=' own a=Numbers()\n'+handle('collection_push(a,7)','n','push_error')+handle('collection_clear(a)','cleared','clear_error')+' if (a.length!=0)|(a.capacity!=16)\n  return err(1)\n end\n handle collection_get(a,0)\n ok bad\n  return err(2)\n err bounds\n  if bounds!=34\n   return err(3)\n  end\n end\n handle collection_reserve(a,65537)\n ok bad_capacity\n  return err(4)\n err limit\n  if limit!=22\n   return err(5)\n  end\n end\n return ok(0)'
 build('clear and recoverable range/limit',program(body),mode)
 body=' own a=Numbers()\n'+handle('collection_push(a,42)','n','push_error')+handle('release(a)','released','release_error')+' handle collection_get(a,0)\n ok bad\n  return err(1)\n err closed\n  if closed!=9\n   return err(2)\n  end\n end\n handle release(a)\n ok bad_release\n  return err(3)\n err again\n  return ok(again!=9)\n end\n return err(90)'
 build('release runtime state and double release',program(body),mode)
 body=' own a=Numbers()\n'+handle('collection_push(a,42)','n','push_error')+' return ok(42)'
 src=program(body).replace('ok value\n  return value','ok value\n  return value!=42');build('cleanup preserves nonzero successful result',src,mode)
 body=' own a=Numbers()\n'+handle('collection_push(a,42)','n','push_error')+' return err(37)';build('cleanup preserves primary error',program(body),mode,expected=37)
 negative=[('copy',' own a=Numbers()\n let b=a\n return ok(0)'),('read moved',' own a=Numbers()\n own b=move(a)\n return ok(a.length)'),('double move',' own a=Numbers()\n own b=move(a)\n own c=move(a)\n return ok(0)'),('raw escape',' own a=Numbers()\n do write(1,a,8)\n return ok(0)'),('owner result',' own a=Numbers()\n return ok(a)'),('nested move',' own a=Numbers()\n if 1\n own b=move(a)\n end\n return ok(0)')]
 for label,body in negative:build(label,program(body),mode,False)
 for label,helper in [('borrow release','handle release(a)\n ok n\n err e\n end\nreturn ok(0)'),('borrow move','own b=move(a)\nreturn ok(0)')]:
  src=HEAD+'fn bad(a:Numbers):IO\n'+helper+'\nend\nfn main(argc,argv)\nreturn 0\nend\n';build(label,src,mode,False)
 for label,source in [('private helper definition','profile RF2_SYSTEM_A64_V1\nfn __rf2heap_fake(x)\nreturn x\nend\nfn main(argc,argv)\nreturn 0\nend\n'),('private helper call',program(' own a=Numbers()\n do __rf2heap_op(0,0,0,0,0)\n return ok(0)'))]:build(label,source,mode,False)
report=dict(passed=True,schema='rf2.heap.collection.verification.v1',cases=ROWS,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),compilerSourceSHA256=hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits='Bounded u64 collections on one Mac, native ordinary/optimized and full/compact modes. Runtime mapping failure injection and relocation address instrumentation are separately qualified. No owner return/function ownership transfer, concurrency, whole-language safety, platform or speed claim.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),passed=True,cases=len(ROWS))))
