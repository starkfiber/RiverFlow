"""Pure amendment prompt/selection tests, no inference or execution."""
from pathlib import Path
import importlib.util,json,tempfile,unittest
p=Path(__file__).with_name('routing_campaign.py');s=importlib.util.spec_from_file_location('amended_route',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Controls(unittest.TestCase):
 def test_explicit_definitions_all_arms(self):
  for task,condition in m.router.ORDER:
   v=m.corrected_payload(task,condition);text=v['messages'][1]['content'];self.assertIn('IMPLEMENTATION DEFINITIONS',text);self.assertIn(json.dumps({'requestedImplementation':condition}),text);self.assertIn('text_report_entry',text);self.assertEqual(v['max_tokens'],1024)
 def test_feedback_repair(self):
  prior={'capability':'log-severity','implementation':'cli'};v=m.corrected_payload('C','manual',prior,'Actual rejection');text=v['messages'][1]['content'];self.assertIn(json.dumps(prior),text);self.assertIn('Actual rejection',text);self.assertIn('previous selection remains a recorded failure',text)
 def test_missing_receipt_counts_unknown(self):
  with tempfile.TemporaryDirectory()as temp:
   root=Path(temp)
   for name in ['attempt-1','attempt-2']:
    folder=root/name;folder.mkdir();(folder/'CALL-STARTED.json').write_text('{}')
   (root/'attempt-1/RECEIPT.json').write_text(json.dumps({'usage':{'prompt_tokens':6,'completion_tokens':4,'total_tokens':10},'elapsedSeconds':2}))
   rows=m.phase_records(root);cost=m.phase_cost(rows)
   self.assertEqual(len(rows),2);self.assertEqual(cost['requests'],2);self.assertEqual(cost['unknownUsageRequests'],1);self.assertEqual(cost['knownProviderTotalTokens'],10)
   self.assertEqual(cost['knownObservationSeconds'],2);self.assertEqual(cost['unknownTimingRequests'],1);self.assertNotIn('observedRequestSeconds',cost)
   self.assertIsNone(rows[1]['elapsedSeconds']);self.assertTrue(rows[1]['receiptMissing'])
 def test_oracle_unchanged(self):
  wrong={'capability':'log-severity','implementation':'cli'};self.assertEqual(m.router.selection(json.dumps(wrong)),wrong);self.assertNotEqual(wrong,{'capability':'log-severity','implementation':'manual'})
if __name__=='__main__':unittest.main()
