"""Offline fake socket/TLS/HTTP tests. No provider call or credential file read."""
import argparse,hashlib,importlib.util,io,json,socket,ssl,time,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('phase_transport',Path(__file__).parent/'provider_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SECRET='RF2_SYNTHETIC_CREDENTIAL_MARKER_12345678'
RAW=b'{"model":"fake","messages":[]}'
BODY=b'{"choices":[],"usage":{"total_tokens":1}}'
class Socket:
    def __init__(self,fail=None):self.fail=fail;self.connected=[];self.sent=[];self.timeouts=[];self.closed=False
    def settimeout(self,value):self.timeouts.append(value)
    def connect(self,address):
        self.connected.append(address)
        if self.fail=='connect':raise TimeoutError(110,SECRET)
    def sendall(self,raw):
        self.sent.append(raw)
        if self.fail=='send':raise BrokenPipeError(32,SECRET)
    def close(self):self.closed=True
class Context:
    check_hostname=True;verify_mode=ssl.CERT_REQUIRED
    def __init__(self,sock,fail=None):self.sock=sock;self.fail=fail;self.calls=[]
    def wrap_socket(self,sock,server_hostname):
        self.calls.append(server_hostname)
        if self.fail=='tls':raise TimeoutError(SECRET)
        return self.sock
class Response:
    def __init__(self,fail=None,status=200,body=BODY):self.fail=fail;self.status=status;self.body=body;self.closed=False;self.length=0
    def begin(self):
        if self.fail=='headers':raise TimeoutError(SECRET)
    def read(self,limit):
        if self.fail=='body':raise TimeoutError(SECRET)
        if self.fail=='incomplete':self.length=100
        return self.body[:limit]
    def close(self):self.closed=True
def invoke(fail=None,status=200,body=BODY,context_verify=True,raw=RAW,config='OPENAI_API_KEY='+SECRET,stdout=None):
    sock=Socket(fail);context=Context(sock,fail);context.check_hostname=context_verify;response=Response(fail,status,body);out=stdout or io.BytesIO();err=io.StringIO();created=[];dns=[]
    def resolver(*args,**kwargs):
        dns.append(args)
        if fail=='dns':raise socket.gaierror(-2,SECRET)
        return[(socket.AF_INET,socket.SOCK_STREAM,6,'',('192.0.2.10',443)),(socket.AF_INET,socket.SOCK_STREAM,6,'',('192.0.2.11',443))]
    def factory(*args):created.append(args);return sock
    ticks=iter([10.,10.5]);code=m.run_remote('/fake/'+SECRET,180,io.BytesIO(raw),out,err,read_config=lambda _:config,resolver=resolver,socket_factory=factory,tls_context=context,response_factory=lambda _:response,clock=lambda:next(ticks))
    error=json.loads(err.getvalue())if err.getvalue()else None;output=out.getvalue()
    assert SECRET not in err.getvalue()and SECRET.encode()not in output
    return code,output,error,sock,context,response,created,dns
class Tests(unittest.TestCase):
    def test_success_one_post(self):
        code,out,error,sock,context,response,created,dns=invoke();self.assertEqual(code,0);self.assertEqual(out,BODY);self.assertIsNone(error);self.assertEqual(len(created),1);self.assertEqual(len(sock.connected),1);self.assertEqual(sock.connected[0],('192.0.2.10',443));self.assertEqual(len(sock.sent),1);self.assertTrue(sock.sent[0].startswith(b'POST /chat/completions HTTP/1.1\r\nHost: api.deepseek.com\r\n'));self.assertTrue(sock.sent[0].endswith(RAW));self.assertEqual(context.calls,['api.deepseek.com']);self.assertEqual(sock.timeouts,[8,180]);self.assertTrue(sock.closed);self.assertTrue(response.closed)
    def test_stages_and_no_retry(self):
        for phase,sent in [('dns',False),('connect',False),('tls',False),('send',True),('headers',True),('body',True)]:
            with self.subTest(phase=phase):
                code,out,error,sock,context,response,created,dns=invoke(fail=phase)
                self.assertEqual(code,1);self.assertEqual(out,b'');self.assertEqual(error['phase'],phase);self.assertEqual(error['requestMayHaveBeenSent'],sent);self.assertFalse(error['retryPerformed']);self.assertEqual(error['usage'],'unknown');self.assertLessEqual(len(created),1);self.assertLessEqual(len(sock.connected),1);self.assertEqual(len(sock.sent),1 if sent else 0)
    def test_connect_vs_read(self):
        connect=invoke('connect')[2];read=invoke('body')[2];self.assertEqual(connect['errno'],110);self.assertEqual(connect['phase'],'connect');self.assertEqual(read['phase'],'body');self.assertIsNone(read['errno'])
    def test_http_refusals_not_retried(self):
        for status in [301,307,401,429,500]:
            code,out,error,sock,*_=invoke(status=status);self.assertEqual(code,1);self.assertEqual(error['phase'],'headers');self.assertEqual(error['httpStatus'],status);self.assertTrue(error['requestMayHaveBeenSent']);self.assertEqual(len(sock.sent),1)
    def test_tls_verification_required(self):
        code,out,error,sock,context,*_=invoke(context_verify=False);self.assertEqual(error['type'],'TLSVerificationRequired');self.assertEqual(error['phase'],'tls');self.assertEqual(len(sock.sent),0);self.assertFalse(error['requestMayHaveBeenSent'])
    def test_reflection(self):
        code,out,error,*_=invoke(body=json.dumps({'secret':SECRET}).encode());self.assertEqual(code,1);self.assertEqual(error['type'],'CredentialReflectionError');self.assertEqual(out,b'')
    def test_invalid_response(self):
        for body in [b'[]',b'{',b'\xff',b'{"n":NaN}',b'x'*(m.MAX_RESPONSE+1)]:
            code,out,error,sock,*_=invoke(body=body);self.assertEqual(code,1);self.assertEqual(error['phase'],'body');self.assertEqual(len(sock.sent),1)
    def test_incomplete_content_length(self):
        code,out,error,sock,*_=invoke(fail='incomplete');self.assertEqual(code,1);self.assertEqual(error['type'],'IncompleteResponseError');self.assertEqual(out,b'');self.assertEqual(len(sock.sent),1)
    def test_payload_before_network(self):
        for raw in [b'{',b'[]',b'x'*(m.MAX_REQUEST+1)]:
            code,out,error,sock,ctx,response,created,dns=invoke(raw=raw);self.assertEqual(error['phase'],'payload');self.assertFalse(error['requestMayHaveBeenSent']);self.assertEqual(dns,[]);self.assertEqual(created,[])
    def test_bad_config_before_network(self):
        code,out,error,sock,ctx,response,created,dns=invoke(config='');self.assertEqual(error['phase'],'configuration');self.assertFalse(error['requestMayHaveBeenSent']);self.assertEqual(dns,[])
    def test_output_failure_still_sent(self):
        class BrokenOutput(io.BytesIO):
            def flush(self):raise BrokenPipeError(32,SECRET)
        code,out,error,sock,*_=invoke(stdout=BrokenOutput());self.assertEqual(error['phase'],'output');self.assertTrue(error['requestMayHaveBeenSent']);self.assertEqual(error['type'],'OutputFlushError');self.assertEqual(len(sock.sent),1)
    def test_supervisor_preserves_safe_phase(self):
        spec=importlib.util.spec_from_file_location('phase_supervisor',Path(__file__).parent/'call_transport.py');supervisor=importlib.util.module_from_spec(spec);spec.loader.exec_module(supervisor)
        error=invoke('connect')[2];self.assertEqual(supervisor.safe_error(json.dumps(error).encode()),error)
        for edit in [{'phase':SECRET},{'peer':{'family':'IPv4','address':SECRET}},{'requestMayHaveBeenSent':SECRET},{'unexpected':SECRET}]:
            self.assertIsNone(supervisor.safe_error(json.dumps({**error,**edit}).encode()))
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);log=io.StringIO();start=time.monotonic();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));(a.out/'unittest.log').write_text(log.getvalue());record={'schema':'rf2.transport-phases.offline.v1','allPassed':result.wasSuccessful(),'testMethods':result.testsRun,'elapsedSeconds':time.monotonic()-start,'providerCalls':0,'realCredentialReads':False,'sourceSHA256':hashlib.sha256((Path(__file__).parent/'provider_transport.py').read_bytes()).hexdigest(),'supervisorSHA256':hashlib.sha256((Path(__file__).parent/'call_transport.py').read_bytes()).hexdigest(),'testSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(a.out/'RESULTS.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));return 0 if result.wasSuccessful()else 1
if __name__=='__main__':raise SystemExit(main())
