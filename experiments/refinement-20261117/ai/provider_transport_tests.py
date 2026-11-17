"""Offline-only stdlib controls; never opens a provider connection or real config."""
from pathlib import Path
import argparse,contextlib,hashlib,importlib.util,io,json,os,socket,ssl,subprocess,sys,tempfile,time,unittest,urllib.error
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_transport',HERE/'provider_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SECRET='RF2_SECRET_MARKER_NEVER_LOG_123456789'
RAW=b'{"model":"synthetic-test","messages":[]}'
CONFIG='IGNORED_SETTING=no\nOPENAI_API_KEY="'+SECRET+'"\n'
ROWS=[]
class Response:
    def __init__(self,body):self.body=body;self.limit=None;self.closed=False
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def read(self,limit):self.limit=limit;return self.body[:limit]
class ShortOutput:
    def write(self,data):return len(data)-1
class BrokenOutput:
    def write(self,data):raise BrokenPipeError(32,SECRET)
class TrackingOutput(io.BytesIO):
    def __init__(self):super().__init__();self.flush_count=0
    def flush(self):self.flush_count+=1;return super().flush()
class BrokenFlushOutput(io.BytesIO):
    def flush(self):raise BrokenPipeError(32,SECRET)
class BrokenErrors:
    def write(self,data):raise RuntimeError(SECRET)

def invoke(*,raw=RAW,config=CONFIG,error=None,body=b'{"choices":[],"usage":{"total_tokens":1}}',read_error=None,timeout=180,stdout=None,stderr=None):
    output=stdout if stdout is not None else io.BytesIO();errors=stderr if stderr is not None else io.StringIO();calls=[];reads=[];response=Response(body)
    def opener(request,timeout):
        calls.append((request,timeout))
        if error is not None:raise error
        return response
    def read_config(path):
        reads.append(path)
        if read_error is not None:raise read_error
        return config
    ticks=iter([100.0,100.25]);code=m.run_remote('/fake/'+SECRET,timeout,io.BytesIO(raw),output,errors,opener=opener,read_config=read_config,clock=lambda:next(ticks))
    out=output.getvalue()if hasattr(output,'getvalue')else b'';err=errors.getvalue()if hasattr(errors,'getvalue')else''
    assert SECRET not in err and SECRET.encode()not in out
    return code,out,err,calls,reads,response

class Controls(unittest.TestCase):
    def record(self,label,*,error_category=None,error_type=None,status=None,reason=None,number=None,network_calls=None,**kwargs):
        code,out,err,calls,reads,response=invoke(**kwargs)
        if error_category is None:
            self.assertEqual(code,0);self.assertEqual(err,'');self.assertTrue(out)
        else:
            self.assertEqual(code,1);self.assertEqual(out,b'');self.assertTrue(err.endswith('\n'));self.assertLess(len(err.encode()),1024);self.assertNotIn('Traceback',err)
            row=json.loads(err);self.assertEqual(row['category'],error_category);self.assertEqual(row['type'],error_type);self.assertEqual(row['httpStatus'],status);self.assertEqual(row['reasonType'],reason);self.assertEqual(row['errno'],number);self.assertEqual(row['elapsedSeconds'],0.25);self.assertFalse(row['retryPerformed']);self.assertEqual(row['usage'],'unknown')
        if network_calls is not None:self.assertEqual(len(calls),network_calls)
        ROWS.append({'name':label,'passed':True,'networkCalls':len(calls),'stderrCredentialFree':True})
        return code,out,err,calls,reads,response
    def test_success_and_request(self):
        row=self.record('success exact bytes',network_calls=1)
        request,budget=row[3][0];self.assertEqual(request.full_url,m.ENDPOINT);self.assertEqual(request.get_method(),'POST');self.assertEqual(request.data,RAW);self.assertEqual(request.get_header('Authorization'),'Bearer '+SECRET);self.assertEqual(budget,180);self.assertTrue(row[5].closed);self.assertEqual(row[5].limit,m.MAX_RESPONSE+1)
    def test_http_errors(self):
        for status in [401,429,500]:
            self.record('HTTP '+str(status),error=urllib.error.HTTPError('https://'+SECRET,status,SECRET,{},io.BytesIO(SECRET.encode())),error_category='http',error_type='HTTPError',status=status,reason='HTTPStatus',network_calls=1)
    def test_network_errors(self):
        cases=[('timeout direct',TimeoutError(SECRET),'timeout','TimeoutError','TimeoutError',None),('timeout URL',urllib.error.URLError(TimeoutError(SECRET)),'timeout','URLError','TimeoutError',None),('DNS URL',urllib.error.URLError(socket.gaierror(-2,SECRET)),'dns','URLError','gaierror',-2),('DNS direct',socket.gaierror(-2,SECRET),'dns','gaierror','gaierror',-2),('TLS',urllib.error.URLError(ssl.SSLError(1,SECRET)),'tls','URLError','SSLError',1),('connection refused',urllib.error.URLError(ConnectionRefusedError(61,SECRET)),'network','URLError','OSError',61),('opaque URL reason',urllib.error.URLError(SECRET),'network','URLError','Unavailable',None),('unexpected exception',RuntimeError(SECRET),'internal','Exception',None,None)]
        for name,error,cat,kind,reason,number in cases:self.record(name,error=error,error_category=cat,error_type=kind,reason=reason,number=number,network_calls=1)
    def test_redirect_refusal(self):
        for status in [301,302,303,307,308]:
            try:m.NoProviderRedirect().redirect_request(None,None,status,SECRET,{},'http://'+SECRET)
            except Exception as error:
                self.record('redirect '+str(status),error=error,error_category='redirect',error_type='RedirectRefused',status=status,network_calls=1)
            else:self.fail('redirect must refuse before new request')
    def test_payload_errors(self):
        for label,raw,kind in [('bad JSON',b'{'+SECRET.encode(),'JSONError'),('UTF8',b'\xff','JSONError'),('array',b'[]','JSONObjectRequired'),('NaN',b'{"x":NaN}','JSONError'),('empty',b'','JSONError'),('too large',b' '* (m.MAX_REQUEST+1),'PayloadSizeError'),('recursion',b'['*3000+b']'*3000,'JSONError')]:
            row=self.record(label,raw=raw,error_category='payload',error_type=kind,network_calls=0);self.assertEqual(row[4],[])
    def test_config_errors(self):
        for label,config,kind in [('missing key','OTHER='+SECRET,'ConfigurationKeyError'),('empty key','OPENAI_API_KEY=','ConfigurationValueError'),('duplicate key',CONFIG+CONFIG,'ConfigurationKeyError'),('bad key','OPENAI_API_KEY='+SECRET+'!','ConfigurationValueError'),('unmatched quote','OPENAI_API_KEY="'+SECRET,'ConfigurationValueError'),('config size','X'*(m.MAX_CONFIG+1),'ConfigurationFormatError')]:
            self.record(label,config=config,error_category='configuration',error_type=kind,network_calls=0)
        self.record('config read missing',read_error=FileNotFoundError(2,SECRET),error_category='configuration',error_type='ConfigurationReadError',reason='OSError',number=2,network_calls=0)
        self.record('config read opaque',read_error=RuntimeError(SECRET),error_category='configuration',error_type='ConfigurationReadError',reason='Unavailable',network_calls=0)
    def test_config_variants(self):
        for label,config in [('unquoted','OPENAI_API_KEY='+SECRET),('single quotes',"OPENAI_API_KEY='"+SECRET+"'"),('export','export OPENAI_API_KEY='+SECRET),('comments','# OPENAI_API_KEY=fake\n'+CONFIG)]:self.record(label,config=config,network_calls=1)
    def test_response_errors(self):
        for label,body,kind in [('response malformed',b'{'+SECRET.encode(),'JSONError'),('response array',b'[]','JSONObjectRequired'),('response UTF8',b'\xff','JSONError'),('response too large',b'x'*(m.MAX_RESPONSE+1),'ResponseSizeError'),('credential body',json.dumps({'echo':SECRET}).encode(),'CredentialReflectionError'),('credential escaped',('{"echo":"'+''.join('\\u%04x'%ord(c)for c in SECRET)+'"}').encode(),'CredentialReflectionError')]:self.record(label,body=body,error_category='response',error_type=kind,network_calls=1)
    def test_invalid_timeouts(self):
        for value in [0,181,True,'180']:
            self.record('invalid timeout '+str(value),timeout=value,error_category='arguments',error_type='TimeoutRangeError',network_calls=0)
    def test_output_failure(self):
        code,out,err,calls,reads,response=invoke(stdout=ShortOutput());self.assertEqual(code,1);self.assertEqual(json.loads(err)['category'],'output');self.assertEqual(len(calls),1);ROWS.append({'name':'short output detected','passed':True,'networkCalls':1,'stderrCredentialFree':True})
        code,out,err,calls,reads,response=invoke(stdout=BrokenOutput());self.assertEqual(code,1);self.assertEqual(json.loads(err)['category'],'output');self.assertEqual(json.loads(err)['type'],'OutputWriteError');self.assertEqual(json.loads(err)['errno'],32);self.assertEqual(len(calls),1);ROWS.append({'name':'broken output sanitized as output write failure','passed':True,'networkCalls':1,'stderrCredentialFree':True})
        code,*_=invoke(error=RuntimeError(SECRET),stderr=BrokenErrors());self.assertEqual(code,1);ROWS.append({'name':'broken error stream does not traceback','passed':True,'networkCalls':1,'stderrCredentialFree':True})
    def test_flush_handling(self):
        writer=TrackingOutput();code,out,err,calls,reads,response=invoke(stdout=writer)
        self.assertEqual(code,0);self.assertEqual(writer.flush_count,1);self.assertEqual(err,'');self.assertTrue(out);self.assertEqual(len(calls),1)
        ROWS.append({'name':'success explicitly flushed within guarded call','passed':True,'networkCalls':1,'stderrCredentialFree':True})
        writer=BrokenFlushOutput();code,out,err,calls,reads,response=invoke(stdout=writer)
        self.assertEqual(code,1);self.assertEqual(out,b'{"choices":[],"usage":{"total_tokens":1}}');record=json.loads(err);self.assertEqual(record['category'],'output');self.assertEqual(record['type'],'OutputFlushError');self.assertEqual(record['errno'],32);self.assertEqual(record['reasonType'],'OSError');self.assertNotIn('Traceback',err);self.assertEqual(len(calls),1)
        ROWS.append({'name':'flush failure sanitized after bytes written; success refused','passed':True,'networkCalls':1,'stderrCredentialFree':True})
    def test_local_command_builder(self):
        original=dict(os.environ)
        try:
            os.environ['RF2_PROVIDER_SSH_HOST']='reviewed-test-host';os.environ['RF2_PROVIDER_REMOTE_ENV_FILE']='/fake/path with spaces/config.env'
            args=m.remote_command();self.assertEqual(args[:6],['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','reviewed-test-host']);self.assertNotIn(SECRET,str(args));self.assertIn('python3 -c',args[-1]);ROWS.append({'name':'explicit SSH command only, no dispatch','passed':True,'networkCalls':0,'stderrCredentialFree':True})
            for host in ['-bad','bad host','host\ncommand','host;bad']:
                os.environ['RF2_PROVIDER_SSH_HOST']=host
                with self.assertRaises(ValueError):m.remote_command()
                ROWS.append({'name':'invalid host rejected','passed':True,'networkCalls':0,'stderrCredentialFree':True})
            os.environ['RF2_PROVIDER_SSH_HOST']='reviewed-test-host'
            for path in ['', 'relative/file', '/path\ncommand']:
                os.environ['RF2_PROVIDER_REMOTE_ENV_FILE']=path
                with self.assertRaises(ValueError):m.remote_command()
                ROWS.append({'name':'invalid config reference rejected','passed':True,'networkCalls':0,'stderrCredentialFree':True})
        finally:os.environ.clear();os.environ.update(original)
    def test_payload_builder_exact(self):
        spec=importlib.util.spec_from_file_location('payload_builder',HERE/'prepare_prompt_contract.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);self.assertEqual(hashlib.sha256(builder.payload()).hexdigest(),'014d18a700642dab98a1f71da790af16d8eead7ae10d327f143e6c30b88ef442');ROWS.append({'name':'reviewed payload exactly recreated','passed':True,'networkCalls':0,'stderrCredentialFree':True})
    def test_cli_bad_args_offline(self):
        for args,data in [([],b''),(['/fake','bad-timeout'],b''),(['/fake','180'],b'{bad')]:
            q=subprocess.run([sys.executable,'-B',str(HERE/'provider_transport.py'),*args],input=data,capture_output=True,timeout=5)
            self.assertEqual(q.returncode,1);self.assertEqual(q.stdout,b'');self.assertNotIn(b'Traceback',q.stderr);self.assertNotIn(SECRET.encode(),q.stderr);self.assertEqual(json.loads(q.stderr)['schema'],'rf2.provider.transport.error.v1');ROWS.append({'name':'standalone malformed invocation offline','passed':True,'networkCalls':0,'stderrCredentialFree':True})

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls));text=log.getvalue();assert SECRET not in text;(a.out/'unittest.log').write_text(text)
    record={'schema':'rf2.refinement.provider-transport-offline.v1','allPassed':result.wasSuccessful(),'unittestMethods':result.testsRun,'controls':len(ROWS),'rows':ROWS,'elapsedSeconds':time.monotonic()-start,'sourceSHA256':hashlib.sha256((HERE/'provider_transport.py').read_bytes()).hexdigest(),'testSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'payloadBuilderSHA256':hashlib.sha256((HERE/'prepare_prompt_contract.py').read_bytes()).hexdigest(),'realNetworkCalls':0,'realCredentialsRead':False,'existingFrozenTransportsModified':False,'scope':'Offline fake urlopen/config/streams only. Candidate not wired into closed studies; no historical root cause or live provider qualification.'};(a.out/'RESULTS.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items()if k!='rows'}));return 0 if result.wasSuccessful()else 1
if __name__=='__main__':raise SystemExit(main())
