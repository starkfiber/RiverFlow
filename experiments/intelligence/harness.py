"""Project-local developer evidence tools. No inference, network, patching or dispatch."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, math, os, re, stat, statistics, subprocess

MAX_BYTES=1048576
def digest(data): return hashlib.sha256(data).hexdigest()
def read_regular(path,limit=MAX_BYTES):
 fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
 try:
  meta=os.fstat(fd)
  if not stat.S_ISREG(meta.st_mode) or meta.st_size>limit: raise ValueError('Bounded regular file required')
  data=bytearray()
  while len(data)<=limit:
   part=os.read(fd,min(65536,limit+1-len(data)))
   if not part: return bytes(data)
   data.extend(part)
  raise ValueError('File exceeded byte budget')
 finally: os.close(fd)
def unique(pairs):
 out={}
 for key,value in pairs:
  if key in out: raise ValueError('Duplicate JSON key')
  out[key]=value
 return out
def parse(data):
 try: value=json.loads(data,object_pairs_hook=unique,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON')))
 except RecursionError as e:raise ValueError('JSON nesting budget exceeded')from e
 pending=[(value,0)]
 while pending:
  item,depth=pending.pop()
  if depth>32:raise ValueError('JSON nesting budget exceeded')
  if isinstance(item,dict):pending.extend((x,depth+1)for x in item.values())
  elif isinstance(item,list):pending.extend((x,depth+1)for x in item)
 return value
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def relative(name):
 p=PurePosixPath(name)
 if not isinstance(name,str) or not name or p.is_absolute() or '..'in p.parts or '\\'in name: raise ValueError('Relative source path required')
 return p
def inventory(root):
 root=Path(root).resolve(strict=True)
 q=subprocess.run(['git','ls-files','-z','--cached'],cwd=root,capture_output=True,check=True,timeout=10)
 files=[];skipped=[];total=0
 names=[name for name in sorted(set(q.stdout.decode().rstrip('\0').split('\0')))if Path(name).suffix in('.rf2','.flow')]
 if len(names)>1000:raise ValueError('Source file budget exceeded')
 for name in names:
  relative(name)
  try: data=read_regular(root/name)
  except (OSError,ValueError) as e:
   skipped.append(dict(path=name,reason=type(e).__name__));continue
  text=data.decode('utf-8',errors='strict'); lines=text.splitlines()
  total+=len(data)
  if total>8*MAX_BYTES:raise ValueError('Aggregate source byte budget exceeded')
  files.append(dict(path=name,sha256=digest(data),bytes=len(data),lines=len(lines),
   declarations=[dict(line=i+1,text=s[:160])for i,s in enumerate(lines)if re.match(r'^(interrupt )?fn |^FUNCTION ',s)],
   effectLeads=[dict(line=i+1,kind=k)for i,s in enumerate(lines)for k,rx in [('syscall',r'\bsyscall6\('),('raw-memory',r'\b(load|store)(8|32|64)\('),('import',r'^use ')]if re.search(rx,s)]))
 return dict(schema='rf2.source-context.v1',coverage='lexical-only; not a grammar parser or security verdict',files=files,skipped=skipped,automaticFindingCount=None)
def capabilities(binary):
 binary=Path(binary).resolve(strict=True); identity=digest(read_regular(binary,67108864))
 status=subprocess.run([str(binary),'status'],capture_output=True,check=True,timeout=5)
 requests=[dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='rf2-intelligence',version='1'))),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list',params={})]
 q=subprocess.run([str(binary),'mcp'],input=b''.join(canonical(x)+b'\n'for x in requests),capture_output=True,check=True,timeout=5)
 if len(q.stdout)>MAX_BYTES or len(status.stdout)>65536:raise ValueError('Runtime reply budget exceeded')
 replies=[parse(x)for x in q.stdout.splitlines()]
 if len(replies)!=2 or [x.get('id')for x in replies]!=[1,2]:raise ValueError('Unexpected MCP discovery replies')
 tools=replies[1].get('result',{}).get('tools')
 if not isinstance(tools,list) or not tools:raise ValueError('No discovered tools')
 return dict(schema='rf2.capabilities-context.v1',runtimeSHA256=identity,status=parse(status.stdout),tools=tools,
  authority='Only observed runtime schemas. This manifest grants no new effects and has no embedded model.')
def review_gate(root,manifest,response):
 if manifest.get('schema')!='rf2.source-context.v1':raise ValueError('Wrong context schema')
 if not isinstance(manifest.get('files'),list)or len(manifest['files'])>1000:raise ValueError('Context file bound')
 sources={}
 for f in manifest['files']:
  name=f['path'];relative(name)
  if name in sources:raise ValueError('Duplicate context path')
  data=read_regular(Path(root)/name)
  if digest(data)!=f['sha256'] or len(data.decode('utf-8').splitlines())!=f['lines']:raise ValueError('Source context drift')
  sources[name]=f
 if not isinstance(response,dict)or not isinstance(response.get('choices'),list)or len(response['choices'])!=1:raise ValueError('One provider choice required')
 choice=response['choices'][0]
 if not isinstance(choice,dict)or not isinstance(choice.get('message'),dict):raise ValueError('Provider message required')
 if choice.get('finish_reason')!='stop':raise ValueError('Incomplete provider output')
 content=choice.get('message',{}).get('content')
 if not isinstance(content,str)or len(content.encode())>65536:raise ValueError('Model content budget')
 body=parse(content)
 if not isinstance(body,dict)or set(body)!={'schema','contextSHA256','findings'}or body['schema']!='rf2.review-proposals.v1':raise ValueError('Review schema required')
 if body['contextSHA256']!=digest(canonical(manifest)):raise ValueError('Wrong context identity')
 if not isinstance(body['findings'],list)or len(body['findings'])>20:raise ValueError('Finding bound')
 for f in body['findings']:
  if not isinstance(f,dict)or set(f)!={'path','line','sourceSHA256','hypothesis','nextTest'}:raise ValueError('Finding schema required')
  if f['path']not in sources:raise ValueError('Unknown source reference')
  source=sources[f['path']]
  if type(f['line'])is not int or not 1<=f['line']<=source['lines']or f['sourceSHA256']!=source['sha256']:raise ValueError('Invalid source reference')
  for key in ('hypothesis','nextTest'):
   if not isinstance(f[key],str)or not 1<=len(f[key].strip())<=2000:raise ValueError('Bounded explanation required')
 return dict(schema='rf2.review-gate.v1',state='reviewable-proposals-only',findings=body['findings'],sourceBound=True,
  patchesApplied=0,commandsExecuted=0,securityVerified=False,contextSHA256=body['contextSHA256'])
def select_build(measurements):
 # Advisory only: accepts matched paired rows, never compiler commands or paths.
 if not isinstance(measurements.get('workloads'),list)or not 1<=len(measurements['workloads'])<=20:raise ValueError('Workload bound')
 rows=[]
 for w in measurements['workloads']:
  pairs=w.get('rows')
  if not isinstance(pairs,list)or not 5<=len(pairs)<=100:raise ValueError('Five through 100 matched trials required')
  clean=[];cached=[]
  for pair in pairs:
   a,b=pair['clean'],pair['cache']
   if not isinstance(a.get('sha256'),str)or not re.fullmatch('[0-9a-f]{64}',a['sha256'])or a['sha256']!=b['sha256']:raise ValueError('Matched byte identities required')
   for item in(a,b):
    x=item['ms']
    if type(x)not in(int,float)or not math.isfinite(x)or x<=0:raise ValueError('Positive finite time required')
   clean.append(a['ms']);cached.append(b['ms'])
  ratio=statistics.median(cached)/statistics.median(clean);wins=sum(b<a for a,b in zip(clean,cached))/len(clean)
  rows.append(dict(trials=len(pairs),cleanMedianMs=statistics.median(clean),cacheMedianMs=statistics.median(cached),cacheToCleanRatio=ratio,pairedCacheWinFraction=wins,
   recommendedRoute='explicit-reuse-candidate'if ratio<=.9 and wins>=.8 else'clean',reason='Require >=10% median advantage and >=80% paired wins; no dispatch or universal speed claim'))
 return dict(schema='rf2.build-advice.v1',advisoryOnly=True,workloads=rows)
def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='action',required=True)
 a=s.add_parser('inventory');a.add_argument('root')
 a=s.add_parser('capabilities');a.add_argument('runtime')
 a=s.add_parser('review');a.add_argument('root');a.add_argument('manifest');a.add_argument('response')
 a=s.add_parser('select-build');a.add_argument('measurements')
 args=p.parse_args()
 try:
  if args.action=='inventory':out=inventory(args.root)
  elif args.action=='capabilities':out=capabilities(args.runtime)
  elif args.action=='review':out=review_gate(args.root,parse(read_regular(args.manifest)),parse(read_regular(args.response)))
  else:out=select_build(parse(read_regular(args.measurements)))
  print(json.dumps(out,indent=2))
 except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as e:p.exit(2,'RF2 intelligence: '+str(e)+'\n')
if __name__=='__main__':main()
