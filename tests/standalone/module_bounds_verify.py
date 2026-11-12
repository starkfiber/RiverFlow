from pathlib import Path
import tempfile,subprocess,json,os
r=Path(__file__).resolve().parents[2];c=Path(os.environ.get('RF2_TEST_COMPILER',r/'output/native-compiler/rf2c'));report={'passed':False,'successes':0,'refusals':0}
def build(src,out,good):
 p=subprocess.run([c,src,out],capture_output=True);assert (p.returncode==0)==good,(p.stderr,src)
 if good:
  subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);assert subprocess.run([out]).returncode==1;report['successes']+=1
 else:assert not out.exists();report['refusals']+=1
with tempfile.TemporaryDirectory()as tmp:
 d=Path(tmp)
 for fields in [1,8,16,17]:
  src=d/f'fields{fields}.rf2';src.write_text('profile RF2_SYSTEM_A64_V1\nrecord R('+','.join(f'f{i}: u64'for i in range(fields))+')\nfn main(a,b)\n let p = R('+','.join(str(i+1)for i in range(fields))+')\n return p.f'+str(fields-1)+' == '+str(fields)+'\nend\n');build(src,d/f'f{fields}',fields<=16)
 for count in [32,33]:
  src=d/f'records{count}.rf2';src.write_text('profile RF2_SYSTEM_A64_V1\n'+''.join(f'record R{i}(x: u64)\n'for i in range(count))+f'fn main(a,b)\n let p = R{count-1}(1)\n return p.x\nend\n');build(src,d/f'r{count}',count==32)
 for count in [31,32]:
  for i in range(count):(d/f'm{i}.rf2').write_text('module m'+str(i)+'\nfn f'+str(i)+'()\nreturn 1\nend\n')
  src=d/f'main{count}.rf2';src.write_text('profile RF2_SYSTEM_A64_V1\n'+''.join(f'use "m{i}.rf2"\n'for i in range(count))+'fn main(a,b)\nreturn f0()\nend\n');build(src,d/f'mp{count}',count==31)
 for depth in [15,16]:
  for i in range(depth):(d/f'c{i}.rf2').write_text(f'module c{i}\n'+(f'use "c{i+1}.rf2"\n'if i<depth-1 else'fn val()\nreturn 1\nend\n'))
  src=d/f'depth{depth}.rf2';src.write_text('profile RF2_SYSTEM_A64_V1\nuse "c0.rf2"\nfn main(a,b)\nreturn val()\nend\n');build(src,d/f'd{depth}',depth==15)
 # Correct lifetime on recursive calls: each invocation owns separate record storage.
 src=d/'recursive.rf2';src.write_text('profile RF2_SYSTEM_A64_V1\nrecord R(x: u64)\nfn f(n)\n let p = R(n)\n if n == 0\n return 0\n end\n let before = p.x\n let rest = f(n-1)\n return before + rest + (p.x != before)*99999\nend\nfn main(a,b)\nreturn f(100) == 5050\nend\n');build(src,d/'recursive',True)
report['passed']=True;(r/'docs/MODULE-BOUNDS-0.10.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
