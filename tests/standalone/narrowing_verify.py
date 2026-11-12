from pathlib import Path
import os,subprocess,tempfile,json,random,hashlib
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c'));OLD=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/package/rf2-0.10.0/rf2c'));M=(1<<64)-1;W=(1<<32)-1
io=(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1];parse='fn parse(p)\nlet n=0\nlet i=0\nwhile load8(p+i)!=0\nset n=n*10+load8(p+i)-48\nset i=i+1\nend\nreturn n\nend\n'
cases=[('x&4294967295',lambda x,y:x&W),('(x*1)&4294967295',lambda x,y:x&W),('(x*1099511627776)&4294967295',lambda x,y:0),('(x*4294967297)&4294967295',lambda x,y:x&W),('(x*4294967299)&4294967295',lambda x,y:x*3&W),('(x*18446744073709551615)&4294967295',lambda x,y:-x&W),('((x^y)*33+17)&4294967295',lambda x,y:((x^y)*33+17)&W),('(x+4294967303)&4294967295',lambda x,y:(x+7)&W),('(x&18446744073709486080)&4294967295',lambda x,y:x&0xffff0000),('(x|18446744073709551615)&4294967295',lambda x,y:W),('(x+~y)&4294967295',lambda x,y:(x+~y)&W),('(x+(y>>3))&4294967295',lambda x,y:(x+(y>>3))&W),('(x//y)&4294967295',lambda x,y:(x//y if y else 0)&W),('(x+(y<33))&4294967295',lambda x,y:(x+int(y<33))&W),('(x*(y+4294967296))&4294967295',lambda x,y:x*y&W),('(x*32)&4294967295',lambda x,y:x*32&W),('(x*2147483648)&4294967295',lambda x,y:x*(1<<31)&W)]
source='profile RF2_SYSTEM_A64_V1\n'+io+parse+''.join(f'fn f{i}(x,y)\nset x={s}\nreturn x\nend\n'for i,(s,_)in enumerate(cases))+'fn main(argc,argv)\nlet x=parse(load64(argv+8))\nlet y=parse(load64(argv+16))\nlet index=parse(load64(argv+24))\n'
for i in range(len(cases)):source+=f'if index=={i}\ndo io_number(f{i}(x,y))\ndo io_print("\\n")\nend\n'
source+='return 0\nend\n';report={'passed':False,'oracleCases':0,'old10Comparisons':0,'guards':'Final u32 mask and polynomial/bitwise-only expression; divisions, right shifts and comparisons retain u64 evaluation.'}
with tempfile.TemporaryDirectory(prefix='rf2-narrow11-')as tmp:
 d=Path(tmp);src=d/'source.rf2';src.write_text(source);paths=[]
 for name,c in [('old',OLD),('new',C)]:
  out=d/name;p=subprocess.run([c,src,out,'--opt'],capture_output=True);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);paths.append(out)
 rng=random.Random(202611122)
 for i in range(340):
  index=i%len(cases);x=rng.choice([0,1,M,(1<<63)+11,rng.randrange(1<<64)]);y=rng.choice([0,1,M,(1<<32)+1,rng.randrange(1<<64)]);e=cases[index][1](x,y)
  for p in paths:
   q=subprocess.run([p,str(x),str(y),str(index)],capture_output=True,timeout=5);assert q.returncode==0 and int(q.stdout)==e,(index,x,y,e,q.stdout,q.stderr)
  report['oracleCases']+=1;report['old10Comparisons']+=1
report.update(passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest());(R/'docs/NARROWING-0.11-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
