"""Edge-valued native instruction selection versus integer oracle and 0.10."""
from pathlib import Path
import subprocess,tempfile,random,json,os,hashlib
R=Path(__file__).resolve().parents[2];C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c'));OLD=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/package/rf2-0.10.0/rf2c'));M=(1<<64)-1;ops=['+','-','*','&','|','^','<<','>>','//','==','!=','<','<=','>','>='];constants=[0,1,2,3,7,31,32,33,63,64,65,255,256,257,4095,4096,(1<<32)-1,1<<32,1<<63,(1<<63)+1,M];values=[0,1,17,4096,(1<<32)-1,(1<<63)+11,M];io=(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1];parse='fn parse(p)\nlet n=0\nlet i=0\nwhile load8(p+i)!=0\nset n=n*10+load8(p+i)-48\nset i=i+1\nend\nreturn n\nend\n';count=0
with tempfile.TemporaryDirectory(prefix='rf2-instructions11-')as tmp:
 d=Path(tmp)
 for opindex,op in enumerate(ops):
  code='profile RF2_SYSTEM_A64_V1\n'+io+parse+''.join(f'fn f{i}(x)\nreturn x {op} {n}\nend\n'for i,n in enumerate(constants))+'fn main(argc,argv)\nlet x=parse(load64(argv+8))\nlet index=parse(load64(argv+16))\n'
  for i in range(len(constants)):code+=f'if index=={i}\ndo io_number(f{i}(x))\ndo io_print("\\n")\nend\n'
  code+='return 0\nend\n';src=d/f'source{opindex}.rf2';src.write_text(code);paths=[]
  for label,c in [('old',OLD),('new',C)]:
   out=d/f'{label}{opindex}';p=subprocess.run([c,src,out,'--opt'],capture_output=True);assert p.returncode==0,p.stderr;subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);paths.append(out)
  for i,n in enumerate(constants):
   for x in values:
    if op=='+':e=(x+n)&M
    elif op=='-':e=(x-n)&M
    elif op=='*':e=x*n&M
    elif op=='&':e=x&n
    elif op=='|':e=x|n
    elif op=='^':e=x^n
    elif op=='<<':e=x<<(n&63)&M
    elif op=='>>':e=x>>(n&63)
    elif op=='//':e=x//n if n else 0
    elif op=='==':e=int(x==n)
    elif op=='!=':e=int(x!=n)
    elif op=='<':e=int(x<n)
    elif op=='<=':e=int(x<=n)
    elif op=='>':e=int(x>n)
    else:e=int(x>=n)
    for out in paths:
     p=subprocess.run([out,str(x),str(i)],capture_output=True,timeout=5);assert p.returncode==0 and int(p.stdout)==e,(op,x,n,e,p.stdout,p.stderr)
    count+=1
report={'passed':True,'independentEdgeCases':count,'old10Comparisons':count,'operators':ops,'constants':constants,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'scope':'Unsigned-u64 arithmetic and comparison, architecture-defined masked shifts and UDIV-zero behavior. Not a claim about C undefined operations or a complete compiler proof.'};(R/'docs/INSTRUCTION-SELECTION-0.11-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
