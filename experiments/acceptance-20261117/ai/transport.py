"""Explicit direct provider transport; remote credential never leaves selected host."""
import os,shlex
REMOTE='''import json,sys,urllib.request
from pathlib import Path
p=json.load(sys.stdin)
e=dict(l.split('=',1)for l in Path(sys.argv[1]).read_text().splitlines()if '='in l and not l.startswith('#'))
k=e['OPENAI_API_KEY'].strip(chr(34)+chr(39))
r=urllib.request.Request('https://api.deepseek.com/chat/completions',data=json.dumps(p).encode(),headers={'Authorization':'Bearer '+k,'Content-Type':'application/json'})
with urllib.request.urlopen(r,timeout=int(sys.argv[2]))as q:sys.stdout.write(q.read().decode())
'''
def remote_command(http_timeout=180):
    assert 1<=http_timeout<=180
    host=os.environ.get('RF2_PROVIDER_SSH_HOST');credential_file=os.environ.get('RF2_PROVIDER_REMOTE_ENV_FILE')
    if not host or not credential_file:raise ValueError('Configure explicit authorized SSH host and remote credential-file reference')
    if host.startswith('-')or '\n'in host:raise ValueError('Invalid host alias')
    return ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8',host,'python3 -c '+shlex.quote(REMOTE)+' '+shlex.quote(credential_file)+' '+str(http_timeout)]
