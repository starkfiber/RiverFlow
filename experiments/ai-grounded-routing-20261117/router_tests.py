"""Pure closed-catalogue controls: no provider, credentials or native execution."""
import importlib.util,json,unittest
from pathlib import Path
p=Path(__file__).with_name('router.py');s=importlib.util.spec_from_file_location('router',p);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Controls(unittest.TestCase):
 def test_all_four_choices(self):
  for task,cond in r.ORDER:
   v={'capability':r.CAPABILITY[task],'implementation':cond};self.assertEqual(r.selection(json.dumps(v)),v)
 def test_refusals(self):
  for raw in ['[]','null','{}','{"capability":"log-severity"}','{"capability":"log-severity","implementation":"cli","path":"/tmp/run"}','{"capability":"log-severity","capability":"identifier-duplicates","implementation":"cli"}','{"capability":"log-severity","implementation":"shell"}','{"capability":"/tmp/run","implementation":"cli"}','{"capability":true,"implementation":"cli"}','```json\n{}\n```','{"capability":"log-severity","implementation":NaN}']:
   with self.subTest(raw=raw):
    with self.assertRaises(ValueError):r.selection(raw)
 def test_unsupported(self):self.assertEqual(r.selection('{"capability":"unsupported","implementation":"none"}'),{'capability':'unsupported','implementation':'none'})
 def test_prompt_no_algorithm_source(self):
  for task,cond in r.ORDER:
   p=r.payload(task,cond);raw=json.dumps(p)
   self.assertEqual(p['max_tokens'],1024);self.assertEqual(p['thinking'],{'type':'disabled'})
   self.assertNotIn('fn text_report_fields',raw);self.assertNotIn('complete main.flow',raw);self.assertNotIn('Return one JSON object with only the key source',raw)
   self.assertNotIn('golden-',raw);self.assertIn('REQUESTED BEHAVIOR',raw);self.assertIn('REQUESTED PLUMBING',raw)
 def test_unknown_usage(self):
  v=r.cost([{'usage':None},{'usage':{'total_tokens':15,'prompt_tokens':10,'completion_tokens':5}}]);self.assertEqual(v['unknownUsageRequests'],1);self.assertEqual(v['knownProviderTotalTokens'],15)
if __name__=='__main__':unittest.main()
