"""Recreate the reviewed pilot payload; pure local preparation, no provider call."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent
EXPECTED='014d18a700642dab98a1f71da790af16d8eead7ae10d327f143e6c30b88ef442'
def payload():
    task=(HERE/'TASK-C.md').read_text();old='Return strict JSON exactly {"source":"complete main.flow"}.'
    assert task.count(old)==1
    task=task.replace(old,'Return one JSON object with only the key source. Its value must be the actual complete RF2 program text, beginning with profile RF2_SYSTEM_A64_V1. Do not output a filename, description, template, placeholder or Markdown fences.')
    system='Implement the complete RF2 task and respect the supplied condition and import permissions. Return one JSON object with only the key source. Its value must contain the actual complete RF2 program text, beginning with profile RF2_SYSTEM_A64_V1. Never return a placeholder, filename or prose description. Source proposal only; no commands or execution claims.'
    content=(HERE/'COMMON-GUIDE.md').read_text()+'\nCONDITION: CLI\nTASK\n'+task
    value={'model':'deepseek-v4-pro','thinking':{'type':'enabled'},'reasoning_effort':'low','messages':[{'role':'system','content':system},{'role':'user','content':content}],'max_tokens':10000,'stream':False,'response_format':{'type':'json_object'}}
    raw=json.dumps(value,ensure_ascii=False).encode();assert hashlib.sha256(raw).hexdigest()==EXPECTED,'Reviewed payload inputs changed'
    return raw
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();raw=payload();args.out.mkdir(parents=True,exist_ok=False);(args.out/'request.json').write_bytes(raw);(args.out/'PREPARED.json').write_text(json.dumps({'requestSHA256':EXPECTED,'providerCalls':0,'source':'Reviewed guide/task plus explicit program-text output contract'},indent=2)+'\n');print(json.dumps({'requestSHA256':EXPECTED,'providerCalls':0}))
