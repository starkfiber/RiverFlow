from pathlib import Path
import subprocess,tempfile,os,json,hashlib
R=Path(__file__).resolve().parents[2];C=Path(os.environ['RF2_TEST_COMPILER']);header='profile RF2_SYSTEM_A64_V1\narray Bytes(u8,128)\nview Slice(Bytes)\n';cases=[]
def add(name,body,good=True,exit=0):cases.append((name,header+body,good,exit))
add('overlap','fn main(argc,argv)\nlet data=Bytes()\nset data[0]=65\nset data[1]=66\nset data[2]=67\nlet a=Slice(data,0,2)\nlet b=Slice(data,1,2)\nreturn (a[1]!=b[0])|(b[1]!=67)|(a.length!=2)\nend\n')
add('derived','fn main(argc,argv)\nlet data=Bytes()\nset data[3]=77\nlet a=Slice(data,0,3)\nlet b=Slice(data,a.length,1)\nreturn b[0]!=77\nend\n')
add('empty-second','fn main(argc,argv)\nlet data=Bytes()\nlet a=Slice(data,0,128)\nlet b=Slice(data,a.length,0)\nreturn b.length\nend\n')
add('overflow-second','fn main(argc,argv)\nlet data=Bytes()\nlet a=Slice(data,0,1)\nlet b=Slice(data,127,18446744073709551615)\nreturn 0\nend\n',exit=2)
add('write-after-second','fn main(argc,argv)\nlet data=Bytes()\nlet a=Slice(data,0,1)\nlet b=Slice(data,1,1)\nset data[0]=9\nreturn 0\nend\n',False)
add('call-in-second','fn f()\nreturn 0\nend\nfn main(argc,argv)\nlet data=Bytes()\nlet a=Slice(data,0,1)\nlet b=Slice(data,f(),1)\nreturn 0\nend\n',False)
add('fresh-owned-storage','fn main(argc,argv)\nlet data=Bytes()\nset data[0]=65\nlet a=Slice(data,0,1)\nlet fresh=Bytes()\nlet b=Slice(fresh,0,1)\nreturn (a[0]!=65)|(b[0]!=0)\nend\n')
for n in [85,86]:
 body='fn big(data:Bytes)\n'+''.join(f'let v{i}=Slice(data,0,0)\n'for i in range(n))+f'return v{n-1}.length\nend\nfn main(argc,argv)\nlet data=Bytes()\nreturn big(data)\nend\n';add(f'frame-{n}',body,n==85)
rows=[]
with tempfile.TemporaryDirectory(prefix='rf2-multi-view-')as tmp:
 for name,src,good,exit in cases:
  for opt in [False,True]:
   path=Path(tmp)/(name+str(opt));source=path.with_suffix('.rf2');source.write_text(src);p=subprocess.run([C,source,path]+(['--opt']if opt else[]),capture_output=True,timeout=30)
   if good:
    assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',path],check=True,capture_output=True);p=subprocess.run([path],input=b'',capture_output=True,timeout=5);assert p.returncode==exit,(name,opt,p.returncode,p.stderr)
   else:assert p.returncode==1 and not path.exists(),(name,opt,p.stderr)
   rows.append({'name':name,'optimized':opt,'passed':True})
v={'passed':True,'checks':rows,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'scope':'18 tests of multiple frame-owned immutable byte views; all-call/all-array-write freeze remains until function return.'};Path(os.environ.get('RF2_TEST_REPORT',str(R/'docs/MULTIPLE-VIEWS-VERIFICATION.json'))).write_text(json.dumps(v,indent=2)+'\n');print('multiple view checks',len(rows),'passed')
