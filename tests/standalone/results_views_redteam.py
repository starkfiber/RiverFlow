"""Independent adversarial programs for typed results and safe byte/text views.

Run only against an explicitly selected new candidate:
 RF2_TEST_COMPILER=/absolute/candidate python3 tests/standalone/results_views_redteam.py
Each run retains a fresh, bounded artifact directory. No negative admission is executed.
"""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2]
selected=os.environ.get('RF2_TEST_COMPILER')
if not selected:raise SystemExit('Set RF2_TEST_COMPILER to the reviewed result/view candidate; baseline execution is intentionally disabled.')
C=Path(selected).resolve()
if not C.is_file():raise SystemExit('Selected candidate is missing.')
D=R/'artifacts/redteam-results-views/new-candidate'/f'run-{time.time_ns()}';D.mkdir(parents=True,exist_ok=False)
HEADER='profile RF2_SYSTEM_A64_V1\n'
RESULTS='''result Number(u64, u64)
fn choose(n): Number
 if n==0
  return err(7)
 end
 return ok(n+1)
end
fn plain(n)
 return n
end
'''
VIEWS='''array Bytes(u8, 8)
array Words(u64, 8)
record Box(value:u64)
view Slice(Bytes)
fn scalar(n)
 return n
end
fn mutate(b:Bytes)
 set b[0]=255
 return 0
end
'''
CASES=[]
def case(name,src,compile_ok=False,exit_code=0,stderr=None):
 CASES.append({'name':name,'source':HEADER+src,'compile_ok':compile_ok,'exit':exit_code,'stderr':stderr})
def main(body):return 'fn main(argc,argv)\n'+body+'\nend\n'
def result_body(success='set answer=value',failure='set answer=100+error',after='return answer!=5'):
 return 'let answer=0\nhandle choose(4)\nok value\n'+success+'\nerr error\n'+failure+'\nend\n'+after
# Both variants and branch-local payload access.
case('result-ok',RESULTS+main(result_body()),True)
case('result-err',RESULTS+main(result_body(after='return answer!=107').replace('handle choose(4)','handle choose(0)')),True)
case('result-arm-if',RESULTS+main(result_body(success='if value==5\nset answer=5\nend')),True)
case('result-typed-root-return',RESULTS+'''fn wrapper(n): Number
 if n==0
  return err(11)
 end
 return ok(n+2)
end
'''+main('let answer=0\nhandle wrapper(3)\nok value\nset answer=value\nerr error\nset answer=error\nend\nreturn answer!=5'),True)
# Exhaustiveness and malformed grammar must fail closed.
for name,body in {
 'result-missing-err':'handle choose(4)\nok value\nreturn value\nend\nreturn 0',
 'result-missing-ok':'handle choose(4)\nerr error\nreturn error\nend\nreturn 0',
 'result-duplicate-ok':'handle choose(4)\nok value\nreturn value\nok again\nreturn again\nend\nreturn 0',
 'result-duplicate-err':'handle choose(4)\nok value\nreturn value\nerr error\nreturn error\nerr again\nreturn again\nend\nreturn 0',
 'result-wildcard':'handle choose(4)\nok value\nreturn value\nelse\nreturn 0\nend\nreturn 0',
 'result-wrong-order':'handle choose(4)\nerr error\nreturn error\nok value\nreturn value\nend\nreturn 0',
 'result-handle-scalar':'handle plain(4)\nok value\nreturn value\nerr error\nreturn error\nend\nreturn 0',
 'result-handle-arithmetic':'handle choose(4)+0\nok value\nreturn value\nerr error\nreturn error\nend\nreturn 0',
 'result-discard':'do choose(4)\nreturn 0',
 'result-as-local':'let r=choose(4)\nreturn 0',
 'result-length-escape':'let r=choose(4).length\nreturn r',
 'result-index-escape':'let r=choose(4)[0]\nreturn r',
 'result-parenthesized-scalar':'return (choose(4))',
 'result-scalar-call':'return plain(choose(4))',
 'result-tag-field':'let r=choose(4)\nset r.tag=0\nreturn 0',
 'result-payload-outside':'let answer=0\nhandle choose(4)\nok value\nset answer=value\nerr error\nset answer=error\nend\nreturn value',
 'result-error-outside':'let answer=0\nhandle choose(0)\nok value\nset answer=value\nerr error\nset answer=error\nend\nreturn error',
 'result-payload-assignment':result_body(success='set value=9'),
 'result-payload-in-err':result_body(failure='set answer=value'),
 'result-error-in-ok':result_body(success='set answer=error'),
 'result-payload-fast-rhs':result_body(failure='set answer=answer+value'),
 'result-payload-fast-condition':result_body(failure='if value<9\nset answer=1\nend'),
 'result-payload-fast-while':result_body(failure='let i=0\nwhile i<value\nset i=i+1\nend'),
 'result-payload-periodic-reducer':result_body(failure='let i=0\nlet total=0\nwhile i<value\nset total=total+(i&255)\nset i=i+1\nend'),
 'result-payload-conditional-reducer':result_body(failure='let i=0\nlet total=0\nwhile i<value\nif (i&3)==0\nset total=total+7\nelse\nset total=total+(i&31)\nend\nset i=i+1\nend'),
}.items():case(name,RESULTS+main(body))
case('result-return-scalar', 'result Number(u64,u64)\nfn bad():Number\nreturn 3\nend\n'+main('return 0'))
case('result-missing-root-return','result Number(u64,u64)\nfn bad(n):Number\nif n\nreturn ok(1)\nelse\nreturn err(2)\nend\nend\n'+main('return 0'))
case('result-main-typed','result Number(u64,u64)\nfn main(argc,argv):Number\nreturn ok(0)\nend\n')
case('result-constructor-untyped',main('return ok(1)'))
case('result-nonscalar-payload','array Bytes(u8,8)\nresult Number(u64,u64)\nfn bad():Number\nlet a=Bytes()\nreturn ok(a)\nend\n'+main('return 0'))
# Previously admitted uninitialized scalar cases must now refuse, not acquire new payload holes.
case('baseline-scalar-forward-read',main('let x=y\nlet y=42\nreturn x'))
case('baseline-scalar-false-arm-read',main('if 0\nlet x=99\nend\nreturn x'))
# View success and its own subrange rather than full owner capacity.
for name,start,count,index,want in [('view-first',0,1,0,11),('view-last',7,1,0,255),('view-middle',2,3,1,44),('view-whole',0,8,7,255)]:
 body=f'let data=Bytes()\nset data[0]=11\nset data[3]=44\nset data[7]=255\nlet v=Slice(data,{start},{count})\nreturn (v.length!={count})|(v[{index}]!={want})'
 case(name,VIEWS+main(body),True)
for name,start,count in [('view-empty-start',0,0),('view-empty-end',8,0)]:case(name,VIEWS+main(f'let data=Bytes()\nlet v=Slice(data,{start},{count})\nreturn v.length!=0'),True)
case('view-read-expression',VIEWS+main('let data=Bytes()\nset data[0]=11\nlet v=Slice(data,0,2)\nlet answer=v[0]+v[1]+v.length\nreturn answer!=13'),True)
for name,start,count,index in [('view-start-over',9,0,None),('view-range-over',7,2,None),('view-overflow-wrap',18446744073709551615,1,None),('view-length-wrap',1,18446744073709551615,None),('view-outside-subrange',2,1,1),('view-empty-read',8,0,0)]:
 body=f'let data=Bytes()\nlet start={start}+(argc-1)\nlet count={count}+(argc-1)\nlet v=Slice(data,start,count)\nreturn '+(f'v[{index}]'if index is not None else'0')
 case(name,VIEWS+main(body),True,2,'RF2 bounds\n')
for name,body in {
 'view-owner-write':'let data=Bytes()\nlet v=Slice(data,0,1)\nset data[0]=255\nreturn v[0]',
 'view-owner-read-bytes':'let data=Bytes()\nlet v=Slice(data,0,1)\nlet n=read_bytes(0,data,1)\nreturn n',
 'view-helper-call':'let data=Bytes()\nlet v=Slice(data,0,1)\ndo mutate(data)\nreturn v[0]',
 'view-pure-call':'let data=Bytes()\nlet v=Slice(data,0,1)\nreturn scalar(v.length)',
 'view-raw-load':'let data=Bytes()\nlet v=Slice(data,0,1)\nreturn load8(v)',
 'view-raw-write':'let data=Bytes()\nlet v=Slice(data,0,1)\nreturn write(1,v,1)',
 'view-copy':'let data=Bytes()\nlet v=Slice(data,0,1)\nlet alias=v\nreturn 0',
 'view-return':'let data=Bytes()\nlet v=Slice(data,0,1)\nreturn v',
 'view-rebind':'let data=Bytes()\nlet v=Slice(data,0,1)\nset v=Slice(data,1,1)\nreturn 0',
 'view-write':'let data=Bytes()\nlet v=Slice(data,0,1)\nset v[0]=65\nreturn 0',
 'view-length-write':'let data=Bytes()\nlet v=Slice(data,0,1)\nset v.length=5\nreturn 0',
 'view-address-field':'let data=Bytes()\nlet v=Slice(data,0,1)\nreturn v.pointer',
 'view-box-escape':'let data=Bytes()\nlet v=Slice(data,0,1)\nlet box=Box(v)\nreturn 0',
 'view-arithmetic-escape':'let data=Bytes()\nlet v=Slice(data,0,1)\nreturn 0+v',
 'view-owner-uninitialized':'let v=Slice(data,0,1)\nlet data=Bytes()\nreturn 0',
}.items():case(name,VIEWS+main(body))
for name,statement in [('view-alias-write','set b[0]=255'),('view-alias-read-bytes','do read_bytes(0,b,1)'),('view-alias-helper','do mutate(b)')]:
 src=VIEWS+'fn alias(a:Bytes,b:Bytes)\nlet v=Slice(a,0,1)\n'+statement+'\nreturn v[0]\nend\n'+main('let data=Bytes()\nreturn alias(data,data)');case(name,src)
case('view-parameter',VIEWS+'fn invalid(v:Slice)\nreturn v.length\nend\n'+main('return 0'))
case('view-word-owner','array Words(u64,8)\nview Slice(Words)\n'+main('return 0'))
# A result payload must not smuggle a borrowed view; the source-side call ban also applies.
case('view-result-escape',VIEWS+'result Number(u64,u64)\nfn invalid():Number\nlet data=Bytes()\nlet v=Slice(data,0,1)\nreturn ok(v)\nend\n'+main('return 0'))
# Follow-on tests exercise custom lowering paths and nested scopes.
case('result-payload-inplace',RESULTS+main(result_body(success='set value=value+1')))
case('result-ignored-condition',RESULTS+main('if choose(1)\nreturn 0\nend\nreturn 0'))
case('result-ignored-while',RESULTS+main('while choose(1)\nreturn 0\nend\nreturn 0'))
case('result-nested-handles',RESULTS+main('let answer=0\nhandle choose(4)\nok outer\nhandle choose(0)\nok inner\nset answer=outer+inner\nerr failure\nset answer=outer+failure\nend\nerr outerFailure\nset answer=outerFailure\nend\nreturn answer!=12'),True)
case('result-inner-payload-after-handle',RESULTS+main('let answer=0\nhandle choose(4)\nok outer\nhandle choose(0)\nok inner\nset answer=inner\nerr failure\nset answer=failure\nend\nset answer=inner\nerr outerFailure\nset answer=outerFailure\nend\nreturn answer'))
case('view-handle-call-ban',RESULTS+VIEWS+main('let data=Bytes()\nlet v=Slice(data,0,1)\nhandle choose(4)\nok value\nreturn value\nerr error\nreturn error\nend\nreturn 0'))
case('view-unreachable-call-ban',VIEWS+main('let data=Bytes()\nlet v=Slice(data,0,1)\nif 0\ndo mutate(data)\nend\nreturn v[0]'))
case('view-byteio-in-index',VIEWS+main('let data=Bytes()\nlet v=Slice(data,0,1)\nreturn v[read_bytes(0,data,1)]'))
case('view-result-observation',VIEWS+"""result Number(u64,u64)
fn first(data:Bytes):Number
 let v=Slice(data,0,1)
 return ok(v[0])
end
"""+main('let data=Bytes()\nset data[0]=17\nlet answer=0\nhandle first(data)\nok value\nset answer=value\nerr error\nset answer=error\nend\nreturn answer!=17'),True)
rows=[]
for c in CASES:
 src=D/(c['name']+'.rf2');src.write_text(c['source'])
 for opt in [False,True]:
  out=D/(c['name']+('-opt'if opt else'-default'));p=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True,timeout=20)
  row={'name':c['name'],'optimized':opt,'expectedCompile':c['compile_ok'],'compileExit':p.returncode,'stderr':p.stderr.decode(errors='replace'),'sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'passed':False}
  if not c['compile_ok']:
   row['passed']=p.returncode==1 and not out.exists()
  elif p.returncode==0:
   subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True)
   try:
    q=subprocess.run([out],input=b'',capture_output=True,timeout=3);row.update(runExit=q.returncode,runStdout=q.stdout.decode(errors='replace'),runStderr=q.stderr.decode(errors='replace'),executableSHA256=hashlib.sha256(out.read_bytes()).hexdigest());row['passed']=q.returncode==c['exit'] and not q.stdout and (c['stderr'] is None or q.stderr.decode(errors='replace')==c['stderr'])
   except subprocess.TimeoutExpired:row['timeout']=True
  rows.append(row)
  print(('PASS'if row['passed']else'FAIL'),c['name'],'opt'if opt else'default',p.returncode,row.get('runExit'),flush=True)
report={'passed':all(x['passed']for x in rows),'compiler':str(C),'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'workingSourceAtInspectionSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'programs':len(CASES),'modeCases':len(rows),'passedCases':sum(x['passed']for x in rows),'results':rows,'scope':'Independent finite local native red-team programs. Negative admissions are never executed. No external traffic, raw-memory exploit or general safety proof. View syntax is a read-only byte slice, not automatically permanent UTF-8 validity.'}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'programs':len(CASES),'modeCases':len(rows),'passedCases':report['passedCases'],'report':str(D/'report.json')}));raise SystemExit(0 if report['passed'] else 1)
