"""Additional bounded key-type, rotation and malformed stdio probes. Disposable keys only."""
from pathlib import Path
import subprocess,tempfile,os,socket,select,json,random,time,hashlib
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_TRUST_DIR',R/'output/trust-0.18'));D=R/'artifacts/trust-0.18'/('protocol-keys-'+str(time.time_ns()));D.mkdir(parents=True);rows=[]
def check(name,ok):assert ok,name;rows.append({'name':name,'passed':True})
def run(args):return subprocess.run([str(B/'rf2-trust'),*map(str,args)],capture_output=True,timeout=3)
with tempfile.TemporaryDirectory(prefix='rf2-keys-')as tmp:
 d=Path(tmp);key=d/'key';check('keygen',run(['keygen',key]).returncode==0);pf=d/'plan';pf.write_text('RF2E1 allow 7 budget 2 input 1 4 steps 1 xor 1\n')
 for name,maker in [('directory',lambda p:p.mkdir()),('fifo',lambda p:os.mkfifo(p,0o600)),('symlink',lambda p:p.symlink_to(key)),('short',lambda p:p.write_bytes(b'x'*31)),('long',lambda p:p.write_bytes(b'x'*33))]:
  path=d/name;maker(path)
  if name in ['short','long']:path.chmod(0o600)
  q=run(['issue',path,pf]);check('reject '+name,q.returncode!=0 and q.stdout==b'{"error":"key-policy"}\n')
 path=d/'socket';sock=socket.socket(socket.AF_UNIX);sock.bind(str(path));q=run(['issue',path,pf]);check('reject unix socket',q.returncode!=0);sock.close()
 for mode in [0o000,0o400,0o640,0o644,0o666,0o700]:
  key.chmod(mode);check('reject mode '+oct(mode),run(['issue',key,pf]).returncode!=0)
 key.chmod(0o600);cap=run(['issue',key,pf]).stdout;capsule=d/'capsule';capsule.write_bytes(cap);other=d/'other';run(['keygen',other]);check('different key rejects',run(['verify',other,capsule]).returncode!=0);check('original key accepts',run(['verify',key,capsule]).returncode==0)
 p=subprocess.Popen([str(B/'rf2-trust'),'mcp',str(key)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/nonexistent'})
 def send(raw):
  p.stdin.write(raw+b'\n');p.stdin.flush();assert select.select([p.stdout],[],[],3)[0],'stdio timeout';b=p.stdout.readline();assert b,'server died';return json.loads(b)
 def rpc(method,params=None):
  x={'jsonrpc':'2.0','id':17,'method':method}
  if params is not None:x['params']=params
  return send(json.dumps(x).encode())
 check('init','result'in rpc('initialize',{'protocolVersion':'2024-11-05'}));p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');p.stdin.flush()
 rng=random.Random(180019)
 packets=[b'[]',b'null',b'123',b'"text"',b'{"jsonrpc":"2.0","id":{},"method":"ping"}',b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"contract_status","arguments":[]}}',b'{"jsonrpc":"2.0","id":1,"method":"tools/list","method":"ping"}',b'{"jsonrpc":"2.0","id":1,"method":"tools\\u002flist","metho\\u0064":"ping"}',b'\xff',b'\xc0\xaf',b'{'*300,b'X'*65537,b'X'*1048577]
 packets +=[b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":'+bytes(rng.randrange(1,256)for _ in range(rng.randrange(1,256))).replace(b'\n',b'x')for _ in range(100)]
 for i,raw in enumerate(packets):
  check('malformed refusal '+str(i),'error'in send(raw));check('recovery '+str(i),'result'in rpc('tools/call',{'name':'contract_status','arguments':{}}))
 # Running process intentionally pins an administrator key; file rotation takes effect on restart.
 key.write_bytes(other.read_bytes());key.chmod(0o600)
 result=rpc('tools/call',{'name':'contract_run','arguments':{'plan':pf.read_text()}});capsule.write_text(result['result']['structuredContent']['capsule']);check('existing session retains original key',run(['verify',key,capsule]).returncode!=0)
 p.stdin.close();p.wait(timeout=3);check('clean EOF',p.returncode==0 and not p.stderr.read())
 check('restart loads rotated key',run(['issue',key,pf]).stdout!=cap)
report={'passed':True,'checks':len(rows),'seed':180019,'controllerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':rows,'limits':['Bounded cases, not proof against arbitrary peers or local same-user compromise','Key snapshot per process; administrator rotation requires restart; no replay rejection','No key bytes retained in this report; test directory removed']};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(rows),'report':str(D/'report.json')}))
