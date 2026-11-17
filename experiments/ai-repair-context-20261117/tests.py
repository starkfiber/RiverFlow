"""Offline source-only controls. No compiler, provider, imports or program runs."""
import argparse,hashlib,io,json,time,unittest
from pathlib import Path
import context as m
def codes(text):return [x['code']for x in m.collect(text.encode())['diagnostics']]
class Controls(unittest.TestCase):
    def test_all_requested_mistakes(self):
        self.assertEqual(codes('fn main(argc,argv)\n let x=0\n let x=1\n if x and argc or argv\n  break\n else if x\n  do try f()\n end\nend\n'),['RF2A_DUPLICATE_LOCAL','RF2A_BOOLEAN_WORD','RF2A_BOOLEAN_WORD','RF2A_BREAK','RF2A_ELSE_IF','RF2A_TRY_UNTYPED'])
    def test_valid_flow(self):
        self.assertEqual(codes('fn f():IO\n let x=try op()\n return ok(x)\nend\nfn main(a,b)\n let x=0\n if all(a,b)\n  set x=1\n else\n  if a|b\n   set x=2\n  end\n end\n handle f()\n ok value\n  return value\n err cause\n  return 2\n end\n return 0\nend\n'),[])
    def test_strings_comments(self):
        self.assertEqual(codes('fn main(a,b)\n # break and or else if try let x\n do out("break and or # else if try let x")\n do out("escaped quote: \\" and break")\n return 0\nend\n'),[])
    def test_escaped_backslash_quote(self):
        self.assertEqual(codes('fn f()\n let s="backslash: \\\\" # break\n return 0\nend\n'),[])
    def test_function_namespaces(self):
        self.assertEqual(codes('fn a(x)\n let y=1\n return y\nend\nfn b(x)\n let y=1\n return y\nend\n'),[])
    def test_parameter_collision(self):self.assertEqual(codes('fn a(x:Thing)\n let x=1\nend\n'),['RF2A_DUPLICATE_LOCAL'])
    def test_branch_redeclaration(self):self.assertEqual(codes('fn a()\n if 1\n let x=1\n else\n let x=2\n end\nend\n'),['RF2A_DUPLICATE_LOCAL'])
    def test_nested_handlers_unique(self):
        self.assertEqual(codes('fn a():IO\n handle f()\n ok v\n  handle g()\n  ok nested_v\n  err nested_e\n  end\n err e\n end\n return ok(0)\nend\n'),[])
    def test_nested_handlers_duplicate(self):
        self.assertEqual(codes('fn a():IO\n handle f()\n ok v\n  handle g()\n  ok v\n  err nested_e\n  end\n err e\n end\n return ok(0)\nend\n'),['RF2A_DUPLICATE_LOCAL'])
    def test_handle_parameter_collision(self):self.assertEqual(codes('fn a(v):IO\n handle f()\n ok v\n err e\n end\n return ok(0)\nend\n'),['RF2A_DUPLICATE_LOCAL'])
    def test_other_result_annotation_not_claimed(self):self.assertEqual(codes('fn f():Other\n do try op()\nend\n'),[])
    def test_whitespace_inline_else(self):self.assertEqual(codes('fn f()\n if 1\n else\t if 2\n end\n end\nend\n'),['RF2A_ELSE_IF'])
    def test_identifier_substrings(self):self.assertEqual(codes('fn f()\n let candy=0\n let origin=0\n let breakthrough=0\n return candy|origin|breakthrough\nend\n'),[])
    def test_boolean_identifier_not_operator(self):self.assertEqual(codes('fn f()\n let and=1\n let or=2\n return all(and,or)\nend\n'),[])
    def test_locations_utf8_bytes(self):
        text='fn f()\n let x="漢"\n let x=1\n if x and 1\nend\n';r=m.collect(text.encode());self.assertEqual(r['diagnostics'][0]['line'],3);self.assertEqual(r['diagnostics'][0]['byteColumn'],6);self.assertEqual(r['sourceSHA256'],hashlib.sha256(text.encode()).hexdigest())
    def test_previous_location(self):self.assertEqual(m.collect(b'fn f()\n let x=0\n let x=1\nend')['diagnostics'][0]['previous'],{'line':2,'byteColumn':6})
    def test_reserved_binding(self):self.assertEqual(codes('fn f()\n let end=1\nend\n'),['RF2A_RESERVED_BINDING'])
    def test_truncation(self):
        r=m.collect(('fn f()\n'+' break\n'*200+'end\n').encode());self.assertEqual(len(r['diagnostics']),128);self.assertEqual(r['diagnosticsObserved'],200);self.assertTrue(r['truncated'])
    def test_invalid_limits(self):
        for value in [0,129,True]:
            with self.assertRaises(ValueError):m.collect(b'',max_diagnostics=value)
        with self.assertRaises(ValueError):m.collect(b'x'*65537)
        with self.assertRaises(ValueError):m.collect('text')
        with self.assertRaises(UnicodeError):m.collect(b'\xff')
    def test_unterminated_string(self):self.assertEqual(codes('fn f()\n let s="unterminated\n break\n'),['RF2A_LEXICAL_INCOMPLETE'])
    def test_empty_and_malformed(self):
        self.assertEqual(codes(''),[]);self.assertEqual(codes('end\nlet x=1\n'),[]);self.assertEqual(codes('fn\n break\n'),[])
    def test_new_fn_recovers_incomplete_previous(self):self.assertEqual(codes('fn a()\n if 1\nfn b()\n break\nend\n'),['RF2A_BREAK'])
    def test_no_rewrite(self):
        source=b'fn f()\n break\nend\n';copy=bytes(source);r=m.collect(source);self.assertEqual(source,copy);self.assertTrue(r['advisoryOnly']);self.assertFalse(r['nativeAcceptance'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls));(a.out/'unittest.log').write_text(log.getvalue())
    receipt={'schema':'rf2.ai.repair-context.controls.v1','allPassed':result.wasSuccessful(),'testMethods':result.testsRun,'elapsedSeconds':time.monotonic()-start,'sourceSHA256':hashlib.sha256((Path(__file__).parent/'context.py').read_bytes()).hexdigest(),'testSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'nativeRuns':0,'providerCalls':0,'scope':'Bounded lexical heuristic controls, not compiler acceptance'}
    (a.out/'RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));return 0 if result.wasSuccessful()else 1
if __name__=='__main__':raise SystemExit(main())
