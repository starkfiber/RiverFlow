from pathlib import Path
import subprocess,json
r=Path.cwd();d=r/'artifacts/nested-039';c=d/'compiler-build/program';rows=[]
base='profile RF2_SYSTEM_A64_V1\nrecord Clock(start:u64,finish:u64)\nrecord Reservation(id:u64,clock:Clock)\n'
valid=base+'''fn extend(clock:Clock)
 set clock.finish=12
 return 0
end
fn main(argc,argv)
 let time=Clock(9,10)
 let booking=Reservation(7,time)
 do extend(booking.clock)
 if (booking.clock.start!=9)|(booking.clock.finish!=12)|(time.finish!=12)|(booking.id!=7)
  return 1
 end
 return 0
end
'''
cases={'borrow-and-alias':(valid,True),'wrong-child':(base+'fn main(argc,argv)\n let b=Reservation(7,99)\n return 0\nend\n',False),'rebind-child':(base+'fn main(argc,argv)\n let t=Clock(1,2)\n let u=Clock(3,4)\n let b=Reservation(1,t)\n set b.clock=u\n return 0\nend\n',False),'escaping-result':(base+'result Bad(Reservation,u64)\nfn main(argc,argv)\n return 0\nend\n',False),'resource-child':('profile RF2_SYSTEM_A64_V1\nresult IO(u64,u64)\ncollection Numbers(IO,8)\nrecord Bad(items:Numbers)\nfn main(argc,argv)\n return 0\nend\n',False),'self-cycle':('profile RF2_SYSTEM_A64_V1\nrecord Node(next:Node)\nfn main(argc,argv)\n return 0\nend\n',False)}
for name,(src,accepted) in cases.items():
 p=d/(name+'.flow');p.write_text(src)
 for opt in (False,True):
  out=d/(name+str(opt));q=subprocess.run([str(c),str(p),str(out),*(['--opt'] if opt else [])],capture_output=True);assert (q.returncode==0)==accepted,(name,q.stderr,q.stdout)
  row={'case':name,'optimized':opt,'compiled':q.returncode==0,'diagnostic':(q.stderr+q.stdout).decode()[:300]}
  if accepted:
   subprocess.run(['/usr/bin/codesign','-s','-',str(out)],check=True,capture_output=True);x=subprocess.run([str(out)]);assert x.returncode==0;row['runExit']=x.returncode
  rows.append(row)
(d/'results.json').write_text(json.dumps({'scope':'Private experimental borrowed record composition, not inline values or released compiler','checks':rows},indent=2));print(len(rows),'prototype cases passed')
