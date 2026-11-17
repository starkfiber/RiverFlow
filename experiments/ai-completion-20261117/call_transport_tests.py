"""Offline supervisor controls; no SSH, config read, or provider request."""
import io,json,subprocess,unittest
import call_transport as m

RAW=b'{"messages":[]}'
SECRET='DO_NOT_SAVE_CREDENTIAL_OR_PATH'
ERROR={'schema':'rf2.provider.transport.error.v1','category':'http','type':'HTTPError',
       'httpStatus':429,'reasonType':'HTTPStatus','errno':None,'elapsedSeconds':0.1,
       'retryPerformed':False,'usage':'unknown'}
class Controls(unittest.TestCase):
    def invoke(self,result=None,error=None):
        calls=[]
        def run(*args,**kw):
            calls.append((args,kw))
            if error:raise error
            return result
        ticks=iter([1.0,2.0])
        receipt,response=m.invoke(RAW,runner=run,command=['OFFLINE-NOT-EXECUTED'],clock=lambda:next(ticks))
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][1]['timeout'],420)
        self.assertFalse(receipt['automaticRetry']);self.assertFalse(receipt['sourceExecuted'])
        self.assertEqual(receipt['elapsedSeconds'],1)
        return receipt,response
    def test_success_usage(self):
        usage={'prompt_tokens':3,'completion_tokens':4,'total_tokens':7,'completion_tokens_details':{'reasoning_tokens':2}}
        body={'choices':[],'usage':usage}
        r,d=self.invoke(subprocess.CompletedProcess([],0,json.dumps(body).encode(),b''))
        self.assertEqual(d,body);self.assertEqual(r['usage'],usage);self.assertTrue(r['usageKnown'])
    def test_unknown_usage_is_not_zero(self):
        for usage in [None,{}, {'prompt_tokens':1,'completion_tokens':1,'total_tokens':3}, {'prompt_tokens':True,'completion_tokens':0,'total_tokens':1}]:
            r,d=self.invoke(subprocess.CompletedProcess([],0,json.dumps({'usage':usage}).encode(),b''))
            self.assertIsNone(r['usage']);self.assertFalse(r['usageKnown']);self.assertIsNotNone(d)
    def test_helper_error(self):
        r,d=self.invoke(subprocess.CompletedProcess([],1,b'{"usage":{"total_tokens":9}}',json.dumps(ERROR).encode()))
        self.assertIsNone(d);self.assertEqual(r['transportError'],ERROR);self.assertIsNone(r['usage'])
    def test_ssh_stderr_not_copied(self):
        for err in [SECRET.encode(),json.dumps({'failure':SECRET}).encode(),json.dumps({**ERROR,'extra':SECRET}).encode(),b'x'*5000]:
            r,d=self.invoke(subprocess.CompletedProcess([],255,b'',err));self.assertIsNone(r['transportError']);self.assertNotIn(SECRET,json.dumps(r))
    def test_timeout_partial_not_accepted(self):
        r,d=self.invoke(error=subprocess.TimeoutExpired('secret',420,output=b'{"usage":{"total_tokens":9}}',stderr=SECRET.encode()))
        self.assertIsNone(d);self.assertIsNone(r['usage']);self.assertIsNone(r['transportExit']);self.assertIn('deadline',r['failure']);self.assertNotIn(SECRET,json.dumps(r))
    def test_invalid_success_not_accepted(self):
        for body in [b'[]',b'{',b'\xff',b'{"value":NaN}',b'x'*(m.transport.MAX_RESPONSE+1)]:
            r,d=self.invoke(subprocess.CompletedProcess([],0,body,b''));self.assertIsNone(d);self.assertIn('failure',r);self.assertIsNone(r['usage'])
    def test_supervisor_exception_sanitized(self):
        r,d=self.invoke(error=OSError(SECRET));self.assertIsNone(d);self.assertNotIn(SECRET,json.dumps(r));self.assertIsNone(r['usage'])
    def test_refuse_before_dispatch(self):
        def run(*args,**kw):self.fail('must not dispatch')
        for payload in ['{}',b'[]',b'{',b'x'*(m.transport.MAX_REQUEST+1)]:
            with self.assertRaises(Exception):m.invoke(payload,runner=run)
        for limit in [0,180,601,True]:
            with self.assertRaises(ValueError):m.invoke(RAW,outer_timeout=limit,runner=run)
    def test_safe_error_types(self):
        for key,value in [('httpStatus',True),('errno',False),('elapsedSeconds',float('nan')),('reasonType',SECRET+'\n'),('retryPerformed',True),('usage','zero')]:
            self.assertIsNone(m.safe_error(json.dumps({**ERROR,key:value}).encode()))
    def test_usage_details_filtered(self):
        self.assertEqual(m.valid_usage({'prompt_tokens':1,'completion_tokens':2,'total_tokens':3,'prompt_tokens_details':{'cached_tokens':1,'bad':SECRET,'negative':-1}}),{'prompt_tokens':1,'completion_tokens':2,'total_tokens':3,'prompt_tokens_details':{'cached_tokens':1}})

if __name__=='__main__':
    import argparse,hashlib,pathlib,time
    p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    log=io.StringIO();start=time.monotonic();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    (a.out/'unittest.log').write_text(log.getvalue())
    receipt={'schema':'rf2.completion.call-supervisor-offline.v1','allPassed':result.wasSuccessful(),'methods':result.testsRun,'realNetworkCalls':0,'realCredentialsRead':False,'elapsedSeconds':time.monotonic()-start,'files':{name:hashlib.sha256((pathlib.Path(__file__).parent/name).read_bytes()).hexdigest()for name in ['call_transport.py','call_transport_tests.py','provider_transport.py']}}
    (a.out/'RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));raise SystemExit(0 if result.wasSuccessful()else 1)
