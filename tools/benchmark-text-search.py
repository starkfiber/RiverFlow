"""Complete native text-search CLI tasks against libc and Python bytes baselines.
Developer tools are not RF2 user dependencies. Run after correctness qualification.
"""
from pathlib import Path
import hashlib,json,os,platform,random,statistics,subprocess,time
R=Path(__file__).resolve().parents[1];RF=Path(os.environ['RF2_SEARCH_BINARY']).resolve();D=R/'artifacts/text-search'/('bench-'+str(time.time_ns()));D.mkdir(parents=True)
N=int(os.environ.get('RF2_BENCH_TRIALS','21'));assert 5<=N<=101
c=R/'tests/comparators/text_search.c';CB=D/'libc-search';subprocess.run(['/usr/bin/clang','-O3','-Wall','-Wextra',str(c),'-o',str(CB)],check=True)
py=D/'search.py';py.write_text('''import sys,json
b=sys.stdin.buffer.read(1048577)
if len(b)>1048576:sys.exit(4)
q=sys.argv[1].encode();start=0;count=0;first=b.find(q)
if not q:count=len(b)+1
else:
 while start<=len(b):
  i=b.find(q,start)
  if i<0:break
  count+=1;start=i+(1 if len(sys.argv)==3 else len(q))
print(json.dumps(dict(bytes=len(b),query_bytes=len(q),matches=count,first_byte=None if first<0 else first)))
''')
rows=[];tasks=[('short',b'a note on native tools\n'*12,'native',False),('document-64k',(b'The river flows through the native compiler.\n'*1600)[:65536],'native',False),('no-match-1m',b'x'*1048576,'missing',False),('overlap-64k',b'a'*65536,'aaa',True),('periodic-1m',b'a'*1048576,'a'*63+'b',False)]
commands={'RF2':[str(RF)],'C libc':[''+str(CB)],'Python bytes':['/usr/bin/python3',str(py)]}
candidate=os.environ.get('RF2_SEARCH_CANDIDATE')
if candidate:commands['RF2 candidate']=[str(Path(candidate).resolve())]
for name,data,query,overlap in tasks:
 count=(len(data)+1)if not query else sum(data.startswith(query.encode(),i)for i in range(len(data)+1))if overlap else data.count(query.encode())
 expected=dict(bytes=len(data),query_bytes=len(query.encode()),matches=count,first_byte=None if data.find(query.encode())<0 else data.find(query.encode()))
 for trial in range(N):
  order=list(commands);random.Random(3100+trial).shuffle(order)
  for route in order:
   args=commands[route]+[query]+(['--overlap']if overlap else[]);start=time.perf_counter_ns();q=subprocess.run(args,input=data,capture_output=True,timeout=15);ms=(time.perf_counter_ns()-start)/1e6
   assert q.returncode==0,(name,route,q.stderr);assert json.loads(q.stdout)==expected,(name,route,q.stdout,expected)
   rows.append(dict(task=name,trial=trial,route=route,ms=ms))
summary=[dict(task=n,medianMs={k:statistics.median(x['ms']for x in rows if x['task']==n and x['route']==k)for k in commands})for n,*_ in tasks]
report=dict(passed=True,trials=N,summary=summary,raw=rows,inputs={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),query=q,overlap=o)for n,b,q,o in tasks},binarySHA256=hashlib.sha256(RF.read_bytes()).hexdigest(),candidateSHA256=hashlib.sha256(Path(candidate).read_bytes()).hexdigest()if candidate else None,cSourceSHA256=hashlib.sha256(c.read_bytes()).hexdigest(),pythonSource=py.read_text(),compilerVersion=subprocess.check_output(['/usr/bin/clang','--version'],text=True),pythonVersion=subprocess.check_output(['/usr/bin/python3','--version'],text=True),host=platform.platform(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits='One Mac; complete processes including input/output and startup. libc memmem and Python bytes.find are optimized library comparators, not identical implementations. No AI usage, energy, other-host or universal result.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),summary=summary)))
