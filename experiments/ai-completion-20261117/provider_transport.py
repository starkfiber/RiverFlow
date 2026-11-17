"""Opt-in provider transport candidate: bounded sanitized errors, no retries.

Importing does not read credentials, call a network service or execute a process.
The remote helper executes only on the explicitly selected credential host.
Existing frozen study transports/controllers do not import this candidate.
"""
from pathlib import Path
import json,math,os,re,shlex,socket,ssl,sys,time,urllib.error,urllib.request
MAX_REQUEST=120000
MAX_RESPONSE=2*1024*1024
MAX_CONFIG=1024*1024
ENDPOINT='https://api.deepseek.com/chat/completions'

class TransportRefusal(Exception):
    def __init__(self,category,error_type,reason_type=None,number=None,status=None):
        self.category=category;self.error_type=error_type;self.reason_type=reason_type;self.number=number;self.status=status

def _integer_errno(value):
    return value if isinstance(value,int)and not isinstance(value,bool)and -65535<=value<=65535 else None

def _reason(error):
    if isinstance(error,socket.gaierror):return 'gaierror',_integer_errno(error.errno),'dns'
    if isinstance(error,(TimeoutError,socket.timeout)):return 'TimeoutError',_integer_errno(getattr(error,'errno',None)),'timeout'
    if isinstance(error,ssl.SSLError):return 'SSLError',_integer_errno(error.errno),'tls'
    if isinstance(error,OSError):return 'OSError',_integer_errno(error.errno),'network'
    return 'Unavailable',None,'network'

def _classify(error):
    if isinstance(error,TransportRefusal):return error.category,error.error_type,error.status,error.reason_type,error.number
    if isinstance(error,urllib.error.HTTPError):
        status=error.code if isinstance(error.code,int)and not isinstance(error.code,bool)and 100<=error.code<=599 else None
        return 'http','HTTPError',status,'HTTPStatus',None
    if isinstance(error,urllib.error.URLError):
        reason,number,category=_reason(error.reason);return category,'URLError',None,reason,number
    reason,number,category=_reason(error)
    if reason!='Unavailable':return category,reason,None,reason,number
    return 'internal','Exception',None,None,None

def _emit_error(error,stderr,started,clock):
    category,kind,status,reason,number=_classify(error)
    elapsed=clock()-started
    if not math.isfinite(elapsed)or elapsed<0:elapsed=0.0
    record={'schema':'rf2.provider.transport.error.v1','category':category,'type':kind,'httpStatus':status,'reasonType':reason,'errno':number,'elapsedSeconds':round(elapsed,6),'retryPerformed':False,'usage':'unknown'}
    # No exception strings, traceback, request, headers, body, path or config data.
    try:stderr.write(json.dumps(record,separators=(',',':'))+'\n')
    except Exception:pass
    return 1

def _json_object(raw,category):
    try:
        value=json.loads(raw.decode('utf-8'),parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
    except (UnicodeError,ValueError,RecursionError):raise TransportRefusal(category,'JSONError')from None
    if not isinstance(value,dict):raise TransportRefusal(category,'JSONObjectRequired')
    return value

def _key(text):
    if not isinstance(text,str)or len(text)>MAX_CONFIG:raise TransportRefusal('configuration','ConfigurationFormatError')
    matches=[]
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        if line.startswith('export '):line=line[7:].lstrip()
        if '='not in line:continue
        name,value=line.split('=',1)
        if name.strip()=='OPENAI_API_KEY':matches.append(value.strip())
    if len(matches)!=1:raise TransportRefusal('configuration','ConfigurationKeyError')
    value=matches[0]
    if len(value)>=2 and value[0]in ['"',"'"]and value[-1]==value[0]:value=value[1:-1]
    if not re.fullmatch(r'[A-Za-z0-9_-]{10,512}',value):raise TransportRefusal('configuration','ConfigurationValueError')
    return value

class NoProviderRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,file,code,message,headers,new_url):
        status=code if isinstance(code,int)and not isinstance(code,bool)and 100<=code<=599 else None
        raise TransportRefusal('redirect','RedirectRefused',status=status)

def _open_once(request,timeout):
    return urllib.request.build_opener(NoProviderRedirect()).open(request,timeout=timeout)

def _read_config(path):
    with Path(path).open(encoding='utf-8')as stream:return stream.read(MAX_CONFIG+1)

def run_remote(config_path,http_timeout,stdin,stdout,stderr,*,opener=None,read_config=None,clock=time.monotonic):
    """One selected POST. Streams/read_config/opener are injectable for offline tests."""
    started=clock()
    try:
        if not isinstance(http_timeout,int)or isinstance(http_timeout,bool)or not 1<=http_timeout<=180:raise TransportRefusal('arguments','TimeoutRangeError')
        raw=stdin.read(MAX_REQUEST+1)
        if not isinstance(raw,bytes)or len(raw)>MAX_REQUEST:raise TransportRefusal('payload','PayloadSizeError')
        _json_object(raw,'payload')
        try:config=(read_config or _read_config)(config_path)
        except Exception as error:
            reason,number,_=_reason(error)
            raise TransportRefusal('configuration','ConfigurationReadError',reason,number)from None
        key=_key(config)
        request=urllib.request.Request(ENDPOINT,data=raw,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
        with(opener or _open_once)(request,timeout=http_timeout)as response:
            body=response.read(MAX_RESPONSE+1)
        if not isinstance(body,bytes)or len(body)>MAX_RESPONSE:raise TransportRefusal('response','ResponseSizeError')
        value=_json_object(body,'response')
        # Fail closed if a provider ever reflects the credential in a success body.
        if key.encode()in body or key in json.dumps(value,ensure_ascii=False):raise TransportRefusal('response','CredentialReflectionError')
        try:wrote=stdout.write(body)
        except Exception as error:
            reason,number,_=_reason(error)
            raise TransportRefusal('output','OutputWriteError',reason,number)from None
        if wrote!=len(body):raise TransportRefusal('output','ShortWriteError')
        try:stdout.flush()
        except Exception as error:
            reason,number,_=_reason(error)
            raise TransportRefusal('output','OutputFlushError',reason,number)from None
        return 0
    except Exception as error:return _emit_error(error,stderr,started,clock)

def remote_command(http_timeout=180):
    if not isinstance(http_timeout,int)or isinstance(http_timeout,bool)or not 1<=http_timeout<=180:raise ValueError('Invalid HTTP timeout')
    host=os.environ.get('RF2_PROVIDER_SSH_HOST');config=os.environ.get('RF2_PROVIDER_REMOTE_ENV_FILE')
    if not isinstance(host,str)or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.@:-]{0,252}',host):raise ValueError('Explicit valid host alias required')
    if not isinstance(config,str)or not config.startswith('/')or any(ord(c)<32 or ord(c)==127 for c in config):raise ValueError('Explicit remote configuration file required')
    # Ship this exact stdlib helper in the SSH command, not a credential or config body.
    helper=Path(__file__).resolve().read_text()
    return ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8',host,'python3 -c '+shlex.quote(helper)+' '+shlex.quote(config)+' '+str(http_timeout)]

if __name__=='__main__':
    if len(sys.argv)!=3:
        raise SystemExit(_emit_error(TransportRefusal('arguments','ArgumentCountError'),sys.stderr,time.monotonic(),time.monotonic))
    try:budget=int(sys.argv[2])
    except(ValueError,TypeError):raise SystemExit(_emit_error(TransportRefusal('arguments','TimeoutRangeError'),sys.stderr,time.monotonic(),time.monotonic))
    raise SystemExit(run_remote(sys.argv[1],budget,sys.stdin.buffer,sys.stdout.buffer,sys.stderr))
