"""Bounded loopback comparison. Measures this implementation/deployment, not languages in general."""
from pathlib import Path
import socket,time,json,hashlib,random,statistics,platform,concurrent.futures,subprocess,os
R=Path(__file__).resolve().parents[1];D=R/'artifacts/virtual-lab';rows=[];checks=[];ports=[int(os.environ.get("RF2_STACK_RF2_PORT","18780")),18781,18782];rng=random.Random(180013)
def request(port,path='/',raw=None):
 start=time.perf_counter_ns()
 with socket.create_connection(('127.0.0.1',port),timeout=3)as s:
  s.settimeout(3);s.sendall(raw or f'GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n'.encode());chunks=[]
  while True:
   b=s.recv(65536)
   if not b:break
   chunks.append(b)
 out=b''.join(chunks);head,body=out.split(b'\r\n\r\n',1);status=int(head.split(b' ')[1]);headers=dict(x.lower().split(b': ',1)for x in head.split(b'\r\n')[1:]);assert int(headers[b'content-length'])==len(body)
 return status,body,(time.perf_counter_ns()-start)/1e6
def oracle(n):
 state=1;total=0
 for _ in range(n):state=(state*1664525+1013904223)&0xffffffff;total+=state
 return (json.dumps({'iterations':n,'checksum':total,'state':state},separators=(',',':'))+'\n').encode()
identities={str(port):json.loads(request(port,'/api/info')[1])for port in ports}
site=(R/'examples/stack-lab/index.html').read_bytes();expected={'/':site,'/health':b'{"ok":true}\n'}
for n in [0,1,10,10000,100000]:expected[f'/api/compute?iterations={n}']=oracle(n)
for port in ports:
 for path,body in expected.items():
  status,actual,_=request(port,path);assert status==200 and actual==body,(port,path,status,actual);checks.append({'port':port,'path':path,'passed':True,'bodySHA256':hashlib.sha256(actual).hexdigest()})
 malformed=[('GET /health HTTP/1.1\r\nHost: x\r\nHost: y\r\n\r\n',400),('GET /health HTTP/1.1\r\n\r\n',400),('GET /health HTTP/1.1\r\nHost: x\r\nContent-Length: 1\r\n\r\nx',400),('GET /health HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n',400),('GET /health HTTP/1.1\r\nHost: x\r\nContent-Length: 0\r\nContent-Length: 0\r\n\r\n',400)]
 for i,(raw,status)in enumerate(malformed):assert request(port,raw=raw.encode())[0]==status;checks.append({'port':port,'malformed':i,'passed':True})
 for v in ['','01','-1','100001','9999999','a','1&x=2','1%30']:
  assert request(port,'/api/compute?iterations='+v)[0]==400;checks.append({'port':port,'invalidIterations':v,'passed':True})
 assert request(port,'/missing')[0]==404
 assert request(port,raw=b'POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 0\r\n\r\n')[0]==405
 for _ in range(20):
  s=socket.create_connection(('127.0.0.1',port),timeout=3);s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n');s.close()
 assert request(port,'/health')[0]==200;checks.append({'port':port,'disconnectRecovery':20,'passed':True})
# 15 interleaved rounds;20 requests per cell;2 routes,2 concurrency levels,3 arms=3600 requests.
cells=[(p,path,c)for p in ports for path in ['/','/api/compute?iterations=10000']for c in [1,4]]
trials=int(os.environ.get('RF2_STACK_TRIALS','15'));batch=int(os.environ.get('RF2_STACK_BATCH','20'));assert 1<=trials<=15 and 1<=batch<=20
for trial in range(trials):
 rng.shuffle(cells)
 for port,path,c in cells:
  start=time.perf_counter_ns()
  with concurrent.futures.ThreadPoolExecutor(max_workers=c)as pool:r=list(pool.map(lambda _:request(port,path),range(batch)))
  seconds=(time.perf_counter_ns()-start)/1e9
  assert all(status==200 and body==expected[path]for status,body,_ in r)
  rows.append({'trial':trial,'port':port,'path':path,'concurrency':c,'milliseconds':[x[2]for x in r],'batchSeconds':seconds,'requestsPerSecond':batch/seconds})
summary=[]
for port,path,c in cells:
 group=[x for x in rows if(x['port'],x['path'],x['concurrency'])==(port,path,c)];lat=[v for x in group for v in x['milliseconds']];summary.append({'port':port,'path':path,'concurrency':c,'requests':len(lat),'medianMs':statistics.median(lat),'p95Ms':sorted(lat)[int(.95*(len(lat)-1))],'medianBatchRequestsPerSecond':statistics.median(x['requestsPerSecond']for x in group)})
report={'date':'2026-11-13','passed':True,'machine':platform.platform(),'backends':identities,'seed':180013,'checks':checks,'trialsPerCell':trials,'requestsPerBatch':batch,'requestsMeasured':sum(len(x['milliseconds'])for x in rows),'summary':summary,'samples':rows,'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (R/'examples/stack-lab').glob('*')if p.is_file()},'limits':['Single physical host, single-worker bounded HTTP subset, loopback; not internet capacity','Host-Python control isolates some VM cost, not all implementation/runtime/OS differences','Guest is QEMU/HVF Linux with user-mode network forwarding; RF2 launches backend, not a new hypervisor','HTTP latency includes socket/client overhead; no compiler-wide/energy/token/transistor claims','Malformed probes are a bounded subset, not complete HTTP conformance or security proof']};Path(os.environ.get('RF2_STACK_REPORT',str(D/'comparison.json'))).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks),'requestsMeasured':report['requestsMeasured'],'summary':summary},indent=2))
