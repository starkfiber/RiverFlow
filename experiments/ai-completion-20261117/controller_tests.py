"""Offline campaign contracts; no provider or native execution."""
from pathlib import Path
import importlib.util,json,unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('campaign',HERE/'campaign.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
class Controls(unittest.TestCase):
 def test_prompts(self):
  for task,condition in c.ORDER:
   with self.subTest(task=task,condition=condition):
    p=c.build_payload(task,condition);raw=json.dumps(p)
    self.assertNotIn('complete main.flow',raw)
    self.assertNotIn('golden-',raw)
    self.assertEqual(p['thinking'],{'type':'disabled'})
    self.assertEqual(p['max_tokens'],16384)
    self.assertEqual(p['temperature'],0)
    self.assertIn('actual RF2 program',raw)
    self.assertIn('Exact common output serialization contract',raw)
    self.assertIn('CONDITION: '+condition.upper(),raw)
    self.assertIn('<!doctype html>',raw)
 def test_repair_preserves_source_and_feedback(self):
  p=c.build_payload('C','manual','SOURCE-CONTROL',{'compileExit':2,'allPassed':False})
  content=p['messages'][1]['content'];self.assertIn('SOURCE-CONTROL',content);self.assertIn('"compileExit": 2',content)
 def test_usage_unknown_not_zero(self):
  got=c.cost([{'usage':{'total_tokens':10,'prompt_tokens':6,'completion_tokens':4},'elapsedSeconds':2},{'usage':None,'elapsedSeconds':3}])
  self.assertEqual(got['knownProviderTotalTokens'],10);self.assertEqual(got['unknownUsageRequests'],1);self.assertEqual(got['requestSeconds'],5)
 def test_modes_are_both_required(self):
  source=(HERE/'campaign.py').read_text();self.assertIn("for mode in ['plain','opt']",source);self.assertIn("len(result['runs'])==2 and all",source)
if __name__=='__main__':unittest.main()
