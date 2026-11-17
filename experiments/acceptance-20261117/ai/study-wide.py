"""Amended useful-output study: complete-output budget and longer provider observation. Source proposals require a separate reviewed build.

No model commands are run. Credentials stay on an explicitly selected host.
All unique study data persist in the project; only emitted native images use TMPDIR.
"""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
COMPILER_SHA='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
ORDER=[('A','manual'),('A','report'),('B','report'),('B','manual')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def guide(condition):
    base=(ROOT/'experiments/sdk-task/SDK-RF2.md').read_text().split('## Shared legacy MCP helper')[0]
    base+='''\nChecked output: io_write_no_sigpipe(fd,p,n):IO is available. Handle or try only inside IO functions.
TextSpan(start:u64,length:u64), TextCursor(next:u64,line:u64,done:u64,status:u64) are provided.
Initialize each with zero fields at function body root. text_next_line(p,n,cursor,span)
returns1for next line,0for finished/error; inspect cursor.status. It excludes LF and
CR immediately before LF, not an unterminated final CR. No phantom trailing line.
ALL record locals must be directly in the function body, before entering branches/handle.
No arrow return syntax, no scalar :u64 annotations, no io_args. main(argc,argv) supplies args.
Only functions declared :IO can use try. Plain writer/report helpers return scalars; use do.
Ordinary function statements require do. No invented APIs, recursion, raw platform operations.
NATIVE-ADMITTED COMMON SYNTAX (not a task solution):\n'''+(HERE/'style.flow').read_text()
    if condition=='report':base+='\n'+(ROOT/'experiments/evolution-20261117/report/REPORT-API.md').read_text()
    else:base+='\nManual condition: import @rf2/v1/text.flow only. Compose JSON/HTML bytes explicitly with Writer helpers; do not import report.flow or use Report helpers.\n'
    return base
def init(a):
    d=a.out.resolve();d.mkdir(parents=True,exist_ok=False)
    assert sha(a.compiler)==COMPILER_SHA
    sdk=load_module(ROOT/'experiments/evolution-20261117/package.py','sdk_pack').create(d/'sdk')
    inputs=[HERE/n for n in ['PROTOCOL.md','TASK-A.md','TASK-B.md','style.flow','grade.py','study-wide.py','AMENDMENT.md','transport.py']]+[ROOT/'experiments/sdk-task/SDK-RF2.md',ROOT/'experiments/evolution-20261117/report/REPORT-API.md']+list(sdk.iterdir())
    for condition in ['manual','report']:(d/(condition+'-guide.md')).write_text(guide(condition))
    inputs += [d/'manual-guide.md',d/'report-guide.md']
    p=subprocess.run([str(a.compiler.resolve()),'--check',str(HERE/'style.flow'),'--sdk-root',str(sdk),'--diagnostic-json'],capture_output=True,timeout=15)
    (d/'style-admission.stderr').write_bytes(p.stderr);assert p.returncode==0,p.stderr.decode()
    frozen={'schema':'rf2.cost-to-correct.freeze.v1','model':'deepseek-v4-pro','thinking':'enabled','effort':'low','maxCompletionTokens':10000,'httpTimeout':180,'transportTimeout':195,'maxCalls':8,'roundsPerAttempt':2,'order':ORDER,'compiler':str(a.compiler.resolve()),'compilerSHA256':COMPILER_SHA,'inputs':{str(p.resolve()):sha(p)for p in inputs},'SDK':str(sdk),'styleNativeAdmission':True,'retention':'project-local only'}
    (d/'FROZEN.json').write_text(json.dumps(frozen,indent=2));print(json.dumps({'frozen':str(d/'FROZEN.json'),'SHA256':sha(d/'FROZEN.json'),'styleNativeAdmission':True}))
def frozen(d):
    f=json.loads((d/'FROZEN.json').read_text())
    for name,want in f['inputs'].items():assert sha(name)==want,'Frozen input drift: '+name
    assert sha(f['compiler'])==f['compilerSHA256'];return f
def call(a):
    d=a.out.resolve();f=frozen(d);assert len(list(d.glob('attempt-*/round-*/request.json')))<f['maxCalls']
    task,condition=ORDER[a.attempt-1];base=d/f'attempt-{a.attempt}-{task}-{condition}';base.mkdir(exist_ok=True);r=base/f'round-{a.round}'
    if a.round==2:
        previous=base/'round-1';assert(previous/'ASSESSMENT.json').exists();prior=json.loads((previous/'ASSESSMENT.json').read_text());assert not prior.get('allPassed'), 'Already complete; no repair allowed'
    r.mkdir(exist_ok=False)
    context=(d/(condition+'-guide.md')).read_text()+'\nTASK\n'+(HERE/f'TASK-{task}.md').read_text()
    if a.round==2:
        context+='\nPREVIOUS PROPOSED SOURCE\n'+(previous/'main.flow').read_text()+'\nACTUAL CONTROLLER FEEDBACK\n'+json.dumps(prior,ensure_ascii=False)
    assert len(context.encode())<=30000
    payload={'model':f['model'],'thinking':{'type':'enabled'},'reasoning_effort':'low','messages':[{'role':'system','content':'Implement the exact complete RF2 task with the supplied language/SDK only. This is source proposed for independent compilation/tests. Return strict JSON exactly {"source":"complete main.flow"}. Do not claim execution or include commands.'},{'role':'user','content':context}],'max_tokens':f['maxCompletionTokens'],'stream':False,'response_format':{'type':'json_object'}}
    raw=json.dumps(payload,ensure_ascii=False).encode();(r/'request.json').write_bytes(raw);start=time.monotonic();receipt={'attempt':a.attempt,'round':a.round,'task':task,'condition':condition,'requestSHA256':hashlib.sha256(raw).hexdigest(),'frozenSHA256':sha(d/'FROZEN.json'),'sourceExecution':False}
    provider=load_module(HERE/'transport.py','provider_transport')
    try:
        p=subprocess.run(provider.remote_command(f['httpTimeout']),input=raw,capture_output=True,timeout=f['transportTimeout']);receipt['transportExit']=p.returncode
        if p.returncode:receipt.update(failure='transport failed; no automatic retry',stderr=p.stderr.decode(errors='replace')[:700])
        else:
            data=json.loads(p.stdout);(r/'response.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));choice=data['choices'][0];receipt.update(servedModel=data.get('model'),usage=data.get('usage'),finishReason=choice.get('finish_reason'))
            if choice.get('finish_reason')=='stop':
                content=json.loads(choice['message']['content']);assert set(content)=={'source'}and isinstance(content['source'],str);source=content['source'].encode();assert len(source)<=65536
                (r/'main.flow').write_bytes(source);receipt['sourceSHA256']=hashlib.sha256(source).hexdigest()
            else:receipt['failure']='incomplete output, not admitted'
    except(Exception,KeyboardInterrupt)as e:receipt['failure']=type(e).__name__+': '+str(e)[:700]
    receipt['elapsedSeconds']=time.monotonic()-start;(r/'RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
def assess(a):
    d=a.out.resolve();f=frozen(d);task,condition=ORDER[a.attempt-1];r=d/f'attempt-{a.attempt}-{task}-{condition}'/f'round-{a.round}';source=r/'main.flow';assert sha(source)==a.reviewed_sha,'Explicit source review hash must match'
    assert not(r/'ASSESSMENT.json').exists(),'Preserve prior assessment'
    # Images are reproducible from recorded source/compiler/options; unique logs remain here.
    tmp=Path(os.environ['TMPDIR'])/f'rf2-study-{a.attempt}-{a.round}';tmp.mkdir(exist_ok=False);binary=tmp/'program'
    command=[f['compiler'],str(source),str(binary),'--compact','--opt','--sdk-root',f['SDK'],'--diagnostic-json'];t=time.monotonic();p=subprocess.run(command,capture_output=True,timeout=30)
    (r/'compile.stderr').write_bytes(p.stderr);(r/'compile.stdout').write_bytes(p.stdout)
    result={'sourceSHA256':sha(source),'manualReviewConfirmed':True,'compileCommand':command,'compileExit':p.returncode,'compiled':p.returncode==0,'allPassed':False}
    if p.returncode:result['feedback']=p.stderr.decode(errors='replace')[:3000]
    else:
        subprocess.run(['codesign','-s','-',str(binary)],capture_output=True,check=True)
        q=subprocess.run([sys.executable,str(HERE/'grade.py'),task,'--binary',str(binary),'--out',str(r/'grade')],capture_output=True,timeout=120);(r/'grade.stdout').write_bytes(q.stdout);(r/'grade.stderr').write_bytes(q.stderr)
        result['binarySHA256']=sha(binary)
        if(r/'grade/RESULTS.json').exists():
            g=json.loads((r/'grade/RESULTS.json').read_text());result.update(allPassed=g['allPassed'],passed=g['passed'],total=g['total'],feedback=[x for x in g['cases']if not x['passed']][:4])
        else:result['feedback']='grader failed: '+q.stderr.decode(errors='replace')[:2000]
    result['buildAndTestSeconds']=time.monotonic()-t;(r/'ASSESSMENT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['init','call','assess']);p.add_argument('--out',type=Path,required=True);p.add_argument('--compiler',type=Path);p.add_argument('--attempt',type=int,choices=[1,2,3,4]);p.add_argument('--round',type=int,choices=[1,2]);p.add_argument('--reviewed-sha');a=p.parse_args();{'init':init,'call':call,'assess':assess}[a.action](a)
