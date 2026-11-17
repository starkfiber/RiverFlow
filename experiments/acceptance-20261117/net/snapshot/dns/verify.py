"""Independent DNS wire expectations for the declared local-zone subset."""
from pathlib import Path
import subprocess,struct,json,hashlib,random,sys
V=Path('experiments/rf2net/dns');D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('artifacts/rf2net-dns-final');D.mkdir(exist_ok=False);C=Path('artifacts/rf2decision-sustained/compiler-opt').resolve()
def name(s):return b''.join(bytes([len(x)])+x.encode() for x in s.split('.') if x)+b'\0'
def query(s='gateway.rf2.test',typ=1,cls=1,flags=256,edns=None,opt=b'',version=0):
 b=struct.pack('!6H',0x2468,flags,1,0,0,int(edns is not None))+name(s)+struct.pack('!HH',typ,cls)
 if edns is not None:b+=b'\0'+struct.pack('!HHIH',41,edns,version<<16,len(opt))+opt
 return b
def soa():
 data=name('gateway.rf2.test')+name('hostmaster.rf2.test')+struct.pack('!5I',1,60,30,300,30)
 return name('rf2.test')+struct.pack('!HHIH',6,1,30,len(data))+data

def oracle(b):
 if not 12<=len(b)<=512:return b''
 ident,flags,qd,an,ns,ar=struct.unpack('!6H',b[:12]);qend=0;edns=0;rcode=0;qname='';typ=cls=0
 if flags&0x8000:return b''
 if flags&0x7800:rcode=4
 elif flags&0x06cf or qd!=1 or an or ns or ar>1:rcode=1
 else:
  try:
   pos=12;labels=[];used=0
   while True:
    n=b[pos];pos+=1
    if n==0:break
    if n>63 or pos+n>len(b) or pos+n-12>=255:raise ValueError()
    label=b[pos:pos+n].lower();used+=n+int(bool(labels))
    if used>253 or any(c not in b'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in label):raise ValueError()
    labels.append(label);pos+=n
   if pos+4>len(b):raise ValueError()
   typ,cls=struct.unpack('!HH',b[pos:pos+4]);qend=pos+4;qname=b'.'.join(labels).decode();pos=qend
   if ar==0:
    if pos!=len(b):raise ValueError()
   else:
    if pos+11>len(b) or b[pos]!=0 or int.from_bytes(b[pos+1:pos+3],'big')!=41:raise ValueError()
    ext,version=b[pos+5:pos+7];edns=2 if version else 1
    if ext:raise ValueError()
    size=int.from_bytes(b[pos+9:pos+11],'big');pos+=11
    if pos+size!=len(b):raise ValueError()
    while pos<len(b):
     if pos+4>len(b):raise ValueError()
     n=int.from_bytes(b[pos+2:pos+4],'big');pos+=4+n
     if pos>len(b):raise ValueError()
  except (IndexError,ValueError):rcode=1
 answer=b'';auth=b'';aa=0
 if rcode==0 and edns!=2:
  zone=qname=='rf2.test' or qname.endswith('.rf2.test')
  if not zone or cls!=1 or qname=='blocked.rf2.test':rcode=5
  else:
   aa=0x400;known=qname in ['rf2.test','gateway.rf2.test','health.rf2.test']
   if not known:rcode=3;auth=soa()
   elif typ==1 and qname!='rf2.test':answer=b'\xc0\x0c'+struct.pack('!HHIH',1,1,30,4)+bytes([10,77,0,2])
   elif typ==6 and qname=='rf2.test':answer=soa()
   elif typ==2 and qname=='rf2.test':answer=b'\xc0\x0c'+struct.pack('!HHIH',2,1,30,18)+name('gateway.rf2.test')
   elif typ in [1,2,6,28]:auth=soa()
   else:rcode=4;aa=0
 extra=b''
 if edns:extra=b'\0'+struct.pack('!HHIH',41,512,(1<<24) if rcode==0 and edns==2 else 0,0)
 f=0x8000|aa|(flags&0x7910)|rcode
 return struct.pack('!6H',ident,f,int(qend>0),int(bool(answer)),int(bool(auth)),int(bool(extra)))+b[12:qend]+answer+auth+extra
cases=[]
def add(label,b):cases.append((label,b))
for s in ['gateway.rf2.test','health.rf2.test','rf2.test','GATEWAY.RF2.TEST','notfound.rf2.test','blocked.rf2.test','evilrf2.test','rf2.test.example','example.test','']:
 for typ in [1,2,6,16,28,255]:
  for edns in [None,512]:add(s+'-'+str(typ)+'-'+str(edns),query(s,typ,edns=edns))
for flags in [0,256,16,48,0x8000,0x1000,0x400,0x200,0x80,0x40,1]:add('flags-'+str(flags),query(flags=flags))
for version in [0,1,255]:add('EDNSversion-'+str(version),query(edns=4096,version=version))
for opt in [b'',b'\0\x0a\0\x08abcdefgh',b'\0\x0a\0\0',b'\0',b'\0\x0a\0\x08abc']:
 add('EDNSopt-'+opt.hex(),query(edns=1232,opt=opt))
for at,value in [(4,0),(5,2),(7,1),(9,1),(11,2)]:
 b=bytearray(query());b[at]=value;add('counts-'+str(at),bytes(b))
b=bytearray(query());b[12]=192;b[13]=12;add('compression-loop-refused',bytes(b))
for n in range(len(query())):add('truncated-query-'+str(n),query()[:n])
for label in ['a'*63,'a'*64,'a.b','a_b','a--b']:
 add('label-'+label,query(label+'.rf2.test'))
add('max-name',query('.'.join(['a'*63]*3+['b'*61])));add('too-long-name',query('.'.join(['a'*63]*4)))
rng=random.Random(171127)
for i in range(1500):
 if i%2:
  s=rng.choice(['gateway','health','unknown'+str(i)])+'.rf2.test';b=query(s,rng.choice([1,2,6,16,28,255]),flags=rng.choice([0,256,272]),edns=rng.choice([None,512,4096]))
 else:
  b=bytearray(query(edns=512));at=rng.randrange(len(b));b[at]^=rng.randrange(1,256);b=bytes(b)
 add('seeded-'+str(i),b)
blob=b''.join(struct.pack('<H',len(b))+b for _,b in cases);expected=b''.join(struct.pack('<H',len(oracle(b)))+oracle(b) for _,b in cases)
(D/'INPUT.bin').write_bytes(blob);(D/'EXPECTED.bin').write_bytes(expected);results=[]
for mode in ['plain','opt']:
 exe=D/('dns-'+mode);x=subprocess.run([str(C),str(V/'main.flow'),str(exe),'--compact']+(['--opt'] if mode=='opt' else []),capture_output=True,text=True,timeout=40);assert x.returncode==0,x.stdout+x.stderr;subprocess.run(['codesign','-s','-',str(exe)],check=True,capture_output=True)
 x=subprocess.run([str(exe.resolve())],input=blob,capture_output=True,timeout=15);(D/('ACTUAL-'+mode+'.bin')).write_bytes(x.stdout)
 if x.returncode!=0 or x.stdout!=expected:
  off=0
  for label,b in cases:
   want=oracle(b);size=2+len(want)
   if x.stdout[off:off+size]!=struct.pack('<H',len(want))+want:print('FIRST MISMATCH',label,'query',b.hex(),'expected',want.hex(),'actual',x.stdout[off:off+size].hex());break
   off+=size
  raise AssertionError((mode,x.returncode,len(x.stdout),len(expected)))
 stream=0;raw=struct.pack('<H',len(query()))+query()
 for n in range(1,len(raw)):
  x=subprocess.run([str(exe.resolve())],input=raw[:n],capture_output=True,timeout=5);assert x.returncode==2 and not x.stdout;stream+=1
 for n in [513,65535]:
  x=subprocess.run([str(exe.resolve())],input=struct.pack('<H',n),capture_output=True,timeout=5);assert x.returncode==2 and not x.stdout;stream+=1
 p=subprocess.Popen([str(exe.resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);p.stdout.close();p.communicate(raw,timeout=5);assert p.returncode==3;stream+=1
 results.append({'mode':mode,'passed':True,'queryCases':len(cases),'streamControls':stream,'binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest()});print(mode,len(cases),'exact DNS query/response cases passed',flush=True)
(D/'RESULTS.json').write_text(json.dumps({'passed':True,'results':results,'scope':'Native Mac bounded local-zone DNS payload transformation; no recursion, forwarding, real client resolver, DNSSEC validation, VM102 or production DNS qualification','sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in V.glob('*') if p.is_file()}},indent=2)+'\n')
