"""Single-call bounded supervisor. Import is inert; no credentials copied locally.

Unlike the historical controller this retains structured safe failures. There is
no retry. A timeout may still have provider usage and is never counted as zero.
"""
import json, subprocess, time
import provider_transport as transport

ERROR_KEYS = {'schema','category','type','httpStatus','reasonType','errno',
              'elapsedSeconds','retryPerformed','usage'}

def safe_error(stderr):
    """Only preserve the qualified helper's strictly typed error fields."""
    try:
        if not isinstance(stderr, bytes) or len(stderr)>4096:return None
        value=json.loads(stderr.decode('utf-8'))
        if not isinstance(value,dict) or set(value)!=ERROR_KEYS:return None
        if value['schema']!='rf2.provider.transport.error.v1':return None
        if value['category']not in ['http','dns','timeout','tls','network','internal','configuration','payload','response','arguments','redirect','output']:return None
        if value['type']not in ['HTTPError','URLError','gaierror','TimeoutError','SSLError','OSError','Exception','JSONError','JSONObjectRequired','ConfigurationReadError','ConfigurationFormatError','ConfigurationKeyError','ConfigurationValueError','PayloadSizeError','ResponseSizeError','CredentialReflectionError','ArgumentCountError','TimeoutRangeError','RedirectRefused','OutputWriteError','OutputFlushError','ShortWriteError']:return None
        reason=value['reasonType']
        if reason not in [None,'HTTPStatus','gaierror','TimeoutError','SSLError','OSError','Unavailable']:return None
        status=value['httpStatus'];number=value['errno'];elapsed=value['elapsedSeconds']
        if status is not None and (type(status)is not int or not 100<=status<=599):return None
        if number is not None and (type(number)is not int or not -65535<=number<=65535):return None
        if type(elapsed)not in (int,float) or not 0<=elapsed<=100000:return None
        if value['retryPerformed']is not False or value['usage']!='unknown':return None
        return value
    except (ValueError,UnicodeError,KeyError,TypeError):return None

def valid_usage(value):
    if not isinstance(value,dict):return None
    fields=['prompt_tokens','completion_tokens','total_tokens']
    if any(type(value.get(k))is not int or not 0<=value[k]<=1000000000 for k in fields):return None
    if value['total_tokens']!=value['prompt_tokens']+value['completion_tokens']:return None
    # Preserve reported details, but only when they are bounded numeric mappings.
    result={k:value[k]for k in fields}
    for name in ['prompt_tokens_details','completion_tokens_details']:
        detail=value.get(name)
        if isinstance(detail,dict):
            result[name]={k:v for k,v in detail.items()if isinstance(k,str)and len(k)<80 and type(v)is int and 0<=v<=1000000000}
    return result

def invoke(payload, *, http_timeout=180, outer_timeout=420, runner=None,
           command=None, clock=time.monotonic):
    """Return (receipt, complete_response_or_None); caller persists raw request.

    Explicit command injection is for offline controls. Live callers leave it
    unset and select the authorized SSH host/config reference via environment.
    No partial response or arbitrary SSH stderr is promoted as a model result.
    """
    if type(outer_timeout)is not int or not http_timeout<outer_timeout<=600:
        raise ValueError('Invalid bounded outer timeout')
    if not isinstance(payload,bytes)or len(payload)>transport.MAX_REQUEST:
        raise ValueError('Request must be bounded JSON bytes')
    transport._json_object(payload,'payload')
    started=clock()
    receipt={'transportExit':None,'usage':None,'usageKnown':False,
             'automaticRetry':False,'sourceExecuted':False,'outerTimeout':outer_timeout,
             'httpTimeout':http_timeout}
    response=None
    try:
        q=(runner or subprocess.run)(command if command is not None else transport.remote_command(http_timeout),
             input=payload,capture_output=True,timeout=outer_timeout)
        receipt['transportExit']=q.returncode
        if q.returncode:
            receipt['failure']='transport failure'
            receipt['transportError']=safe_error(q.stderr)
        else:
            if not isinstance(q.stdout,bytes)or len(q.stdout)>transport.MAX_RESPONSE:
                raise ValueError('Response size')
            response=transport._json_object(q.stdout,'response')
            receipt['usage']=valid_usage(response.get('usage'))
            receipt['usageKnown']=receipt['usage']is not None
    except subprocess.TimeoutExpired:
        receipt.update(failure='outer transport deadline exceeded',transportError=None)
    except (Exception,KeyboardInterrupt) as error:
        receipt.update(failure='supervisor '+type(error).__name__,transportError=None)
        response=None
    receipt['elapsedSeconds']=max(0,clock()-started)
    return receipt,response
