"""Native library/application/HTTP checks with independent byte and integer oracles."""
from pathlib import Path
import bisect
import hashlib
import html
import http.client
import json
import os
import random
import select
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.parse

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'examples/documents'
COMPILER=Path(os.environ['RF2_TEST_COMPILER']).resolve()
OUT=Path(tempfile.mkdtemp(prefix='documents-',dir=ROOT/'artifacts'))
ROWS=[]
CAP=(1<<64)-1
RNG=random.Random(3702026)

def check(name,ok,detail=None):
    ROWS.append(dict(name=name,passed=bool(ok),detail=detail))
    (OUT/'progress.json').write_text(json.dumps(ROWS,indent=2)+'\n')
    assert ok,(name,detail)

def call(args,data=b'',**kw):
    return subprocess.run(list(map(str,args)),input=data,capture_output=True,timeout=15,**kw)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build(entry,dest,opt):
    p=call([COMPILER,entry,dest]+(['--opt'] if opt else []));check('compile:'+dest.name,p.returncode==0,p.stderr.decode())
    p=call(['/usr/bin/codesign','-s','-',dest]);check('sign:'+dest.name,p.returncode==0)
    return dest

original={str(p.relative_to(ROOT)):sha(p) for p in SOURCE.rglob('*') if p.is_file()}
fixture=OUT/'probe.bin'

def probe(binary,mode,data,arg='',option=0):
    fixture.write_bytes(data)
    p=call([binary,mode,fixture,arg,option]);check('probe-process:'+mode,p.returncode==0,p.stderr.decode())
    return json.loads(p.stdout)

def fold_bytes(b):return bytes(c+32 if 65<=c<=90 else c for c in b)

def search_ref(data,q,fold):
    if fold:data,q=fold_bytes(data),fold_bytes(q)
    if not q:return [0,len(data)+1,0,len(data)]
    places=[];pos=0
    while True:
        pos=data.find(q,pos)
        if pos<0:break
        places.append(pos);pos+=len(q)
    return [0,len(places),places[0] if places else CAP,places[-1] if places else CAP]

def measure_ref(data):
    try:
        s=data.decode('utf8')
        if any(ord(c)<32 and c not in '\t\r\n ' for c in s):raise ValueError()
    except (UnicodeDecodeError,ValueError):return [84,0,0,0]
    lines=data.count(b'\n')+(bool(data) and not data.endswith(b'\n'))
    words=0;active=False
    for c in s:
        if c in '\t\r\n ':active=False
        elif not active:words+=1;active=True
    return [0,len(s),int(lines),words]

def lines_ref(data):
    result=[];start=0
    for i,c in enumerate(data):
        if c==10:
            result.append([start,i-start-(i>start and data[i-1]==13)]);start=i+1
    if start<len(data):result.append([start,len(data)-start])
    return result

BINS={}
for opt in [False,True]:
    suffix='opt' if opt else 'default'
    probe_bin=build(SOURCE/'library-probe.flow',OUT/('probe-'+suffix),opt)
    workspace=build(SOURCE/'workspace.flow',OUT/('workspace-'+suffix),opt)
    lines=build(SOURCE/'text-lines.flow',OUT/('lines-'+suffix),opt)
    BINS[suffix]=dict(probe=probe_bin,workspace=workspace,lines=lines)
    valid=[b'',b'hello world',b'\n',b'a\r\nb\n',b'a\rb','தமிழ் அறிவு\n🙂 café\n'.encode(),b'\t \r\n',b'\xef\xbb\xbftext']
    invalid=[b'\0',b'a\x01',b'\xc0\xaf',b'\xed\xa0\x80',b'\xf4\x90\x80\x80',b'\xf0\x9f',b'\x80',b'\xff']
    for _ in range(24):valid.append(''.join(RNG.choice(['a','B','தமிழ்','🙂','é','\n',' ','\t','\r']) for _ in range(RNG.randrange(80))).encode())
    for i,data in enumerate(valid+invalid):
        check(suffix+':measure:'+str(i),probe(probe_bin,'measure',data)==measure_ref(data))
    for i,data in enumerate(valid):
        check(suffix+':lines:'+str(i),probe(probe_bin,'lines',data)==lines_ref(data))
    for i in range(28):
        data=''.join(RNG.choice(['a','A','ba','தமிழ்',' ','🙂']) for _ in range(80)).encode()
        query=RNG.choice(['a','A','ba','தமிழ்','🙂','missing',''])
        for folding in [0,1]:
            check(suffix+':search:'+str(i)+':'+str(folding),probe(probe_bin,'search',data,query,folding)==search_ref(data,query.encode(),folding))
    check(suffix+':long-query-refused',probe(probe_bin,'search',b'abc','q'*257)==[22,0,CAP,CAP])
    check(suffix+':invalid-fold-refused',probe(probe_bin,'search',b'abc','a',2)==[22,0,CAP,CAP])
    for i in range(20):
        data=bytes(RNG.randrange(256) for _ in range(RNG.randrange(300)))
        check(suffix+':sorted-unique:'+str(i),probe(probe_bin,'collections',data)==sorted(set(data)))
    check(suffix+':rows-capacity-read-refusal',probe(probe_bin,'rows',b'')==[56,4096,99])
    parse_cases=[b'',b'0',b'00',b'01',b'-1',b'+1',b'1 ',b'0x10',b'18446744073709551615',b'18446744073709551616',b'999999999999999999999']
    parse_cases += [str(RNG.randrange(1<<64)).encode() for _ in range(12)]
    for i,data in enumerate(parse_cases):
        maximum=CAP if i%2 else 100000
        expected=[22,0]
        if data and len(data)<=20 and all(48<=c<=57 for c in data) and not(len(data)>1 and data[0]==48):
            number=int(data);expected=[0,number] if number<=maximum else [75,0]
        check(suffix+':parse:'+str(i),probe(probe_bin,'parse',data,option=maximum)==expected)
    for i,data in enumerate([b'',b'abc',b'<>&\'"','தமிழ்🙂'.encode(),b'&&&&',b'\n\t']):
        escaped=data.replace(b'&',b'&amp;').replace(b'<',b'&lt;').replace(b'>',b'&gt;').replace(b'\'',b'&#39;').replace(b'"',b'&quot;')
        for capacity in sorted(set([0,1,len(escaped),max(0,len(escaped)-1),512])):
            got=probe(probe_bin,'html',data,option=capacity)
            if len(escaped)>capacity:expected=dict(status=28,count=0,bytes=[170]*514)
            else:expected=dict(status=0,count=len(escaped),bytes=list(escaped)+[170]*(514-len(escaped)))
            check(suffix+':html-atomic:'+str(i)+':'+str(capacity),got==expected)
    for i,data in enumerate([b'',b'a+b',b'%20',b'%E0%AE%A4',b'%',b'%GG',b'%00',b'%0A',b'%7f',b'abc',b'a%26b']):
        for capacity in [0,1,3,16,512]:
            decoded=None
            try:
                p=0;result=bytearray()
                while p<len(data):
                    c=data[p]
                    if c==43:c=32
                    elif c==37:
                        if p+2>=len(data):raise ValueError()
                        a,b=data[p+1:p+3]
                        if a not in b'0123456789abcdefABCDEF' or b not in b'0123456789abcdefABCDEF':raise ValueError()
                        c=int(data[p+1:p+3],16);p+=2
                    if c<32 or c==127:raise ValueError()
                    result.append(c);p+=1
                decoded=bytes(result)
            except ValueError:pass
            got=probe(probe_bin,'decode',data,option=capacity)
            # Exact precedence may meet capacity before a later malformed byte.
            if decoded is None:
                check(suffix+':decode-refusal:'+str(i)+':'+str(capacity),got['status'] in [22,28] and got['bytes']==[170]*514)
            elif len(decoded)>=capacity:
                check(suffix+':decode-capacity:'+str(i)+':'+str(capacity),got==dict(status=28,count=0,bytes=[170]*514))
            else:
                check(suffix+':decode:'+str(i)+':'+str(capacity),got==dict(status=0,count=len(decoded),bytes=list(decoded)+[0]+[170]*(513-len(decoded))))

# Use only generated, non-sensitive files in the explicit document manifest.
corpus=OUT/'supplied documents';corpus.mkdir()
contents=[b'Alpha beta\nSecond line\n','தமிழ் அறிவு\nALPHA and alpha\n'.encode(),b'<script>alert(1)</script> & "quotes"\n',b'']
names=['first.txt','Tamil notes.txt','<unsafe>".txt','empty.txt']
files=[]
for name,data in zip(names,contents):
    p=corpus/name;p.write_bytes(data);files.append(p)
manifest=OUT/'documents.txt';manifest.write_text('\n'.join(map(str,files))+'\n')
hashes={str(p):sha(p) for p in files}
expected=dict(documents=4,bytes=sum(map(len,contents)),snapshot=True,items=[])
for i,(p,data) in enumerate(zip(files,contents)):
    info=measure_ref(data)
    expected['items'].append(dict(id=i,name=p.name,source=str(p),bytes=len(data),scalars=info[1],lines=info[2],words_ascii_breaks=info[3]))
for mode,bins in BINS.items():
    p=call([bins['workspace'],manifest,'--catalog']);check(mode+':catalog',p.returncode==0 and json.loads(p.stdout)==expected,p.stderr.decode())
    for i,data in enumerate(contents):
        query='alpha';parts=lines_ref(data);wanted=[j+1 for j,(a,n) in enumerate(parts) if b'alpha' in fold_bytes(data[a:a+n])]
        p=call([bins['lines'],files[i],query,'--fold']);check(mode+':line-app:'+str(i),p.returncode==0 and json.loads(p.stdout)==dict(bytes=len(data),lines=len(parts),matching_lines=wanted))
    p=call([bins['workspace'],manifest,'--catalog'],preexec_fn=lambda:os.close(1));check(mode+':closed-output',p.returncode!=0)

bad=OUT/'bad-input';bad.write_bytes(b'invalid\xff')
large=OUT/'oversized';large.write_bytes(b'a'*65537)
fifo=OUT/'fifo';os.mkfifo(fifo)
link=OUT/'symlink';link.symlink_to(files[0])
invalid_lists=[b'',b'\0',str(OUT/'missing').encode(),str(corpus).encode(),str(fifo).encode(),str(link).encode(),str(bad).encode(),str(large).encode(),(str(files[0])+'\n'+str(files[0])).encode(),b'a'*1024,(('\n'.join(map(str,files)))+'\n\n').encode(),b'a'*32769]
for i,data in enumerate(invalid_lists):
    bad_list=OUT/('bad-list-'+str(i));bad_list.write_bytes(data)
    for mode,bins in BINS.items():
        for action in ['--catalog','--serve']:
            p=call([bins['workspace'],bad_list,action]);check(mode+':import-refusal:'+str(i)+action,p.returncode!=0 and not p.stdout,p.stderr.decode())
# Corpus and count limits use distinct regular files, not duplicates.
large_files=[]
for i in range(65):
    p=OUT/('bulk-'+str(i));p.write_bytes(b'z'*65536 if i<17 else b'');large_files.append(p)
valid_list=OUT/'max-valid.txt';valid_list.write_text('\n'.join(map(str,large_files[:16])))
for mode,bins in BINS.items():
    p=call([bins['workspace'],valid_list,'--catalog']);check(mode+':max-valid-corpus',p.returncode==0 and json.loads(p.stdout)['bytes']==1048576)
for label,chosen in [('corpus-size',large_files[:17]),('document-count',large_files)]:
    if label=='document-count':
        for p in large_files:p.write_bytes(b'')
    limit_list=OUT/(label+'.txt');limit_list.write_text('\n'.join(map(str,chosen)))
    for mode,bins in BINS.items():
        p=call([bins['workspace'],limit_list,'--catalog']);check(mode+':'+label,p.returncode!=0 and not p.stdout)

# Check descriptor balance inside one native process, rather than relying on process exit.
resource_source = r"""profile RF2_SYSTEM_A64_V1
use "lib/io.flow"
fn check_files(good,bad):IO
 let before=open("/dev/null",0,0)
 if before>>63
  return err(5)
 end
 do close(before)
 let data=buffer("resource_probe",65537)
 let i=0
 while i<100
  handle io_regular(good,data,65536)
  ok bytes
  err error
   return err(error)
  end
  handle io_regular(bad,data,65536)
  ok unexpected
   return err(1)
  err expected_error
  end
  set i=i+1
 end
 let after=open("/dev/null",0,0)
 if after>>63
  return err(5)
 end
 do close(after)
 if after!=before
  return err(1)
 end
 return ok(0)
end
fn main(argc,argv)
 if argc!=3
  return 2
 end
 let status=0
 handle check_files(load64(argv+8),load64(argv+16))
 ok balanced
 err failure
  set status=1
 end
 return status
end
"""
resource_tree=OUT/'resource-source';shutil.copytree(SOURCE,resource_tree)
(resource_tree/'resource-probe.flow').write_text(resource_source)
for opt in [False,True]:
    executable=build(resource_tree/'resource-probe.flow',OUT/('resource-'+str(opt)),opt)
    for refused in [corpus,fifo,link,OUT/'not-there']:
        p=call([executable,files[0],refused]);check('descriptor-balance:'+str(opt)+':'+refused.name,p.returncode==0)

# Native browser controller and protocol refusal campaign.
def start_server(binary):
    p=subprocess.Popen([str(binary),str(manifest),'--serve'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert select.select([p.stdout],[],[],5)[0]
    url=p.stdout.readline().decode().strip();assert url.startswith('http://127.0.0.1:'),url
    return p,url

def fetch(base,target):
    u=urllib.parse.urlsplit(base);c=http.client.HTTPConnection(u.hostname,u.port,timeout=6)
    try:
        c.request('GET',target);r=c.getresponse();return r.status,dict(r.getheaders()),r.read()
    finally:c.close()

def raw(port,payload):
    with socket.create_connection(('127.0.0.1',port),timeout=6) as s:
        s.sendall(payload);s.settimeout(6);data=b''
        while True:
            try:block=s.recv(65536)
            except ConnectionResetError:break
            if not block:break
            data+=block
    return int(data.split(b' ',2)[1]) if data else 0

for mode,bins in BINS.items():
    proc,url=start_server(bins['workspace']);u=urllib.parse.urlsplit(url);host=u.netloc
    try:
        code,headers,body=fetch(url,'/');check(mode+':browser-home',code==200 and b'RF\xc2\xb2' in body and b'&lt;script&gt;' not in body)
        check(mode+':browser-security-headers',headers.get('Cache-Control')=='no-store' and "script-src" not in headers['Content-Security-Policy'] and "default-src 'none'" in headers['Content-Security-Policy'])
        for target,phrase in [('/?doc=2',b'&lt;script&gt;alert(1)&lt;/script&gt;'),('/?q=ALPHA&fold=1',b'2 documents match.'),('/?q='+urllib.parse.quote('தமிழ்'),b'1 document matches.'),('/?q=absent',b'No matching documents')]:
            code,headers,body=fetch(url,target);check(mode+':browser-route:'+target,code==200 and phrase in body and b'<script>' not in body)
        code,headers,body=fetch(url,'/catalog.json');check(mode+':browser-catalog',code==200 and json.loads(body)==expected and headers['Content-Type'].startswith('application/json'))
        for target in ['/?q=%','/?q=%00','/?q=%FF','/?q=a&q=b','/?q=a&unknown=1','/?doc=01','/?doc=4','/?fold=2','/?q=a&','/?q='+('x'*257),'/?q=%0D%0A']:
            check(mode+':bad-query:'+target,fetch(url,target)[0]==400)
        for target in ['/etc/passwd','/../secret','/robots.txt']:
            check(mode+':unknown-path:'+target,fetch(url,target)[0]==404)
        base=f'GET / HTTP/1.1\r\nHost: {host}\r\n'.encode()
        attacks=[b'GET  HTTP/1.1\r\nHost: '+host.encode()+b'\r\n\r\n',b'POST / HTTP/1.1\r\nHost: '+host.encode()+b'\r\n\r\n',base+b'Host: '+host.encode()+b'\r\n\r\n',b'GET / HTTP/1.1\r\nHost: evil.example\r\n\r\n',base+b'Origin: https://evil.example\r\n\r\n',base+b'Transfer-Encoding: chunked\r\n\r\n',base+b'Content-Length: 1\r\n\r\nx',base+b'Content-Length: 0\r\nContent-Length: 0\r\n\r\n',base+b'Expect: 100-continue\r\n\r\n',base+b'\r\nextra',b'GET / HTTP/1.0\r\n\r\n',base+b'X-Invalid: \x01\r\n\r\n']
        for i,request in enumerate(attacks):check(mode+':protocol-refusal:'+str(i),raw(u.port,request)==400)
        # Idle preconnections must not block a ready browser request.
        idle=[socket.create_connection(('127.0.0.1',u.port),timeout=5) for _ in range(2)]
        try:check(mode+':idle-recovery',fetch(url,'/')[0]==200)
        finally:
            for s in idle:s.close()
        check(mode+':partial-request-deadline',raw(u.port,base)==400)
        check(mode+':after-refusals',fetch(url,'/catalog.json')[2]==json.dumps(expected,separators=(',',':')).encode()+b'\n')
        # Explicitly show that a running process serves its loaded snapshot.
        files[0].write_bytes(b'Changed after startup\n')
        check(mode+':snapshot-stable-after-source-change',json.loads(fetch(url,'/catalog.json')[2])==expected)
        files[0].write_bytes(contents[0])
    finally:
        proc.terminate();proc.wait(timeout=5)
        check(mode+':owned-test-server-exited',proc.returncode is not None)
    with socket.socket() as s:check(mode+':listener-closed',s.connect_ex(('127.0.0.1',u.port))!=0)

# Isolated mutations must affect both applications using the same physical modules.
for module,old,new in [
    ('text.flow','return c+32','return c'),
    ('collections.flow','fn items_insert_unique(values:Items,key):IO\n','fn items_insert_unique(values:Items,key):IO\n if key==1\n  return ok(0)\n end\n')]:
    copy=OUT/('mutated-'+module);shutil.copytree(SOURCE,copy)
    library=copy/'lib'/module;source=library.read_text();assert old in source;library.write_text(source.replace(old,new,1))
    workspace=build(copy/'workspace.flow',OUT/('mutated-workspace-'+module),True)
    lines=build(copy/'text-lines.flow',OUT/('mutated-lines-'+module),True)
    p=call([lines,files[0],'ALPHA','--fold']);check('shared-mutation-lines:'+module,p.returncode==0 and json.loads(p.stdout)['matching_lines']==[])
    process,base=start_server(workspace)
    try:check('shared-mutation-workspace:'+module,b'1 document matches.' in fetch(base,'/?q=ALPHA&fold=1')[2])
    finally:process.terminate();process.wait(timeout=5)

# Original input bytes and canonical RF2 source are unchanged by execution.
check('originals-unchanged',all(sha(Path(p))==value for p,value in hashes.items()))
check('canonical-source-unchanged',all(sha(ROOT/p)==value for p,value in original.items()))
report=dict(schema='rf2.documents.v1',passed=True,checks=len(ROWS),compilerSHA256=sha(COMPILER),controllerSHA256=sha(Path(__file__)),sources=original,binaries={mode:{name:sha(path) for name,path in bins.items()} for mode,bins in BINS.items()},rows=ROWS,scope='Actual native Mac execution in both compiler modes. Independent UTF-8/byte/collection/application oracles, failure and HTTP controls. Generated non-sensitive inputs only; no physical hardware, performance, token or independent security certification claim.')
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,checks=len(ROWS),report=str(OUT/'report.json'))))
