"""Independent Unicode scalar-view probes; Python strict UTF-8 is the oracle.

Use RF2_TEST_COMPILER=/absolute/candidate. No network or device access.
Valid cases compare a wrapping scalar fingerprint plus both count units;
this is finite differential evidence, not a proof or a timing benchmark.
"""
from pathlib import Path
import hashlib,json,os,random,struct,subprocess,tempfile,time
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
D=R/'artifacts/unicode-view-adversarial'/str(time.time_ns());D.mkdir(parents=True)
HEADER='profile RF2_SYSTEM_A64_V1\narray Bytes(u8,255)\ntextview Text(Bytes)\n'
SOURCE=HEADER+'''fn inspect(data:Bytes,start,count)
 let text=Text(data,start,count)
 let hash=1469598103934665603
 let i=0
 while i<text.length
  set hash=(hash^text[i])*1099511628211
  set i=i+1
 end
 return hash^(text.length<<32)^text.byte_length
end
fn main(argc,argv)
 let data=Bytes()
 let count=read_bytes(0,data,255)
 if count<2
  return 1
 end
 let answer=inspect(data,data[0]+2,data[1])
 let out=buffer("unicode_probe_answer",8)
 do store64(out,answer)
 do write(1,out,8)
 return 0
end
'''
CASES=[]
def add(name,body,start=0,count=None):
 if count is None:count=len(body)-start
 assert 0<=start<=253 and 0<=count<=255 and len(body)<=253
 raw=body[start:start+count]
 try:
  value=raw.decode('utf-8','strict');valid=True
 except UnicodeDecodeError:value=None;valid=False
 # Range is against declared capacity, not received byte count. Test cases never
 # accidentally ask for unreceived bytes, except named explicit bounds cases.
 assert start+count<=len(body)
 CASES.append({'name':name,'input':bytes([start,count])+body,'valid':valid,'raw':raw,'text':value})
for name,text in [
 ('empty',''),('ascii','abc\r\n\t'),('nul','\0'),('bom','\ufeff'),('noncharacters','\ufdd0\ufffe\uffff\U0001fffe\U0010ffff'),
 ('tamil','தமிழ்'),('combining','e\u0301'),('emoji-zwj','👩\u200d🔬'),('flag','🇲🇾'),('mixed','Aதமிழ்\0é🌍')]:add(name,text.encode())
for point in [0,1,0x7f,0x80,0x7ff,0x800,0xd7ff,0xe000,0xffff,0x10000,0x10ffff]:add(f'boundary-{point:x}',chr(point).encode())
for byte in range(128,256):add(f'single-byte-{byte:02x}',bytes([byte]))
for name,body in [
 ('overlong-two',b'\xc0\x80'),('overlong-two-max',b'\xc1\xbf'),('overlong-three',b'\xe0\x80\x80'),('overlong-three-max',b'\xe0\x9f\xbf'),
 ('overlong-four',b'\xf0\x80\x80\x80'),('overlong-four-max',b'\xf0\x8f\xbf\xbf'),('surrogate-start',b'\xed\xa0\x80'),('surrogate-end',b'\xed\xbf\xbf'),
 ('above-max',b'\xf4\x90\x80\x80'),('above-max-end',b'\xf4\xbf\xbf\xbf'),('five-byte',b'\xf8\x88\x80\x80\x80'),
 ('bad-two-middle',b'\xc2A'),('bad-three-middle',b'\xe2A\xac'),('bad-four-last',b'\xf0\x90\x80A'),('invalid-after-valid',b'A\xff'),
 ('stray-after-valid',b'\xc2\x80\x80'),('continuation-after-nul',b'\0\x80')]:add(name,body)
for body in [b'\xc2\x80',b'\xe0\xa0\x80',b'\xef\xbf\xbf',b'\xf0\x90\x80\x80',b'\xf4\x8f\xbf\xbf']:
 for n in range(1,len(body)):add('truncated-'+body.hex()+'-'+str(n),body[:n])
# Valid selected windows must not inspect malformed bytes outside the selected span.
add('invalid-owner-outside-window',b'\xffA\xc2\x80\xff',1,3)
add('empty-after-invalid',b'\xff',1,0)
add('selected-continuation',b'\xc2\x80',1,1)
add('selected-truncated',b'\xc2\x80',0,1)
add('selected-full-emoji',b'\xff\xf0\x9f\x8c\x8d\xff',1,4)
# The owner has255 bytes, two prefix bytes are fixture metadata. Empty at capacity.
CASES.append({'name':'empty-at-capacity','input':bytes([253,0])+b'x'*253,'valid':True,'raw':b'','text':''})
# Generated corpus is fixed and independent of RF2's implementation.
rng=random.Random(140013)
for i in range(70):
 points=[]
 for j in range(rng.randrange(1,22)):
  point=rng.randrange(0x110000)
  while 0xd800<=point<=0xdfff:point=rng.randrange(0x110000)
  points.append(point)
 add('generated-valid-'+str(i),''.join(map(chr,points)).encode())
for i in range(70):
 body=bytes(rng.randrange(256) for j in range(rng.randrange(1,36)))
 add('generated-bytes-'+str(i),body)
NEG=[]
def reject(name,body):NEG.append((name,HEADER+body))
reject('write-text','fn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,0,1)\nset t[0]=65\nreturn 0\nend\n')
reject('write-owner','fn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,0,1)\nset b[0]=65\nreturn 0\nend\n')
reject('call-while-live','fn f()\nreturn 0\nend\nfn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,0,1)\nreturn f()\nend\n')
reject('copy-text','fn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,0,1)\nlet u=t\nreturn 0\nend\n')
reject('return-text','fn f(b:Bytes)\nlet t=Text(b,0,1)\nreturn t\nend\nfn main(argc,argv)\nreturn 0\nend\n')
reject('text-parameter','fn f(t:Text)\nreturn t.length\nend\nfn main(argc,argv)\nreturn 0\nend\n')
reject('raw-text','fn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,0,1)\nreturn load64(t)\nend\n')
reject('wrong-owner','array Other(u8,255)\nfn main(argc,argv)\nlet b=Other()\nlet t=Text(b,0,1)\nreturn 0\nend\n')
reject('view-of-words','array Words(u64,2)\ntextview Bad(Words)\nfn main(argc,argv)\nreturn 0\nend\n')
reject('block-declaration','fn main(argc,argv)\nlet b=Bytes()\nif 1\nlet t=Text(b,0,1)\nend\nreturn 0\nend\n')
reject('rebind','fn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,0,1)\nset t=Text(b,0,1)\nreturn 0\nend\n')
reject('escape-through-record','record Box(x:u64)\nfn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,0,1)\nlet box=Box(t)\nreturn 0\nend\n')

reject('alias-owner-write','fn f(a:Bytes,b:Bytes)\nlet t=Text(a,0,1)\nset b[0]=65\nreturn 0\nend\nfn main(argc,argv)\nlet b=Bytes()\nreturn f(b,b)\nend\n')
reject('hidden-call-second-view','fn zero()\nreturn 0\nend\nfn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,0,1)\nlet u=Text(b,zero(),0)\nreturn 0\nend\n')
reject('copy-through-ordinary-call','fn f(n)\nreturn n\nend\nfn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,0,1)\nreturn f(t)\nend\n')

def expected(text,raw):
 h=1469598103934665603
 for ch in text:h=((h^ord(ch))*1099511628211)&((1<<64)-1)
 return h^(len(text)<<32)^len(raw)
rows=[]
source=D/'probe.rf2';source.write_text(SOURCE)
for opt in [False,True]:
 exe=D/('probe-opt'if opt else'probe');p=subprocess.run([C,source,exe]+(['--opt']if opt else[]),capture_output=True,timeout=30)
 assert p.returncode==0,p.stderr
 subprocess.run(['/usr/bin/codesign','-s','-',exe],capture_output=True,check=True)
 for case in CASES:
  q=subprocess.run([exe],input=case['input'],capture_output=True,timeout=5)
  if case['valid']:
   assert q.returncode==0 and q.stdout==struct.pack('<Q',expected(case['text'],case['raw'])) and not q.stderr,(case['name'],opt,q.returncode,q.stdout,q.stderr)
  else:assert q.returncode==2 and b'RF2 UTF8'in q.stderr and not q.stdout,(case['name'],opt,q.returncode,q.stderr)
  rows.append({'name':case['name'],'optimized':opt,'expected':'valid'if case['valid']else'invalid-utf8','inputSHA256':hashlib.sha256(case['input']).hexdigest(),'passed':True})
 # Boundary and alias syntax probes separate from Unicode validity.
 for name,body in NEG:
  src=D/(name+str(opt)+'.rf2');src.write_text(body);out=src.with_suffix('.bin');q=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True,timeout=30)
  assert q.returncode==1 and not out.exists(),(name,opt,q.returncode,q.stderr)
  rows.append({'name':name,'optimized':opt,'expected':'compile-refusal','passed':True})
 # Scalar index count differs from byte count for U+0080.
 for name,body in [
 ('index-scalars','fn main(argc,argv)\nlet b=Bytes()\nset b[0]=194\nset b[1]=128\nlet t=Text(b,0,2)\nreturn t[1]\nend\n'),
 ('index-minus-one','fn main(argc,argv)\nlet b=Bytes()\nset b[0]=65\nlet t=Text(b,0,1)\nreturn t[-1]\nend\n'),
 ('index-max','fn main(argc,argv)\nlet b=Bytes()\nset b[0]=65\nlet t=Text(b,0,1)\nreturn t[18446744073709551615]\nend\n'),
 ('index-max-minus-one','fn main(argc,argv)\nlet b=Bytes()\nset b[0]=65\nlet t=Text(b,0,1)\nreturn t[18446744073709551614]\nend\n'),
 ('range-overflow','fn main(argc,argv)\nlet b=Bytes()\nlet t=Text(b,254,18446744073709551615)\nreturn 0\nend\n')]:
  src=D/(name+str(opt)+'.rf2');src.write_text(HEADER+body);out=src.with_suffix('.bin');q=subprocess.run([C,src,out]+(['--opt']if opt else[]),capture_output=True,timeout=30);assert q.returncode==0,q.stderr;subprocess.run(['/usr/bin/codesign','-s','-',out],check=True,capture_output=True);q=subprocess.run([out],capture_output=True,timeout=5);assert q.returncode==2 and b'RF2 bounds'in q.stderr,(name,opt,q.returncode,q.stderr);rows.append({'name':name,'optimized':opt,'expected':'bounds-trap','passed':True})
report={'passed':True,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'compilerSourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'checks':rows,'caseCount':len(rows),'inputCasesPerMode':len(CASES),'compileRefusalsPerMode':len(NEG),'scope':'Independent strict-codec oracle plus source refusal/range cases. Unicode scalar values, not grapheme clusters, normalization, locale segmentation or security certification. No speed or token claim.'}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'checks':len(rows),'report':str(D/'report.json')}))
