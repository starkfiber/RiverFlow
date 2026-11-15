"""Compile source-checked API cards into a native, no-file-access lookup utility."""
from pathlib import Path
import hashlib,json,subprocess,sys
if len(sys.argv)!=4:raise SystemExit('Usage: build-docs.py COMPILER STAGED-LIB NEW-DIRECTORY')
C,LIB,D=map(lambda x:Path(x).resolve(),sys.argv[1:]);D.mkdir(parents=True,exist_ok=False);cards=json.loads((Path(__file__).with_name('api-cards.json')).read_text());entries=[]
for name,contract in cards.items():
 found=[]
 for p in sorted(LIB.iterdir()):
  if p.suffix not in('.flow','.rf2'):continue
  for i,line in enumerate(p.read_text().splitlines(),1):
   if line.startswith(('fn '+name+'(', 'record '+name+'(', 'result '+name+'(')):found.append((p.name,i,line))
 if name=='records_read':
  anchor=Path(__file__).resolve().parents[2]/'experiments/nested-owned/compiler-extension.flow'
  matches=[i for i,line in enumerate(anchor.read_text().splitlines(),1)if 'if tmatch(name,"records_read")'in line];assert len(matches)==1
  found=[('compiler intrinsic (experiments/nested-owned/compiler-extension.flow)',matches[0],'Intrinsic records_read(rows,index,out): declared IO; out has the declared nominal row type')]
 if len(found)!=1:raise ValueError((name,found))
 file,line,signature=found[0];location=('experiments/nested-owned/compiler-extension.flow'if name=='records_read'else'lib/'+file)+':'+str(line);entries.append(dict(name=name,signature=signature,source=location,contract=contract))
source='''profile RF2_SYSTEM_A64_V1
fn equal(a,b)
 let i=0
 while load8(a+i)==load8(b+i)
  if load8(a+i)==0
   return 1
  end
  set i=i+1
  if i>64
   return 0
  end
 end
 return 0
end
fn say(p)
 let n=0
 while load8(p+n)
  set n=n+1
 end
 let used=0
 while used<n
  let got=write(1,p+used,n-used)
  if (got==0)|(got>>63)
   return 0
  end
  set used=used+got
 end
 return 1
end
fn lookup(query)
'''
for e in entries:
 text=e['signature']+'\n'+e['contract']+'\nSource: '+e['source']+'\n'
 source+=' if equal(query,'+json.dumps(e['name'])+')\n  if say('+json.dumps(text,ensure_ascii=False)+')\n   return 0\n  end\n  return 1\n end\n'
source+=' if equal(query,"--list")\n  if say('+json.dumps('\n'.join(e['name']for e in entries)+'\n')+')\n   return 0\n  end\n  return 1\n end\n return 2\nend\nfn main(argc,argv)\n if (argc<2)|(argc>30)\n  return 2\n end\n let i=1\n while i<argc\n  let status=lookup(load64(argv+i*8))\n  if status\n   return status\n  end\n  set i=i+1\n end\n return 0\nend\n';p=D/'api.flow';p.write_text(source);binary=D/'rf2-doc'
q=subprocess.run([str(C),str(p),str(binary),'--compact','--opt'],capture_output=True,timeout=30);q.check_returncode();subprocess.run(['/usr/bin/codesign','-s','-',str(binary)],check=True,capture_output=True)
checks=[]
for e in entries:
 q=subprocess.run([str(binary),e['name']],capture_output=True,timeout=10);assert q.returncode==0 and e['signature'].encode()in q.stdout and e['contract'].encode()in q.stdout;checks.append(e['name'])
q=subprocess.run([str(binary),'app_form','store_configure','mcp_serve'],capture_output=True);assert q.returncode==0 and all(x in q.stdout for x in[b'fn app_form(',b'fn store_configure(',b'fn mcp_serve('])
for args in[[],['missing'],['x'*65],['ui_input','extra']]:assert subprocess.run([str(binary),*args],capture_output=True).returncode==2
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();(D/'RESULTS.json').write_text(json.dumps(dict(compilerSHA256=sha(C),sourceSHA256=sha(p),binarySHA256=sha(binary),cards=len(entries),checks=checks,invalidArgumentCases=4,entries=entries),indent=2)+'\n');print(json.dumps(dict(binary=str(binary),cards=len(entries),invalidArgumentCases=4)))
