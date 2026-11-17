"""One explicitly bounded provider campaign; credentials never enter local artifacts.

Calls only propose source. Compilation/execution is a separate manually reviewed
step. This is not OpenClaw/DeepClaw execution or an embedded RF2 model.
"""
import argparse,hashlib,json,os,shlex,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
REMOTE='''import json,sys,urllib.request
from pathlib import Path
p=json.load(sys.stdin)
e=dict(l.split('=',1)for l in Path(sys.argv[1]).read_text().splitlines()if '='in l and not l.startswith('#'))
k=e['OPENAI_API_KEY'].strip(chr(34)+chr(39))
r=urllib.request.Request('https://api.deepseek.com/chat/completions',data=json.dumps(p).encode(),headers={'Authorization':'Bearer '+k,'Content-Type':'application/json'})
with urllib.request.urlopen(r,timeout=120)as q:sys.stdout.write(q.read().decode())
'''
def sha(b):return hashlib.sha256(b).hexdigest()
def remote_command():
    host=os.environ.get('RF2_PROVIDER_SSH_HOST')
    credential_file=os.environ.get('RF2_PROVIDER_REMOTE_ENV_FILE')
    if not host or not credential_file:raise ValueError('Configure explicit RF2_PROVIDER_SSH_HOST and RF2_PROVIDER_REMOTE_ENV_FILE; credentials stay on the authorized provider host')
    if host.startswith('-')or '\n'in host:raise ValueError('Invalid SSH host alias')
    return ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8',host,'python3 -c '+shlex.quote(REMOTE)+' '+shlex.quote(credential_file)]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--attempt',type=int,choices=(1,2,3,4),required=True);a=ap.parse_args()
    root=a.out.resolve();root.mkdir(parents=True,exist_ok=True)
    # A/B/B/A is fixed before any response; each directory is exclusive, no retries.
    condition=('manual','report','report','manual')[a.attempt-1]
    d=root/f'author-{a.attempt}-{condition}';d.mkdir(exist_ok=False)
    guide=(ROOT/'experiments/sdk-task/SDK-RF2.md').read_text().split('## Shared legacy MCP helper')[0]
    guide+='\nExtra IO: io_write_no_sigpipe(fd,p,n):IO is supplied; call via exhaustive handle or try inside IO-returning functions.\n'
    if condition=='report':guide+='\n'+(HERE/'REPORT-API.md').read_text()
    task=(HERE/'PROVIDER-TASK.md').read_text()
    p={'model':'deepseek-flash','thinking':{'type':'disabled'},'messages':[{'role':'system','content':'Implement the exact task using ONLY the supplied RF2 language and SDK contract. Source is a proposal; the controller will compile and execute it independently. Strict JSON only.'},{'role':'user','content':guide+'\nTASK\n'+task}],'max_tokens':3500,'stream':False,'response_format':{'type':'json_object'}}
    request=json.dumps(p,ensure_ascii=False).encode();(d/'request.json').write_bytes(request)
    t=time.monotonic();receipt={'schema':'rf2.provider.author.v1','attempt':a.attempt,'condition':condition,'requestSHA256':sha(request),'taskSHA256':sha(task.encode()),'guideSHA256':sha(guide.encode()),'requestedModel':p['model'],'thinking':'disabled','maxOutputTokens':3500,'sourceExecution':'not performed by provider runner','retention':'project-owned local; no shared Memory/Chain/OpenClaw/DeepClaw session'}
    try:
        proc=subprocess.run(remote_command(),input=request,capture_output=True,timeout=135)
        receipt['transportExit']=proc.returncode
        if proc.returncode!=0:
            receipt['failure']='transport/provider failed; no automatic retry';receipt['stderr']=proc.stderr.decode(errors='replace')[:1000]
        else:
            raw=json.loads(proc.stdout);(d/'response.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2))
            choice=raw['choices'][0];receipt.update(servedModel=raw.get('model'),usage=raw.get('usage'),finishReason=choice.get('finish_reason'))
            if choice.get('finish_reason')!='stop':receipt['failure']='provider did not finish; source not admitted'
            else:
                content=json.loads(choice['message']['content']);assert set(content)=={'source'} and isinstance(content['source'],str)
                source=content['source'].encode();assert len(source)<=65536
                (d/'main.flow').write_bytes(source);receipt['proposedSourceSHA256']=sha(source)
    except (Exception,KeyboardInterrupt)as e:
        receipt['failure']=type(e).__name__+': '+str(e)[:500]
    receipt['elapsedSeconds']=round(time.monotonic()-t,3)
    (d/'RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
if __name__=='__main__':main()
