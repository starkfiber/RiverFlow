"""Synthetic unit controls for source/model/build advice boundaries; no provider calls."""
import copy,json,os,subprocess,tempfile,unittest
from pathlib import Path
import harness as h
class EvidenceControls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  (self.root/'piece.flow').write_text('profile RF2_SYSTEM_A64_V1\n# தமிழ்\nfn main(argc,argv)\n return 0\nend\n')
  subprocess.run(['git','init','-q',str(self.root)],check=True)
  subprocess.run(['git','add','piece.flow'],cwd=self.root,check=True)
  self.manifest=h.inventory(self.root);f=self.manifest['files'][0]
  self.body=dict(schema='rf2.review-proposals.v1',contextSHA256=h.digest(h.canonical(self.manifest)),findings=[dict(path=f['path'],line=3,sourceSHA256=f['sha256'],hypothesis='Test-only possible failure',nextTest='Run isolated oracle')])
 def tearDown(self):self.tmp.cleanup()
 def response(self,body=None,finish='stop'):
  return dict(choices=[dict(finish_reason=finish,message=dict(content=json.dumps(body or self.body)))])
 def test_valid_proposal_has_no_execution_authority(self):
  x=h.review_gate(self.root,self.manifest,self.response());self.assertEqual(x['patchesApplied'],0);self.assertFalse(x['securityVerified']);self.assertEqual(x['state'],'reviewable-proposals-only')
 def test_context_drift_refuses(self):
  (self.root/'piece.flow').write_text('changed');self.assertRaises(ValueError,h.review_gate,self.root,self.manifest,self.response())
 def test_unicode_line_accounting(self):
  (self.root/'piece.flow').write_text('line\u2028line\n');m=h.inventory(self.root);b=dict(self.body,contextSHA256=h.digest(h.canonical(m)),findings=[]);h.review_gate(self.root,m,self.response(b))
 def test_empty_context_is_explicit(self):
  subprocess.run(['git','rm','--cached','-q','-f','piece.flow'],cwd=self.root,check=True);self.assertEqual(h.inventory(self.root)['files'],[])
 def test_skipped_fifo_has_no_coverage(self):
  pipe=self.root/'pipe.flow';pipe.write_text('tracked regular source');subprocess.run(['git','add','pipe.flow'],cwd=self.root,check=True);pipe.unlink();os.mkfifo(pipe)
  x=h.inventory(self.root);self.assertEqual(len(x['skipped']),1);self.assertIsNone(x['automaticFindingCount'])
 def test_symlink_refuses(self):
  (self.root/'link.flow').symlink_to(self.root/'piece.flow');self.assertRaises(OSError,h.read_regular,self.root/'link.flow')
 def test_file_budget_refuses(self):
  self.assertRaises(ValueError,h.read_regular,self.root/'piece.flow',1)
 def test_duplicate_json_refuses(self):self.assertRaises(ValueError,h.parse,'{"x":1,"x":2}')
 def test_nonfinite_json_refuses(self):
  for value in('NaN','Infinity','-Infinity'):self.assertRaises(ValueError,h.parse,value)
 def test_deep_json_refuses(self):
  self.assertRaises(ValueError,h.parse,'['*34+'0'+']'*34)
  self.assertRaises(ValueError,h.parse,'['*2000+'0'+']'*2000)
 def test_provider_failures(self):
  for finish in('length','content_filter','tool_calls',None):
   with self.subTest(finish=finish):self.assertRaises(ValueError,h.review_gate,self.root,self.manifest,self.response(finish=finish))
  for response in({},dict(choices=[]),dict(choices=[{}]),dict(choices=[dict(message=None,finish_reason='stop')])):
   with self.subTest(response=response):self.assertRaises(ValueError,h.review_gate,self.root,self.manifest,response)
 def test_bad_model_json_refuses(self):
  q=self.response();q['choices'][0]['message']['content']='not JSON';self.assertRaises(ValueError,h.review_gate,self.root,self.manifest,q)
 def test_wrong_context_refuses(self):
  b=copy.deepcopy(self.body);b['contextSHA256']='0'*64;self.assertRaises(ValueError,h.review_gate,self.root,self.manifest,self.response(b))
 def test_findings_outside_source_refuse(self):
  for key,value in [('path','../outside.flow'),('path','other.flow'),('line',0),('line',1000),('line',True),('sourceSHA256','0'*64),('hypothesis',''),('nextTest',None)]:
   with self.subTest(key=key,value=value):
    b=copy.deepcopy(self.body);b['findings'][0][key]=value;self.assertRaises(ValueError,h.review_gate,self.root,self.manifest,self.response(b))
 def test_injected_command_schema_refuses(self):
  b=dict(self.body,execute='rm anything');self.assertRaises(ValueError,h.review_gate,self.root,self.manifest,self.response(b))
 def test_finding_budget(self):
  b=dict(self.body,findings=self.body['findings']*21);self.assertRaises(ValueError,h.review_gate,self.root,self.manifest,self.response(b))
 def sample(self,ratio=1):
  return dict(workloads=[dict(rows=[dict(clean=dict(ms=10,sha256='a'*64),cache=dict(ms=10*ratio,sha256='a'*64))for _ in range(5)])])
 def test_route_retains_clean_on_noise_or_loss(self):
  for ratio in(.99,1,1.25):self.assertEqual(h.select_build(self.sample(ratio))['workloads'][0]['recommendedRoute'],'clean')
 def test_route_requires_material_paired_gain(self):
  x=h.select_build(self.sample(.8));self.assertTrue(x['advisoryOnly']);self.assertEqual(x['workloads'][0]['recommendedRoute'],'explicit-reuse-candidate')
 def test_route_rejects_mismatched_images(self):
  m=self.sample(.8);m['workloads'][0]['rows'][0]['cache']['sha256']='b'*64;self.assertRaises(ValueError,h.select_build,m)
 def test_route_rejects_bad_samples(self):
  for value in(0,-1,float('nan'),float('inf'),True,'1'):
   with self.subTest(value=value):
    m=self.sample();m['workloads'][0]['rows'][0]['clean']['ms']=value;self.assertRaises(ValueError,h.select_build,m)
 def test_route_rejects_too_few_samples(self):
  m=self.sample();m['workloads'][0]['rows'].pop();self.assertRaises(ValueError,h.select_build,m)
if __name__=='__main__':unittest.main(verbosity=2)
