from pathlib import Path
import os
import subprocess,json,hashlib
D=Path(os.environ['RF2_SHIP_EVIDENCE']);b=Path('/Users/ik/Projects/RiverFlow/output/bin/rf2');s=Path('examples/sum.flow').read_text()
requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'local-mmio-smoke','version':'1'}}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list'},{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'rf2_run','arguments':{'source':s,'data':[3,4,5]}}},{'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'rf2_run','arguments':{'source':'profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n return popcount64(255)\nend','data':[]}}}]
requests.append({'jsonrpc':'2.0','id':5,'method':'tools/call','params':{'name':'rf2_status','arguments':{}}})
p=subprocess.run([str(b),'mcp'],input=''.join(json.dumps(r)+'\n' for r in requests),capture_output=True,text=True,timeout=10)
rows=[json.loads(l) for l in p.stdout.splitlines()];byid={r['id']:r for r in rows};names=[t['name'] for t in byid[2]['result']['tools']];assert len(names)==9
assert byid[3]['result']['structuredContent']['value']==12
assert 'error' in byid[4] or byid[4]['result'].get('isError'),byid[4]
assert 'error' not in byid[5] and not byid[5]['result'].get('isError'),byid[5]
assert p.returncode==0
r=dict(passed=True,toolNames=names,requests=requests,responses=rows,binarySHA256=hashlib.sha256(b.read_bytes()).hexdigest(),scope='unchanged existing native runtime; no device systems source admitted into bounded Core')
(D/'MCP-SMOKE.json').write_text(json.dumps(r,indent=2)+'\n');print('Nine native MCP tools; sum=12; systems source refused.')
