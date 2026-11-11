from pathlib import Path
import subprocess,json,os,random,select,atexit,re,hashlib
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_TEST_BINARY',str(R/'output/core-0.6-r2/rf2')))
class Peer:
 def __init__(self,args):self.p=subprocess.Popen([str(x)for x in args],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.i=0;atexit.register(lambda:self.p.kill()if self.p.poll()is None else None)
 def send(self,obj):
  self.p.stdin.write(json.dumps(obj,separators=(',',':')).encode()+b'\n');self.p.stdin.flush();assert select.select([self.p.stdout],[],[],15)[0],'timeout';line=self.p.stdout.readline();assert line,(self.p.poll(),self.p.stderr.read());return json.loads(line)
 def rpc(self,method,params=None):
  self.i+=1;obj={'jsonrpc':'2.0','id':self.i,'method':method}
  if params is not None:obj['params']=params
  ans=self.send(obj);assert ans['id']==self.i;return ans
 def close(self):self.p.stdin.close();self.p.wait(timeout=5);assert self.p.returncode==0;assert not self.p.stderr.read()
peer=Peer([B,'mcp']);oracle=Peer(['/opt/homebrew/opt/node@22/bin/node',R/'tests/standalone/oracle.mjs'])
peer.rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'core-verifier','version':'1'}})
peer.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');peer.p.stdin.flush()
report={'schema':'rf2.native.core.verification.v1','programs':0,'admissionCases':0,'executionCases':0,'seededMutations':0,'passed':False,'speedClaim':None,'tokenClaim':None}
S=(R/'examples/sum.flow').read_text()
def simple(op,args,mode='CHECKED'):
 return f'FLOW "Proof"\nPROFILE RF2_U32_CORE_V0\nARITHMETIC {mode}\nFUNCTION main(data: u32[], count: u32) RETURNS u32\nSTEP x = {op} WITH {{ {args}, result: answer }}\nRETURN answer\nEND'
def run(source,data,count=None):
 args={'source':source,'data':data}
 if count is not None:args['count']=count
 return peer.rpc('tools/call',{'name':'rf2_run','arguments':args})
def check(source):
 a=peer.rpc('tools/call',{'name':'rf2_check','arguments':{'source':source}});b=oracle.send({'mode':'check','source':source});ok='result'in a and not a['result'].get('isError',False);assert ok==b['ok'],('admission mismatch',source,a,b);report['admissionCases']+=1;return ok
def compare(source,data,count=None):
 a=run(source,data,count);b=oracle.send({'source':source,'data':data,'count':len(data)if count is None else count});ok='result'in a and not a['result'].get('isError',False);assert ok==b['ok'],('execution mismatch',source,data[:20],count,a,b)
 if ok:
  v=a['result']['structuredContent'];assert v['value']==b['value']and v['steps']==b['steps'],('value/work',source,a,b)
 report['executionCases']+=1
sources=[S,simple('ADD','a: 4294967295, b: 1'),simple('MUL','a: 4294967295, b: 4294967295','WRAP'),simple('LOAD','array: data, index: 1'),simple('POPCOUNT','value: 4294967295'),simple('NONZERO','value: 0'),S.replace('LIMIT 65536','LIMIT 1')]
helper='FUNCTION plus(a: u32, b: u32) RETURNS u32\nSTEP x = ADD WITH { a: a, b: b, result: value }\nRETURN value\nEND\n'
H=S.replace('FUNCTION main',helper+'FUNCTION main').replace('ADD WITH { a: total, b: item','CALL plus WITH { a: total, b: item');sources+=[H,H[H.index('FLOW'):],H.replace(helper,'')+'\n'+helper]
sources+=[S.replace('  RETURN total','  FOR j FROM 0 TO count LIMIT 65536\nVAR delta = 1\nSTEP y = ADD WITH { a: total, b: delta, result: total }\nEND FOR\n  RETURN total')]
sources+=[x for x in re.findall(r'```flow\n([\s\S]*?)```',(R/'book/RiverFlow-First-Edition.md').read_text())]
sources+=[simple('CALL unit','').replace('WITH { ,','WITH {')+'\nFUNCTION unit() RETURNS u32\nRETURN 19\nEND']
sources+=[S.replace(S.splitlines()[0],'FLOW "தமிழ் 🌊"'),S.replace('FUNCTION main(data: u32[], count: u32)','FUNCTION main(, data: u32[],, count: u32,)')]
rng=random.Random(20261112)
for i in range(70):
 body=['VAR v0 = 1']
 for j in range(rng.randrange(1,12)):
  op=rng.choice(['ADD','MUL','POPCOUNT','NONZERO']);value=f'v{rng.randrange(j+1)}';args=f'a: {value}, b: {rng.randrange(50)}'if op in ['ADD','MUL']else f'value: {value}';body.append(f'STEP s{j} = {op} WITH {{ {args}, result: v{j+1} }}')
 sources.append('FLOW "Seeded"\nPROFILE RF2_U32_CORE_V0\nARITHMETIC '+rng.choice(['CHECKED','WRAP'])+'\nFUNCTION main(data: u32[], count: u32) RETURNS u32\n'+'\n'.join(body)+f'\nRETURN v{len(body)-1}\nEND')
# Boundary programs preserve unused-function checks, four-argument calls and scope restoration.
sources += [S.replace('END FOR\n', 'END FOR\nVAR item = 7\n',1), S.replace('data: u32[], count: u32','buffer: u32[], size: u32').replace('TO count','TO size').replace('array: data','array: buffer')]
chain='FLOW "Chain"\nPROFILE RF2_U32_CORE_V0\nARITHMETIC CHECKED\nFUNCTION main(data: u32[], count: u32) RETURNS u32\nSTEP x = CALL f0 WITH { result: v }\nRETURN v\nEND\n'
for k in range(15):chain+=f'FUNCTION f{k}() RETURNS u32\n'+(f'STEP x = CALL f{k+1} WITH {{ result: v }}\nRETURN v\n'if k<14 else'RETURN 29\n')+'END\n'
sources.append(chain)
sources.append('FLOW "Four"\nPROFILE RF2_U32_CORE_V0\nARITHMETIC WRAP\nFUNCTION helper(a:u32,b:u32,c:u32,d:u32) RETURNS u32\nSTEP x = ADD WITH { a: a, b: b, result: x }\nSTEP y = MUL WITH { a: c, b: d, result: y }\nSTEP z = ADD WITH { a: x, b: y, result: z }\nRETURN z\nEND\nFUNCTION main(data:u32[],count:u32) RETURNS u32\nSTEP x = CALL helper WITH { d: 9, c: 8, b: 7, a: 6, result: v }\nRETURN v\nEND')
for ws in ['\u00a0','\u1680','\u2003','\u202f','\u205f','\u3000','\ufeff']:
 sources.append(ws+S+ws)
 sources.append(S.replace('data: u32[]','data:'+ws+'u32[]'))
sources += [S.replace(S.splitlines()[0], 'FLOW "'+'🌊'*32+'"'),'#'+'é'*20000+'\n'+S]
for source in sources:
 assert check(source);report['programs']+=1
 for i,data in enumerate([[],[1],[2,3,4],[4294967295,1],[0,1,3,255]]+[[rng.randrange(2**32)for _ in range(rng.randrange(20))]for _ in range(5)]):compare(source,data,0 if i==9 else None)
invalid=[S.replace('RF2_U32_CORE_V0','OTHER'),S.replace('ADD WITH','NETWORK WITH'),S.replace('result: total','result: count'),S.replace('RETURN total','RETURN item'),H.replace('STEP x = ADD WITH','STEP x = CALL plus WITH'),S.replace('VAR total = 0','VAR total = data'),S.replace('FOR i','FOR count'),S.replace('LIMIT 65536','LIMIT 65537'),S.replace('LIMIT 65536','LIMIT 0'),S.replace('index: i','index: data'),S.replace('FUNCTION main(','FUNCTION main ('),S.replace('VAR total = 0','VAR total  = 0'),S.replace('b: item','a: item'),S.replace('STEP add','STEP 3foo'),S.replace('LOAD WITH','CALL missing WITH')]
for source in invalid:check(source)
check(S.replace(S.splitlines()[0], 'FLOW "'+'🌊'*33+'"'))
collision='FLOW "Collision"\nPROFILE RF2_U32_CORE_V0\nARITHMETIC CHECKED\nFUNCTION helper(result: u32) RETURNS u32\nRETURN result\nEND\nFUNCTION main(data:u32[],count:u32) RETURNS u32\nVAR x = 1\nSTEP s = CALL helper WITH { result: x, bogus: 0 }\nRETURN x\nEND'
check(collision)
check(collision.replace('STEP s = CALL helper WITH { result: x, bogus: 0 }','STEP s = ADD WITH { a: x, b: 0, result: x }'))
for sep in ['\r','\u2028','\u2029']:
 check(S.replace('a: total','a:'+sep+'total'))
 check(S.replace('data: u32[]','data:'+sep+'u32[]'))
check(S+'\nFUNCTION unused() RETURNS u32\nRETURN missing\nEND')
check(chain+'FUNCTION extra() RETURNS u32\nRETURN 1\nEND')
check(S.replace('STEP add = ADD WITH','\n'.join(f'STEP x{i} = ADD WITH {{ a: total, b: 0, result: total }}'for i in range(513))+'\nSTEP add = ADD WITH'))
# Large work limit, LOAD beyond count but within full input capacity, helper chains and loop-local reuse.
work=S.replace('STEP add = ADD WITH','\n'.join(f'STEP w{i} = ADD WITH {{ a: total, b: 0, result: total }}'for i in range(20))+'\nSTEP add = ADD WITH');assert check(work);compare(work,[0]*65536)
compare(simple('LOAD','array: data, index: 1'),[5,7],1)
# Recovery after source refusal and execution overflow.
compare(S,[1,2,3]);compare(S,[4294967295,1]);compare(S,[7])
for i in range(180):
 pos=rng.randrange(len(S));changed=S[:pos]+rng.choice([' ','X',':',',','\n','0'])+S[pos+1:];check(changed);report['seededMutations']+=1
report['uniqueSourcePrograms']=len(set(sources));peer.close();oracle.close();report.update(passed=True,executableSHA256=hashlib.sha256(B.read_bytes()).hexdigest());(R/'docs/GENERAL-CORE-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
