from pathlib import Path
import subprocess,json,tempfile,hashlib,os,math,stat
import pymupdf
from pypdf import PdfReader
R=Path(__file__).resolve().parents[2];B=Path(os.environ.get('RF2_TEST_BINARY',str(R/'output/runtime-0.8-final/rf2')));plan=R/'capabilities/invoice.total.v1/quote.rf2';report={'passed':False,'documentCases':0,'pdfCases':0,'editCases':0,'refusals':0}
def run(args,ok=True):
 r=subprocess.run([str(B),'invoice']+[str(x)for x in args],capture_output=True,env={'PATH':'/nonexistent'});assert (r.returncode==0)==ok,(args,r.stdout,r.stderr);return r
with tempfile.TemporaryDirectory(prefix='rf2-workspace-')as name:
 d=Path(name)
 for n in [0,1,39,40,41,1000]:
  rows=[{'quantity':1,'unit_cents':100+i}for i in range(n)];lines=d/f'lines{n}.json';lines.write_text(json.dumps(rows));doc=d/f'doc{n}.json';a=json.loads(run(['save',plan,lines,doc]).stdout);assert json.loads(doc.read_text())['lines']==rows;assert stat.S_IMODE(doc.stat().st_mode)==0o600;assert json.loads(run(['inspect',doc]).stdout)==a;report['documentCases']+=1
  pdf=d/f'out{n}.pdf';run(['pdf',doc,pdf]);p=pymupdf.open(pdf);assert not p.is_repaired;assert len(PdfReader(pdf,strict=True).pages)==len(p);assert len(p)==max(1,math.ceil(n/40));assert 'Total: '+str(a['totalCents'])in p[-1].get_text()
  for page in p:
   for block in page.get_text('blocks'):assert block[0]>=0 and block[2]<595 and block[1]>=0 and block[3]<842
  assert all('xref'in pdf.read_text()for _ in [0]);report['pdfCases']+=1
  before=pdf.read_bytes();run(['pdf',doc,pdf],False);assert pdf.read_bytes()==before;report['refusals']+=1
 doc=d/'doc1.json';original=doc.read_bytes();new=d/'edited.json';v=json.loads(run(['set',doc,0,2,250,new]).stdout);assert v['subtotalCents']==500 and doc.read_bytes()==original;report['editCases']+=1
 add=d/'added.json';v=json.loads(run(['set',new,1,1,99,add]).stdout);assert v['subtotalCents']==599 and v['lineCount']==2;report['editCases']+=1
 removed=d/'removed.json';v=json.loads(run(['remove',add,0,removed]).stdout);assert v['subtotalCents']==99 and v['lineCount']==1;report['editCases']+=1
 for args in [['set',doc,2,1,2,d/'bad1'],['set',doc,0,0,2,d/'bad2'],['set',doc,0,4294967295,2,d/'bad3'],['set',doc,'bad',1,2,d/'bad4'],['remove',doc,1,d/'bad5'],['save',plan,d/'missing',d/'bad6']]:run(args,False);assert not Path(args[-1]).exists();report['refusals']+=1
 link=d/'linked';link.symlink_to(doc);run(['save',plan,d/'lines1.json',link],False);assert doc.read_bytes()==original;report['refusals']+=1
 for payload in [{'format':'wrong','plan':plan.read_text(),'lines':[]},{'format':'rf2.invoice.document.v1','plan':plan.read_text(),'lines':[],'totalCents':1}]:
  src=d/'invalid.json';src.write_text(json.dumps(payload));run(['inspect',src],False);report['refusals']+=1
 # Deliver one actual native-generated, visually reviewable programming example.
 out=d/'example.pdf';run(['pdf',new,out]);(R/'output/Invoice-Worksheet-Example.pdf').write_bytes(out.read_bytes());report['examplePDFSHA256']=hashlib.sha256(out.read_bytes()).hexdigest()
report.update(passed=True,runtimeSHA256=hashlib.sha256(B.read_bytes()).hexdigest());(R/'docs/WORKSPACE-0.8-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
