"""Black-box native app tests and independent hashlib/input-state oracles."""
from pathlib import Path
import hashlib,json,os,struct,subprocess,tempfile
R=Path(__file__).resolve().parent
EXE=Path(os.environ.get('DOCUMENT_AUDIT_BIN',str(R/'artifacts/document-audit'))).resolve()
OUT=Path(os.environ.get('RF2_TEST_ARTIFACTS', R/'artifacts'))
OUT.mkdir(parents=True,exist_ok=True)
if not EXE.is_file():raise SystemExit('Build the native app first and set DOCUMENT_AUDIT_BIN to its executable path.')
D=Path(tempfile.mkdtemp(prefix='document-audit-',dir=OUT))
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 (D/'RESULTS.json').write_text(json.dumps(dict(checks=checks,allPassed=all(x['passed']for x in checks)),indent=2)+'\n')
 if not ok:raise AssertionError((name,detail,D))
def call(*args):return subprocess.run([str(EXE),*map(str,args)],cwd=D,capture_output=True,timeout=8)
def snapshot(paths):
 h=hashlib.sha256();h.update(b'RF2-DOCUMENT-AUDIT-V1')
 for p in paths:
  raw=(D/p).read_bytes();name=p.encode();h.update(struct.pack('<Q',len(name)));h.update(name);h.update(struct.pack('<Q',len(raw)));h.update(hashlib.sha256(raw).digest())
 return h.hexdigest()
def manifest(paths,ending='\n'):
 (D/'files.txt').write_bytes(ending.join(paths).encode()+ending.encode());return D/'files.txt'
paths=['alpha.txt','tamil.txt','empty.txt'];contents=[b'banana banana\nSecond line.\n','வணக்கம் தமிழ்\nbanana'.encode(),b'']
for p,data in zip(paths,contents):(D/p).write_bytes(data)
m=manifest(paths);originals={p:(D/p).read_bytes()for p in paths};manifest_original=m.read_bytes()
p=call('catalog',m);check('catalog native success',p.returncode==0,p.stderr.decode());result=json.loads(p.stdout)
check('versioned CLI wire schema',result.get('schema')=='rf2.document-audit.v2')
check('document and byte counts',result['documents']==3 and result['bytes']==sum(map(len,contents)))
check('independent framed corpus SHA256',result['corpus_sha256']==snapshot(paths),result['corpus_sha256'])
for i,row in enumerate(result['items']):check('per-file SHA256 '+str(i),row['sha256']==hashlib.sha256(contents[i]).hexdigest()and row['path']==paths[i]and row['bytes']==len(contents[i]))
p=call('check',m,result['corpus_sha256']);check('baseline check succeeds',p.returncode==0)
before=set(D.iterdir());p=call('search',m,'ana');search=json.loads(p.stdout);search_json=p.stdout
check('search native success',p.returncode==0)
for i,row in enumerate(search['items']):
 check('nonoverlap exact-byte search '+str(i),row['matches']==contents[i].count(b'ana'))
 check('v2 nullable first byte offset '+str(i),row['first_byte']==(contents[i].find(b'ana')if b'ana'in contents[i]else None))
check('queries do not create files',set(D.iterdir())==before)
check('original document bytes untouched',all((D/p).read_bytes()==v for p,v in originals.items()))
check('original manifest untouched',m.read_bytes()==manifest_original)
node=os.environ.get('DOCUMENT_AUDIT_NODE')
javascript=None
if node:
 p=subprocess.run([node,str(R/'test-wire.mjs')],input=search_json,capture_output=True,timeout=8)
 check('JavaScript v2 parse/roundtrip and absent control',p.returncode==0,p.stderr.decode())
 javascript=dict(runtimeSHA256=hashlib.sha256(Path(node).read_bytes()).hexdigest(),report=json.loads(p.stdout))
for query in ['தமிழ்','not present','x'*128]:
 p=call('search',m,query);check('valid query '+query[:12],p.returncode==0,p.stderr.decode())
p=call('search',m,'x'*129);check('query bound rejects without stdout',p.returncode!=0 and not p.stdout)
p=call('search',m,'');check('empty query refuses',p.returncode!=0)
p=call('check',m,'A'*64);check('noncanonical digest refuses',p.returncode!=0 and b'22'in p.stderr)
(D/'alpha.txt').write_bytes(contents[0]+b'changed');p=call('check',m,result['corpus_sha256']);check('changed content detected',p.returncode!=0 and b'409'in p.stderr and not p.stdout)
(D/'alpha.txt').write_bytes(contents[0]);p=call('catalog',manifest(list(reversed(paths))));check('order identity matters',json.loads(p.stdout)['corpus_sha256']!=result['corpus_sha256'])
p=call('catalog',manifest(paths,'\r\n'));check('CRLF manifest admits',p.returncode==0)
for title,data,error in [('duplicate','alpha.txt\nalpha.txt\n',17),('blank','alpha.txt\n\n',22),('missing','absent.txt\n',2),('empty','',84),('bad-utf8','\udcff',84)]:
 raw=data.encode(errors='surrogateescape');m.write_bytes(raw);p=call('catalog',m);check(title+' refusal',p.returncode!=0 and ('"error":'+str(error)).encode()in p.stderr and not p.stdout,p.stderr.decode())
(D/'invalid.txt').write_bytes(b'\xff');m.write_text('invalid.txt\n');p=call('catalog',m);check('invalid document UTF8 refuses',p.returncode!=0 and not p.stdout)
(D/'link.txt').symlink_to(D/'alpha.txt');m.write_text('link.txt\n');p=call('catalog',m);check('symlink document refuses',p.returncode!=0 and not p.stdout)
(D/'big.txt').write_bytes(b'x'*65537);m.write_text('big.txt\n');p=call('catalog',m);check('65537-byte document refuses',p.returncode!=0 and not p.stdout)
(D/'big.txt').write_bytes(b'x'*65536);p=call('catalog',m);check('65536-byte document accepted',p.returncode==0)
many=[]
for i in range(65):
 name='small'+str(i)+'.txt';(D/name).write_bytes(b'x');many.append(name)
p=call('catalog',manifest(many[:64]));check('64 documents accepted',p.returncode==0 and json.loads(p.stdout)['documents']==64)
p=call('catalog',manifest(many));check('65 documents refused',p.returncode!=0 and not p.stdout)
# Bounded stdio protocol with the launch-selected same corpus implementation.
m=manifest(paths)
messages=[dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2025-11-25',capabilities={},clientInfo=dict(name='native-oracle',version='1'))),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/call',params=dict(name='audit_snapshot',arguments={})),dict(jsonrpc='2.0',id=3,method='tools/call',params=dict(name='audit_snapshot',arguments={'path':'absent.txt'}))]
p=subprocess.run([str(EXE),'mcp',str(m)],cwd=D,input=('\n'.join(json.dumps(x)for x in messages)+'\n').encode(),capture_output=True,timeout=8)
responses=[json.loads(x)for x in p.stdout.splitlines()];byid={x.get('id'):x for x in responses}
check('MCP finite stream completes',p.returncode==0,p.stderr.decode())
check('MCP exposes same current corpus',byid[2]['result']['structuredContent']['corpus_sha256']==snapshot(paths),byid[2])
check('versioned MCP wire schema',byid[2]['result']['structuredContent'].get('schema')=='rf2.document-audit.v2')
check('MCP path argument refused',byid[3].get('error',{}).get('code')==-32602,byid[3])
# Harder epoch: valid maximal inputs must still have a bounded agent summary.
long=D/'long';long.mkdir();long_names=[];working=Path.cwd()
try:
 os.chdir(long)
 for i in range(32):
  name=Path('a'+'"'*249)/('b'+'"'*249)/('c'+'"'*249)/(f'f{i:02d}'+'"'*242+'.txt')
  name.parent.mkdir(parents=True,exist_ok=True);name.write_bytes(b'x');long_names.append(str(name))
 (long/'files.txt').write_text('\n'.join(long_names)+'\n')
finally:os.chdir(working)
p=subprocess.run([str(EXE),'catalog','files.txt'],cwd=long,capture_output=True,timeout=8);check('long escaped catalog remains available',p.returncode==0 and len(p.stdout)>65536)
long_result=json.loads(p.stdout)
p=subprocess.run([str(EXE),'mcp','files.txt'],cwd=long,input=('\n'.join(json.dumps(x)for x in messages[:3])+'\n').encode(),capture_output=True,timeout=8)
responses=[json.loads(x)for x in p.stdout.splitlines()];byid={x.get('id'):x for x in responses}
check('long corpus MCP summary succeeds',byid[2]['result'].get('isError')is False,byid[2])
check('long corpus summary fingerprint agrees with CLI',byid[2]['result']['structuredContent']['corpus_sha256']==long_result['corpus_sha256'])
check('long corpus summary names CLI index',byid[2]['result']['structuredContent'].get('index_via_cli')is True)
check('long corpus summary stays bounded',len(p.stdout)<1024,len(p.stdout))
large=[]
for i in range(17):
 name='large'+str(i)+'.txt';(D/name).write_bytes(b'x'*65536);large.append(name)
p=call('catalog',manifest(large[:16]));check('exact 1MiB corpus accepted',p.returncode==0 and json.loads(p.stdout)['bytes']==1048576)
p=call('catalog',manifest(large));check('over 1MiB refuses without partial stdout',p.returncode!=0 and not p.stdout)
m=manifest(paths)
process=subprocess.Popen([str(EXE),'mcp',str(m)],cwd=D,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
 process.stdin.write((json.dumps(messages[0])+'\n'+json.dumps(messages[1])+'\n'+json.dumps(messages[2])+'\n').encode());process.stdin.flush()
 first=json.loads(process.stdout.readline());second=json.loads(process.stdout.readline());check('live MCP initial fresh snapshot',second['result']['isError']is False)
 (D/'alpha.txt').unlink()
 message=dict(messages[2],id=9);process.stdin.write((json.dumps(message)+'\n').encode());process.stdin.flush();changed=json.loads(process.stdout.readline())
 check('live MCP missing source returns tool error',changed['id']==9 and changed['result']['isError']is True,changed)
 check('live MCP missing source has no stale structured snapshot','structuredContent'not in changed['result'])
 process.stdin.close();process.wait(timeout=8)
finally:
 if process.poll()is None:process.kill();process.wait()
report=dict(schema='rf2.document-audit.tests.v2',wireSchema='rf2.document-audit.v2',binarySHA256=hashlib.sha256(EXE.read_bytes()).hexdigest(),checks=checks,count=len(checks),allPassed=all(x['passed']for x in checks),javascript=javascript,scope='One native Mac ARM64 process family; controlled text files and stdio. No human trial, model token or hardware claim.')
(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(directory=str(D),checks=len(checks),allPassed=report['allPassed'])))
