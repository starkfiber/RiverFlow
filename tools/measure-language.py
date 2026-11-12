"""Matched executed native kernels, complete MCP exchanges, and exact source encodings."""
from pathlib import Path
import subprocess,json,tempfile,random,time,statistics,hashlib,os,sys,re
import tiktoken
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tests/standalone'));from invoice_verify import Peer,value
C=Path(os.environ.get('RF2_TEST_COMPILER',R/'output/native-compiler/rf2c'));OLD_C=Path(os.environ.get('RF2_BASELINE_COMPILER',R/'output/package/rf2-0.9.0/rf2c'));B=R/'output/native-0.10-final/rf2';OLD=R/'output/package/rf2-0.9.0/rf2'
if not OLD.exists():OLD=R/'output/native-0.9/rf2'
report={'schema':'rf2.language.measurement.v1','compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'runtimeSHA256':hashlib.sha256(B.read_bytes()).hexdigest(),'baseline09SHA256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'scope':'One host. Fresh-process wall time includes launch. Repeated kernels retain actual checksums. Optional optimiser compared with frozen 0.9 for identical scalar source. Token counts encode retained exchanges, not provider bills or AI task success.','raw':[],'kernels':[]}
with tempfile.TemporaryDirectory(prefix='rf2-lang-bench-')as tmp:
 d=Path(tmp)
 kernels={'accumulate':'set checksum = checksum + (i & 255)\n set i = i + 1','mix':'set checksum = ((checksum ^ i) * 33 + 17) & 4294967295\n set i = i + 1','branches':'if (i & 3) == 0\n set checksum = checksum + 7\n else\n set checksum = checksum + (i & 31)\n end\n set i = i + 1'}
 for name,body in kernels.items():
  source='profile RF2_SYSTEM_A64_V1\n'+(R/'examples/workload/lib/io.rf2').read_text().split('\n',1)[1]+'fn main(argc,argv)\n let i = 0\n let checksum = 0\n while i < 2000000\n '+body+'\n end\n do io_number(checksum)\n do io_print("\\n")\n return 0\nend\n';src=d/(name+'.rf2');src.write_text(source);variants={}
  for version,compiler,opt in [('09',OLD_C,False),('10-default',C,False),('10-opt',C,True)]:
   out=d/(name+version);t=time.perf_counter_ns();r=subprocess.run([compiler,src,out]+(['--opt']if opt else[]),capture_output=True);compile_ns=time.perf_counter_ns()-t;assert r.returncode==0,r.stderr;subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);variants[version]=out;report['raw'].append({'kernel':name,'variant':version,'compileMs':compile_ns/1e6,'executableBytes':out.stat().st_size})
  cbody={'accumulate':'checksum += i & 255;', 'mix':'checksum = ((checksum ^ i) * 33 + 17) & 4294967295ULL;', 'branches':'if ((i & 3) == 0) checksum += 7; else checksum += i & 31;'}[name]
  csrc=d/(name+'.c');csrc.write_text('#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\nint main(int argc,char **argv){uint64_t n=strtoull(argv[1],0,10),checksum=0;for(uint64_t i=0;i<n;i++){'+cbody+'}printf("%llu\\n",(unsigned long long)checksum);return 0;}')
  cout=d/(name+'-c');subprocess.run(['/usr/bin/clang','-O2',csrc,'-o',cout],check=True,capture_output=True)
  pysrc=d/(name+'.py');pybody={'accumulate':'checksum += i & 255','mix':'checksum = ((checksum ^ i) * 33 + 17) & 4294967295','branches':'checksum += 7 if (i & 3) == 0 else i & 31'}[name];pysrc.write_text('checksum=0\nfor i in range(2000000):\n '+pybody+'\nprint(checksum)\n')
  extra={'clang-O2':[str(cout),'2000000'],'python-reference':[sys.executable,str(pysrc)]}
  expected=0
  for i in range(2000000):
   if name=='accumulate':expected+=i&255
   elif name=='mix':expected=((expected^i)*33+17)&4294967295
   else:expected+=7 if i&3==0 else i&31
  for path in variants.values():assert int(subprocess.check_output([path]))==expected
  for cmd in extra.values():assert int(subprocess.check_output(cmd))==expected
  commands={v:[str(p)]for v,p in variants.items()};commands.update(extra);times={v:[]for v in commands}
  for trial in range(9):
   order=list(commands);random.Random(trial+19).shuffle(order)
   for version in order:
    t=time.perf_counter_ns();got=subprocess.check_output(commands[version]);elapsed=time.perf_counter_ns()-t;assert int(got)==expected;times[version].append(elapsed/1e6);report['raw'].append({'kernel':name,'trial':trial,'variant':version,'elapsedMs':elapsed/1e6,'checksum':expected})
  report['kernels'].append({'name':name,'iterations':2000000,'checksum':expected,'medianMs':{v:statistics.median(x)for v,x in times.items()}})
 # Actual non-invoice Core workload through standard or opt-in compact MCP.
 peers={'09':Peer([OLD,'mcp']),'10':Peer([B,'mcp']),'10-compact':Peer([B,'mcp','--compact'])};transcripts={v:[]for v in peers};catalog=None;timings={v:[]for v in peers};source='rf2 v1 checked\nbits input';data=[i for i in range(64)];expected=sum(x.bit_count()for x in data)
 for name,p in peers.items():
  init={'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'matched-measurement','version':'1'}};ans=p.request('initialize',init);transcripts[name]+=[{'method':'initialize','params':init},ans];p.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');p.p.stdin.flush();tools=p.request('tools/list',{});transcripts[name]+=[{'method':'tools/list','params':{}},tools]
  if catalog is None:catalog=tools['result']
  else:assert tools['result']==catalog
 args={'source':source,'data':data}
 for i in range(100):
  order=list(peers);random.Random(i+10).shuffle(order)
  for name in order:
   p=peers[name];t=time.perf_counter_ns();ans=p.call('rf2_run',args);elapsed=time.perf_counter_ns()-t;assert value(ans)['value']==expected;timings[name].append(elapsed/1000);transcripts[name]+=[{'method':'tools/call','params':{'name':'rf2_run','arguments':args}},ans]
 for name,p in peers.items():
  bad={'source':'rf2 v1 checked\nsum input','data':[4294967295,1]};ans=p.call('rf2_run',bad);assert ans['result']['isError'];transcripts[name]+=[{'method':'tools/call','params':{'name':'rf2_run','arguments':bad}},ans];p.close()
 token_counts={encoding:{name:len(tiktoken.get_encoding(encoding).encode(json.dumps(text,separators=(',',':'))))for name,text in transcripts.items()}for encoding in ['o200k_base','cl100k_base']}
 report['mcp']={'source':source,'inputWords':len(data),'calls':100,'expected':expected,'medianUs':{name:statistics.median(x)for name,x in timings.items()},'rawUs':timings,'catalogByteIdentical':True,'tokens':token_counts,'compactScope':'Only successful check/run readable summaries omitted by explicit --compact. Complete structured results, schemas and errors retained. Lowered source and other tools unchanged.'}
 (R/'docs/LANGUAGE-TOKEN-FIXTURES-0.10.json').write_text(json.dumps(transcripts,separators=(',',':'))+'\n')
 # Exact authoring source, whole bundle and consumer only; not inferred model tokens.
 main=(R/'examples/workload/main.rf2').read_text();bundle='\n'.join(p.read_text()for p in sorted((R/'examples/workload').rglob('*.rf2')))
 report['sourceTokens']={encoding:{'main':len(tiktoken.get_encoding(encoding).encode(main)),'bundle':len(tiktoken.get_encoding(encoding).encode(bundle))}for encoding in ['o200k_base','cl100k_base']}
(R/'docs/LANGUAGE-MEASUREMENTS-0.10.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['kernels','mcp','sourceTokens']},indent=2))
