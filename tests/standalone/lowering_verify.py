from pathlib import Path
import subprocess,json,os,re,random,hashlib,select,atexit
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_TEST_BINARY',str(R/'output/core-0.6-r6/rf2')));C=R/'output/native-compiler/rf2c';root=R/'output/lowering-0.6';root.mkdir(exist_ok=True)
import tempfile
work=Path(tempfile.mkdtemp(prefix='run-',dir=root));p=subprocess.Popen(['/opt/homebrew/opt/node@22/bin/node',str(R/'tests/standalone/oracle.mjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE);atexit.register(lambda:p.kill()if p.poll()is None else None)
def oracle(src,data,count):
 p.stdin.write(json.dumps({'source':src,'data':data,'count':count}).encode()+b'\n');p.stdin.flush();return json.loads(p.stdout.readline())
S=(R/'examples/sum.flow').read_text()
def simple(op,args,mode='CHECKED'):return f'FLOW "Lowering"\nPROFILE RF2_U32_CORE_V0\nARITHMETIC {mode}\nFUNCTION main(data: u32[], count: u32) RETURNS u32\nSTEP x = {op} WITH {{ {args}, result: answer }}\nRETURN answer\nEND'
helper='FUNCTION plus(a: u32, b: u32) RETURNS u32\nSTEP x = ADD WITH { a: a, b: b, result: value }\nRETURN value\nEND\n'
sources=[S,S.replace('CHECKED','WRAP'),simple('ADD','a: 4294967295, b: 1'),simple('MUL','a: 4294967295, b: 4294967295','WRAP'),simple('LOAD','array: data, index: 1'),simple('POPCOUNT','value: 4294967295'),simple('NONZERO','value: 0'),S.replace('LIMIT 65536','LIMIT 1'),S.replace('FUNCTION main',helper+'FUNCTION main').replace('ADD WITH { a: total, b: item','CALL plus WITH { a: total, b: item'),S.replace('  RETURN total','  FOR j FROM 0 TO count LIMIT 65536\nVAR delta = 1\nSTEP y = ADD WITH { a: total, b: delta, result: total }\nEND FOR\n  RETURN total')]
sources+=re.findall(r'```flow\n([\s\S]*?)```',(R/'book/RiverFlow-First-Edition.md').read_text())
sources+=[(R/'capabilities/attendance.local.v1/tally.flow').read_text()]
# 501 distinct registers challenge systems compiler local-count limits: lowering uses bounded frames.
sources+=['FLOW "Many registers"\nPROFILE RF2_U32_CORE_V0\nARITHMETIC CHECKED\nFUNCTION main(data: u32[], count: u32) RETURNS u32\n'+'\n'.join(f'VAR v{i} = {i}'for i in range(501))+'\nRETURN v500\nEND']
worksource=S.replace('STEP add = ADD WITH','\n'.join(f'STEP w{i} = ADD WITH {{ a: total, b: 0, result: total }}'for i in range(20))+'\nSTEP add = ADD WITH');sources.append(worksource)
rng=random.Random(20261112);report={'schema':'rf2.direct.kernel.verification.v1','programFamilies':0,'executions':0,'passed':False,'speedClaim':None,'tokenClaim':None,'compilation':'native rf2 -> systems kernel -> native rf2c -> ARM64 image; explicit OS signing'}
for i,source in enumerate(sources):
 d=work/str(i);src=work/f'{i}.flow';src.write_text(source)
 r=subprocess.run([str(R/'tools/build-core.sh'),str(B),str(C),str(src),str(d)],cwd=R,capture_output=True,timeout=30);assert r.returncode==0,(i,r.stdout,r.stderr)
 arrays=[[],[1,2,3],[0,1,3,255],[4294967295,1]]+[[rng.randrange(2**32)for _ in range(rng.randrange(12))]for _ in range(5)]
 for j,data in enumerate(arrays):
  count=len(data)if j%3 else 0;e=oracle(source,data,count);got=subprocess.run([str(d/'program'),json.dumps(data),str(count)],capture_output=True,text=True,timeout=10,env={'PATH':'/nonexistent'});assert (got.returncode==0)==e['ok'],(i,source,data,e,got.stdout,got.stderr)
  if not e['ok']:
   for category in ['overflow','LOAD','Loop','work limit']:
    if category in e.get('error',''):assert category.lower() in got.stdout.lower(),(i,e,got.stdout)
  if e['ok']:
   v=json.loads(got.stdout);assert(v['value'],v['steps'])==(e['value'],e['steps']),(i,v,e)
  report['executions']+=1
 if source==worksource:
  # Large arrays go through a native diagnostic harness because macOS argv has a size ceiling.
  compiled=(d/'program.rf2').read_text();start=compiled.index('fn main(argc, argv)');end=compiled.index('\nend\n',start)+5
  main='''fn main(argc, argv)
 let data = buffer("large_probe", 262144)
 let value = cgn_entry(data, 65536, 65536)
 if load64(cgn_state()) != 18
  return 1
 end
 return 0
end
'''
  probe=d/'budget.rf2';probe.write_text(compiled[:start]+main+compiled[end:]);out=d/'budget';r=subprocess.run([str(C),str(probe),str(out)],capture_output=True,timeout=20);assert r.returncode==0,r.stderr;subprocess.run(['/usr/bin/codesign','-s','-',str(out)],check=True,capture_output=True);assert subprocess.run([str(out)],capture_output=True,timeout=10).returncode==0;report['executions']+=1
 report['programFamilies']+=1
# Generated attendance source is reproducible from the versioned Core artifact.
generated=subprocess.run([str(B),'lower',str(R/'capabilities/attendance.local.v1/tally.flow')],capture_output=True,check=True).stdout;assert generated==(R/'native/attendance-kernel.rf2').read_bytes();report['attendanceKernelReproduced']=True
report['uniqueSourcePrograms']=len(set(sources));p.stdin.close();p.wait(timeout=5);report.update(passed=True,runtimeSHA256=hashlib.sha256(B.read_bytes()).hexdigest(),compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),harnessSHA256=hashlib.sha256((R/'native/lowered-harness.rf2').read_bytes()).hexdigest());(R/'docs/DIRECT-KERNEL-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
