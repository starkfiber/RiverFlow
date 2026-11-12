"""Differential WebAssembly results/errors/work against retained0.18, without OS imports."""
from pathlib import Path
import subprocess,json,random,time,hashlib,os,select,shutil
R=Path(__file__).resolve().parents[2];D=R/'artifacts/foundation-0.19'/('wasm-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ.get('RF2_WASM_COMPILER',R/'output/wasm-0.19-r2/rf2-wasm'));old=Path(os.environ.get('RF2_CORE_BASELINE',R/'output/bin/rf2'));rows=[];rng=random.Random(190021)
peer=subprocess.Popen([os.environ.get('RF2_NODE',shutil.which('node')or'/opt/homebrew/opt/node@22/bin/node'),R/'tests/standalone/wasm_peer.mjs'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
def wasm(module,data,count=None,**extra):
 q={'module':str(module),'data':data,**extra}
 if count is not None:q['count']=count
 peer.stdin.write(json.dumps(q)+'\n');peer.stdin.flush();assert select.select([peer.stdout],[],[],10)[0],'wasm timeout';r=json.loads(peer.stdout.readline());assert'error'not in r,r;return r
def build(name,source,generic=False):
 src=D/(name+'.flow');out=D/(name+'.wasm');src.write_text(source);p=subprocess.run([C,*(['--generic']if generic else[]),src,out],capture_output=True,timeout=30);assert p.returncode==0,(name,p.stderr,p.stdout);return src,out
base=(R/'examples/sum.flow').read_text();programs=[('sum',base),('sum-wrap',base.replace('CHECKED','WRAP')),('squares',base.replace('STEP add = ADD WITH { a: total, b: item, result: total }','STEP mul = MUL WITH { a: item, b: item, result: square }\nSTEP add = ADD WITH { a: total, b: square, result: total }')),('popcount',base.replace('STEP add = ADD WITH { a: total, b: item, result: total }','STEP bits = POPCOUNT WITH { value: item, result: bits }\nSTEP add = ADD WITH { a: total, b: bits, result: total }')),('nonzero',base.replace('STEP add = ADD WITH { a: total, b: item, result: total }','STEP nz = NONZERO WITH { value: item, result: nz }\nSTEP add = ADD WITH { a: total, b: nz, result: total }'))]
helper='''FLOW "Helpers"
PROFILE RF2_U32_CORE_V0
ARITHMETIC CHECKED
FUNCTION twice(x: u32) RETURNS u32
 STEP add = ADD WITH { a: x, b: x, result: y }
 RETURN y
END
FUNCTION main(data: u32[], count: u32) RETURNS u32
 VAR total = 0
 FOR i FROM 0 TO count LIMIT 65536
 STEP read = LOAD WITH { array: data, index: i, result: x }
 STEP call = CALL twice WITH { x: x, result: y }
 STEP add = ADD WITH { a: total, b: y, result: total }
 END FOR
 RETURN total
END
''';programs.append(('helpers',helper))
try:
 for original_name,source in programs:
  for generic in [False,True]:
   name=original_name+('-generic'if generic else'-optimized')
   src,module=build(name,source,generic)
   tests=[([],0),([1,2,3],3),([4294967295,1],2),([0,1,65536,4294967295],4)]
   tests +=[([rng.randrange(2**32)for _ in range(rng.randrange(65))],None)for _ in range(35)]
   tests +=[([rng.randrange(100)for _ in range(20)],rng.randrange(21))for _ in range(10)]
   for i,(data,count)in enumerate(tests):
    count=len(data)if count is None else count;r=wasm(module,data,count);p=subprocess.run([old,'run',src,json.dumps(data),str(count)],capture_output=True,timeout=10)
    if p.returncode==0:
     v=json.loads(p.stdout);assert r=={'value':v['value'],'status':0,'work':v['steps']},(name,i,r,v)
    else:
     assert r['status']==4,(name,i,r,p.stdout)
    rows.append({'program':name,'case':i,'wasm':r,'baselineCoreExit':p.returncode,'passed':True})
 # Bounds, reset after error, exact wrapping and finite work cap.
 src,module=build('limit',base.replace('LIMIT 65536','LIMIT 2'))
 assert wasm(module,[1,2,3])['status']==17
 assert wasm(module,[1],2)['status']==2
 assert wasm(module,[1],ptr=1)['status']==2
 assert wasm(module,[],words=65537)['status']==2
 assert wasm(module,[],ptr=262144,words=1)['status']==2
 assert wasm(module,[5])['status']==0
 badload=base.replace('index: i','index: count');src,module=build('bounds',badload);assert wasm(module,[1])['status']==16
 many=base.replace('STEP add = ADD WITH { a: total, b: item, result: total }','\n'.join(f'STEP a{i} = ADD WITH {{ a: total, b: 0, result: total }}'for i in range(20)))
 src,module=build('work-cap',many);r=wasm(module,[0]*65536);assert r['status']==18 and r['work']==1048577,r
 # Refused source and output paths do not replace existing bytes or symlink targets.
 invalid=D/'invalid.flow';invalid.write_text('profile RF2_SYSTEM_A64_V1\nfn main(a,b)\nreturn 0\nend\n');out=D/'must-not-exist';assert subprocess.run([C,invalid,out],capture_output=True).returncode!=0 and not out.exists()
 keep=D/'keep';keep.write_bytes(b'keep');assert subprocess.run([C,src,keep],capture_output=True).returncode!=0 and keep.read_bytes()==b'keep'
 link=D/'link';link.symlink_to(keep);assert subprocess.run([C,src,link],capture_output=True).returncode!=0 and keep.read_bytes()==b'keep'
 report={'passed':True,'differentialCases':len(rows),'boundaryCases':11,'seed':190021,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'retainedCoreRuntimeSHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256((R/'native/wasm/backend.rf2').read_bytes()).hexdigest(),'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'observations':rows,'limits':['Bounded RF2 CoreV0 backend, not general systems/WASI/DOM/threads or legacy-browser WASM','Node V8 execution is a development oracle; browser acceptance separately required','One host, no speed, token, energy or Android4.1 hardware claim']};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'differentialCases':len(rows),'report':str(D/'report.json')}))
finally:peer.stdin.close();peer.wait(timeout=5)
