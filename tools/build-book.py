"""Document production only. RF² itself has no Python dependency."""
from pathlib import Path
import re,json,html,zipfile,uuid,hashlib,datetime,shutil
from xml.etree import ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,Table,TableStyle,Preformatted,Flowable,Image,KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output';(OUT/'pdf').mkdir(parents=True,exist_ok=True);(OUT/'epub').mkdir(exist_ok=True)
source=(ROOT/'book/RiverFlow-First-Edition.md').read_text()
bench=json.loads((ROOT/'docs/NATIVE-BENCHMARK-RUNS.json').read_text())
rows=['| Words | Native median range, µs | Manual median range, µs | Ratio range |','| --- | --- | --- | --- |']
for i,size in enumerate([8,256,4096]):
 rs=[r['rows'][i] for r in bench['runs']]
 rng=lambda key:f"{min(x[key] for x in rs):.4f} to {max(x[key] for x in rs):.4f}"
 rows.append(f"| {size} | {rng('generatedMedianUs')} | {rng('baselineMedianUs')} | {rng('speedupVsManual')} |")
snapshot='\n'.join(rows)+'\n\nRatio is manual time divided by generated time. Three fresh processes ran on one host, with eleven rotated trials per size and variant in each process. Small differences do not establish broad superiority. The optimization brings the exact sum close to the selected manual implementation; it is not a result for arbitrary programmes or devices.\n\nThe native differential suite compiles and executes seventeen program families, including all five complete book examples, with host address and undefined-behavior sanitizers. It compares successful values and work counts and checks retained error categories. Native tests require Clang and supported sanitizer runtimes. Other hosts need their own qualification.\n\nSource and raw evidence: docs/NATIVE-BENCHMARK-RUNS.json, docs/NATIVE-BENCHMARK-CONSERVATIVE.json, tests/native.test.mjs and tools/check-book-examples.mjs.\n'
source=source.replace('{{EVIDENCE_TABLES}}',snapshot)
(ROOT/'book/RiverFlow-First-Edition-expanded.md').write_text(source)
fonts=Path('/System/Library/Fonts/Supplemental')
if (fonts/'Georgia.ttf').exists():
 for n,f in [('Book','Georgia.ttf'),('BookBold','Georgia Bold.ttf'),('BookItalic','Georgia Italic.ttf'),('Sans','Arial.ttf'),('SansBold','Arial Bold.ttf'),('Code','Andale Mono.ttf')]:pdfmetrics.registerFont(TTFont(n,str(fonts/f)))
 pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='BookItalic',boldItalic='BookBold')
else:
 for n,b in [('Book','Times-Roman'),('BookBold','Times-Bold'),('BookItalic','Times-Italic'),('Sans','Helvetica'),('SansBold','Helvetica-Bold'),('Code','Courier')]:pdfmetrics.registerFont(pdfmetrics.Font(n,b,'WinAnsiEncoding'))
 pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='BookItalic',boldItalic='BookBold')
NAVY=colors.HexColor('#092033');CYAN=colors.HexColor('#82e6ef');INK=colors.HexColor('#182b3a');MUTED=colors.HexColor('#506273');PAPER=colors.HexColor('#fbfaf6')
W,H=148*mm,210*mm;M=16*mm;TW=W-2*M
styles={
 'body':ParagraphStyle('Body',fontName='Book',fontSize=10,leading=14.6,textColor=INK,spaceAfter=8,splitLongWords=True,allowWidows=0,allowOrphans=0),
 'h1':ParagraphStyle('H1',fontName='SansBold',fontSize=23,leading=27,textColor=NAVY,spaceAfter=18,keepWithNext=True),
 'h2':ParagraphStyle('H2',fontName='SansBold',fontSize=14,leading=18,textColor=NAVY,spaceBefore=12,spaceAfter=9,keepWithNext=True),
 'small':ParagraphStyle('Small',fontName='Sans',fontSize=8,leading=11,textColor=MUTED,spaceAfter=7),
 'code':ParagraphStyle('Code',fontName='Code',fontSize=7.7,leading=10.8,backColor=colors.HexColor('#edf3f5'),borderPadding=9,spaceBefore=5,spaceAfter=12),
 'front':ParagraphStyle('Front',fontName='Book',fontSize=9.5,leading=13.3,textColor=INK,spaceAfter=6,splitLongWords=True),
 'refs':ParagraphStyle('Refs',fontName='Book',fontSize=9,leading=12.6,textColor=INK,spaceAfter=6,splitLongWords=True),
 'cell':ParagraphStyle('Cell',fontName='Sans',fontSize=7.3,leading=10,textColor=INK),
}
def inline(s):
 s=html.escape(s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
 s=re.sub(r'`([^`]+)`',r'<font name="Code">\1</font>',s)
 s=re.sub(r'(https?://[^\s<>]+)',r'<link href="\1" color="#15506b">\1</link>',s)
 return s
class Pipeline(Flowable):
 def __init__(self):Flowable.__init__(self);self.width=TW;self.height=112
 def draw(self):
  c=self.canv;c.setFont('Sans',8)
  boxes=[(0,77,82,'RF² source'),(112,77,94,'Check + IR'),(237,77,89,'Interpreter'),(112,27,94,'C11 emitter'),(237,27,89,'Host compiler')]
  for x,y,w,t in boxes:c.setFillColor(colors.HexColor('#edf3f5'));c.setStrokeColor(colors.HexColor('#8aa9b7'));c.roundRect(x,y,w,23,5,stroke=1,fill=1);c.setFillColor(NAVY);c.drawCentredString(x+w/2,y+8,t)
  c.setStrokeColor(NAVY)
  for x1,y1,x2,y2 in [(82,88,110,88),(206,88,235,88),(159,77,159,52),(206,38,235,38)]:
   c.line(x1,y1,x2,y2);p=c.beginPath();p.moveTo(x2,y2);p.lineTo(x2-4 if x1!=x2 else x2-3,y2-3 if x1!=x2 else y2+5);p.lineTo(x2-4 if x1!=x2 else x2+3,y2+3 if x1!=x2 else y2+5);p.close();c.setFillColor(NAVY);c.drawPath(p,fill=1,stroke=0)
  c.setFont('Sans',7);c.setFillColor(MUTED);c.drawString(0,7,'Figure 1. Source paths. Native compilation does not qualify a device.')
class NativePipeline(Flowable):
 def __init__(self):Flowable.__init__(self);self.width=TW;self.height=112
 def draw(self):
  c=self.canv;c.setFont('Sans',8)
  for x,y,t in [(0,77,'Core source'),(113,77,'Check + IR'),(232,77,'Native runtime'),(0,27,'Systems kernel'),(113,27,'rf2c'),(232,27,'ARM64 program')]:
   c.setFillColor(colors.HexColor('#edf3f5'));c.setStrokeColor(colors.HexColor('#8aa9b7'));c.roundRect(x,y,94,23,5,stroke=1,fill=1);c.setFillColor(NAVY);c.drawCentredString(x+47,y+8,t)
  c.setStrokeColor(NAVY)
  for x1,y1,x2,y2 in [(94,88,111,88),(207,88,230,88),(160,77,47,52),(94,38,111,38),(207,38,230,38)]:
   c.line(x1,y1,x2,y2)
   dx=x2-x1;dy=y2-y1;length=(dx*dx+dy*dy)**.5;ux=dx/length;uy=dy/length
   c.line(x2,y2,x2-5*ux+2.5*uy,y2-5*uy-2.5*ux);c.line(x2,y2,x2-5*ux-2.5*uy,y2-5*uy+2.5*ux)
  c.setFont('Sans',7);c.setFillColor(MUTED);c.drawString(0,7,'Figure 2. Runtime execution and per-program compilation are distinct routes.')
class BookDoc(BaseDocTemplate):
 def __init__(self,path):
  super().__init__(str(path),pagesize=(W,H),leftMargin=M,rightMargin=M,topMargin=18*mm,bottomMargin=18*mm,title='RiverFlow RF²: Ideas into checked computation',author='Ilangkhumanan Thirunavokkarasu',subject='Revised first edition, native package 0.8 and reference Core')
  self.addPageTemplates(PageTemplate('book',[Frame(M,18*mm,TW,H-36*mm,id='normal',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=self.decorate))
 def decorate(self,c,doc):
  if doc.page==1:
   c.setFillColor(NAVY);c.rect(0,0,W,H,fill=1,stroke=0);c.setFillColor(CYAN);c.setFont('SansBold',9);c.drawString(M,H-23*mm,'STARK FIBER ENTERPRISE')
   c.setFillColor(colors.white);c.setFont('SansBold',67);c.drawString(M,H-52*mm,'RF²');c.setFont('SansBold',39);c.drawString(M,H-70*mm,'RiverFlow');c.setFont('Book',14);c.drawString(M,H-83*mm,'Ideas into checked computation')
   art=ROOT/'site/assets/riverflow-hero.png';c.drawImage(str(art),0,43*mm,width=W,height=76*mm,preserveAspectRatio=True,anchor='c')
   c.setFillColor(colors.white);c.setFont('Sans',10);c.drawString(M,29*mm,'Ilangkhumanan Thirunavokkarasu');c.setFillColor(CYAN);c.setFont('Sans',8);c.drawString(M,20*mm,'FIRST EDITION  /  NOVEMBER 2026');return
  c.setStrokeColor(colors.HexColor('#cad4d8'));c.setLineWidth(.4);c.line(M,H-13*mm,W-M,H-13*mm)
  c.setFont('Sans',7);c.setFillColor(MUTED);c.drawString(M,H-10*mm,'RIVERFLOW RF²');c.drawRightString(W-M,H-10*mm,'REVISED EDITION · 0.8')
  c.drawString(M,10*mm,'Stark Fiber Enterprise');c.drawRightString(W-M,10*mm,str(doc.page))
 def afterFlowable(self,f):
  if isinstance(f,Paragraph) and f.style.name=='H1':
   text=f.getPlainText()
   if text in ['Contents','Publication note']:return
   key='section-'+hashlib.sha256(text.encode()).hexdigest()[:12];self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,0,False);self.notify('TOCEntry',(0,text,self.page,key))
def blocks(s):
 lines=s.splitlines();i=0
 while i<len(lines):
  line=lines[i]
  if not line.strip():i+=1;continue
  if line.startswith('```'):
   lang=line[3:];i+=1;code=[]
   while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
   i+=1;yield('code','\n'.join(code));continue
  if line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].startswith('|'):
    row=[x.strip() for x in lines[i].strip('|').split('|')]
    if not all(re.fullmatch(r'[:\- ]+',x) for x in row):rows.append(row)
    i+=1
   yield('table',rows);continue
  if line.startswith('# '):yield('h1',line[2:]);i+=1;continue
  if line.startswith('## '):yield('h2',line[3:]);i+=1;continue
  if line=='{{PIPELINE_FIGURE}}':yield('figure','');i+=1;continue
  if line=='{{NATIVE_PIPELINE}}':yield('nativefigure','');i+=1;continue
  text=[line];i+=1
  while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','```','|','{{')):text.append(lines[i]);i+=1
  yield('p',' '.join(text))
body=source[source.index('# About this edition'):]
story=[Spacer(1,H-40*mm),PageBreak(),Paragraph('Publication note',styles['h1']),Paragraph('RiverFlow RF²<br/>Ideas into checked computation',styles['h2']),Paragraph('Ilangkhumanan Thirunavokkarasu<br/>Stark Fiber Enterprise<br/>First edition, revised November 2026<br/>Language package 0.8',styles['body']),Spacer(1,12),Image(str(ROOT/'site/assets/riverflow-mark.png'),35*mm,35*mm),Spacer(1,12),Paragraph('Independently published technical edition. Original text and code are available under the MIT licence. AI assisted development and concept artwork. No ISBN or external academic approval is asserted.',styles['small']),Paragraph('Source, corrections and release files:<br/>https://github.com/starkfiber/RiverFlow',styles['small']),PageBreak(),Paragraph('Contents',styles['h1'])]
toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOC0',fontName='Sans',fontSize=8.7,leading=12,spaceBefore=0,textColor=NAVY)];story+=[toc,PageBreak()]
first=True
references=False
frontmatter=False
for kind,value in blocks(body):
 if kind=='h1':
  if not first:story.append(PageBreak())
  first=False;references=value.startswith('Appendix D.');frontmatter=value=='About this edition';story.append(Paragraph(inline(value),styles['h1']))
  art=None
  for prefix,file in [('1. ','riverflow-language.png'),('12. ','riverflow-research.png'),('14. ','riverflow-future.png')]:
   if value.startswith(prefix):art=file
  if art:
   from reportlab.lib.utils import ImageReader
   aw,ah=ImageReader(str(ROOT/'site/assets'/art)).getSize()
   story+=[Image(str(ROOT/'site/assets'/art),TW,TW*ah/aw),Spacer(1,12)]
 elif kind=='h2':story.append(Paragraph(inline(value),styles['h2']))
 elif kind=='p':story.append(Paragraph(inline(value),styles['refs' if references else 'front' if frontmatter else 'body']))
 elif kind=='code':
  block=Preformatted(value,styles['code'],dedent=0);story.append(KeepTogether([block]) if len(value.splitlines())<=12 else block)
 elif kind=='figure':story+=[Pipeline(),Spacer(1,8)]
 elif kind=='nativefigure':story+=[NativePipeline(),Spacer(1,8)]
 elif kind=='table':
  cells=[[Paragraph(inline(c),styles['cell']) for c in row]for row in value];n=len(cells[0]);widths=[TW/n]*n
  if n==3:widths=[TW*.16,TW*.44,TW*.40]
  t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebef')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f6')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#8aa9b7'))]));story+=[KeepTogether([t]) if len(cells)<=5 else t,Spacer(1,12)]
pdf=OUT/'pdf/RiverFlow-First-Edition.pdf';BookDoc(pdf).multiBuild(story)
# Accessible reflowable HTML and EPUB, using the same expanded source.
css='body{max-width:42em;margin:3em auto;padding:0 1.2em;font:1.05em/1.7 Georgia,serif;color:#182b3a;background:#fbfaf6}h1,h2{font-family:Arial,sans-serif;color:#092033;line-height:1.2}h1{margin-top:2em}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf3f5;padding:1em;font-size:.8em}img{max-width:100%}table{border-collapse:collapse;width:100%;font-size:.85em}td,th{border:1px solid #8aa9b7;padding:.6em;text-align:left}a{color:#15506b}.cover{text-align:center;padding-top:1em}.cover img{width:65%;max-width:24em}nav li{margin:.4em 0}'
sections=[];current=[];title=''
for kind,value in blocks(body):
 if kind=='h1':
  if current:sections.append((title,'\n'.join(current)))
  title=value;current=['<h1>'+html.escape(value)+'</h1>'];continue
 if kind=='p':current.append('<p>'+html.escape(value)+'</p>')
 elif kind=='h2':current.append('<h2>'+html.escape(value)+'</h2>')
 elif kind=='code':current.append('<pre><code>'+html.escape(value)+'</code></pre>')
 elif kind=='table':current.append('<table>'+''.join('<tr>'+''.join(f'<{"th" if i==0 else "td"}>'+html.escape(c)+f'</{"th" if i==0 else "td"}>' for c in row)+'</tr>'for i,row in enumerate(value))+'</table>')
 elif kind=='nativefigure':current.append('<p><strong>Figure 2.</strong> Core source → check and IR → native runtime. Checked lowering → systems kernel → rf2c → per-program ARM64 executable.</p>')
 elif kind=='figure':current.append('<p><strong>Figure 1.</strong> RF² source → checker and IR → interpreter. The checked IR can also feed the C11 emitter → host compiler → native code. Device qualification is a separate experiment.</p>')
if current:sections.append((title,'\n'.join(current)))
nav='<nav><h1>Contents</h1><ol>'+''.join(f'<li><a href="#chapter-{i}">{html.escape(t)}</a></li>'for i,(t,_)in enumerate(sections))+'</ol></nav>'
cover='<section class="cover"><img src="assets/riverflow-mark.png" alt="RiverFlow glass river mark"/><h1>RiverFlow RF²</h1><p>Ideas into checked computation</p><p>Ilangkhumanan Thirunavokkarasu<br/>Stark Fiber Enterprise<br/>First edition · November 2026</p></section>'
htm='<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>RiverFlow RF² · The book</title><style>'+css+'</style></head><body>'+cover+nav+''.join(f'<section id="chapter-{i}">{s}</section>'for i,(_,s)in enumerate(sections))+'</body></html>'
sitebook=ROOT/'site/book';sitebook.mkdir(exist_ok=True);(sitebook/'index.html').write_text(htm);(sitebook/'assets').mkdir(exist_ok=True);shutil.copy(ROOT/'site/assets/riverflow-mark.png',sitebook/'assets/riverflow-mark.png')
xhtml=lambda title,content:'<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en"><head><title>'+html.escape(title)+'</title><link rel="stylesheet" href="style.css"/></head><body>'+content+'</body></html>'
epub=OUT/'epub/RiverFlow-First-Edition.epub';identifier='urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,hashlib.sha256(source.encode()).hexdigest()));modified=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
manifest=['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>','<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>','<item id="style" href="style.css" media-type="text/css"/>','<item id="art" href="assets/riverflow-mark.png" media-type="image/png" properties="cover-image"/>']+[f'<item id="c{i}" href="c{i}.xhtml" media-type="application/xhtml+xml"/>'for i in range(len(sections))]
opf=f'<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">{identifier}</dc:identifier><dc:title>RiverFlow RF²: Ideas into checked computation</dc:title><dc:creator>Ilangkhumanan Thirunavokkarasu</dc:creator><dc:language>en</dc:language><dc:publisher>Stark Fiber Enterprise</dc:publisher><dc:rights>Original text and code: MIT. Concept artwork: AI generated.</dc:rights><meta property="dcterms:modified">{modified}</meta></metadata><manifest>{"".join(manifest)}</manifest><spine><itemref idref="cover"/><itemref idref="nav"/>'+''.join(f'<itemref idref="c{i}"/>'for i in range(len(sections)))+'</spine></package>'
with zipfile.ZipFile(epub,'w')as z:
 z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED);z.writestr('META-INF/container.xml','<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>');z.writestr('OEBPS/content.opf',opf);z.writestr('OEBPS/style.css',css);z.writestr('OEBPS/cover.xhtml',xhtml('RiverFlow RF²',cover));z.writestr('OEBPS/nav.xhtml',xhtml('Contents','<nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc"><h1>Contents</h1><ol>'+''.join(f'<li><a href="c{i}.xhtml">{html.escape(t)}</a></li>'for i,(t,_)in enumerate(sections))+'</ol></nav>'));z.write(ROOT/'site/assets/riverflow-mark.png','OEBPS/assets/riverflow-mark.png')
 for i,(t,s)in enumerate(sections):z.writestr(f'OEBPS/c{i}.xhtml',xhtml(t,s))
with zipfile.ZipFile(epub)as z:
 assert z.testzip()is None
 for n in z.namelist():
  if n.endswith(('.xhtml','.xml','.opf')):ET.fromstring(z.read(n))
shutil.copytree(sitebook,ROOT/'docs/book',dirs_exist_ok=True)
report={'book':'RiverFlow RF²: Ideas into checked computation','edition':'First edition, revised package 0.8','sourceWords':len(re.findall(r'\S+',source)),'sections':len(sections),'pdf':str(pdf.relative_to(ROOT)),'pdfSHA256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'epub':str(epub.relative_to(ROOT)),'epubSHA256':hashlib.sha256(epub.read_bytes()).hexdigest(),'epubXmlWellFormed':True,'limits':'XML/ZIP integrity checks are not a full EPUBCheck certification. PDF requires separate visual inspection.'}
(ROOT/'book/BUILD.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
