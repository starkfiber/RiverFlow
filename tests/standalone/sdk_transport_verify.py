"""SDK B native transport controls; original warm SDK A remains untouched."""
from pathlib import Path
import errno, fcntl, hashlib, importlib.util, json, os, signal, subprocess, sys, tempfile, threading

R=Path(__file__).resolve().parents[2]
if len(sys.argv)not in(3,4)or(len(sys.argv)==4 and sys.argv[3]!='--plain'):raise SystemExit('sdk_transport_verify.py COMPILER FROZEN-SDK-A [--plain]')
OPT=len(sys.argv)==3
C=Path(sys.argv[1]).resolve();A=Path(sys.argv[2]).resolve()
D=Path(tempfile.mkdtemp(prefix='sdk-transport-',dir=R/'artifacts'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={p.name:sha(p)for p in A.iterdir()if p.is_file()}
spec=importlib.util.spec_from_file_location('rf2_transport_package',R/'experiments/sdk-packages/package.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack);B=pack.create(D/'sdk-b')
checks=[];executions=[]
def record(name,good,detail=None):
 checks.append(dict(name=name,passed=bool(good),detail=detail))
 report=dict(schema='rf2.sdk-transport-checks.v1',compiler=str(C),compilerSHA256=sha(C),compilerMode='optimized'if OPT else'plain',testSourceSHA256=sha(Path(__file__)),frozenSDK=str(A),frozenFiles=before,sdkB=str(B),sdkManifestSHA256=sha(B/'rf2-sdk.manifest'),checks=checks,executions=executions,allPassed=all(x['passed']for x in checks),limits=['Mac ARM64 Darwin descriptor policy, not process-global signal handling or other platforms','Ordinary returns only; no cleanup on kill/traps/process exit or concurrent descriptor mutation','A failed OS write may already have delivered a prefix; no transactional stream rollback','Restore-failure controls are explicit source-hooked models, not observed kernel failures','No verified owned TTY was available; TTY behavior remains unqualified'])
 (D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
 if not good:raise AssertionError((name,detail,D))
def native_compile(source,name,sdk):
 w=D/name;w.mkdir();p=w/'main.flow';p.write_text(source);out=w/'program'
 cmd=[str(C),str(p),str(out),'--sdk-root',str(sdk),*(['--opt']if OPT else[])]
 q=subprocess.run(cmd,capture_output=True,timeout=30);(w/'COMPILE.log').write_bytes(q.stdout+q.stderr)
 record(name+' compiles',q.returncode==0,q.stderr.decode(errors='replace'))
 subprocess.run(['/usr/bin/codesign','-s','-',str(out)],check=True,capture_output=True)
 return out
source='''profile RF2_SYSTEM_A64_V1
use "@rf2/v1/mcp.flow"
resource TransportFile(IO)
fn mcp_execute(out:Writer):IO
 let count=buffer("transport_callback_count",8)
 do store64(count,load64(count)+1)
 if load64(count)==1
  return err(22)
 end
 do writer_text(out,"{\\"ok\\":true}")
 return ok(out.used)
end
fn operation(mode):IO
 let fd=open("/dev/null",0,0)
 if fd>>63
  return err(0-fd)
 end
 do store64(buffer("transport_cleanup_fd",8),fd)
 defer close(fd)
 if text_equal(mode,io_size(mode),"mcp-input-closed",16)
  do close(0)
 end
 if text_equal(mode,io_size(mode),"mcp-output-closed",17)|text_equal(mode,io_size(mode),"io-output-closed",16)
  do close(1)
 end
 if text_equal(mode,io_size(mode),"io",2)|text_equal(mode,io_size(mode),"io-output-closed",16)
  return io_write_no_sigpipe(1,"hello\\n",6)
 end
 if text_equal(mode,io_size(mode),"io-large",8)
  let data=buffer("transport_large",131072)
  let i=0
  while i<131072
   do store8(data+i,120)
   set i=i+1
  end
  return io_write_no_sigpipe(1,data,131072)
 end
 if text_equal(mode,io_size(mode),"io-empty",8)
  do close(1)
  return io_write_no_sigpipe(1,0,0)
 end
 return mcp_serve("transport-check","1","report","Read-only transport check")
end
fn owned_operation(mode):IO
 own file=TransportFile("/dev/null",0,0)
 return operation(mode)
end
fn main(argc,argv)
 if argc!=3
  return 3
 end
 let mode=load64(argv+8)
 let initial=0
 if text_equal(load64(argv+16),io_size(load64(argv+16)),"1",1)
  set initial=1
 end
 do syscall6(92,1,73,initial,0,0,0)
 # No concurrent descriptor operations occur in this test process: the next
 # resource acquisition takes the lowest free descriptor just observed here.
 let owner_fd=open("/dev/null",0,0)
 do close(owner_fd)
 let failure=0
 let value=0
 handle owned_operation(mode)
 ok completed
  set value=completed
 err operation_error
  set failure=operation_error
 end
 let flags=syscall6(92,1,74,0,0,0,0)
 let descriptor=load64(buffer("transport_cleanup_fd",8))
 let closed=syscall6(92,descriptor,1,0,0,0,0)
 let owner_closed=syscall6(92,owner_fd,1,0,0,0,0)
 let out=Writer(buffer("transport_diagnostic",512),512,0,0)
 do writer_text(out,"{\\"error\\":")
 do writer_number(out,failure)
 do writer_text(out,",\\"value\\":")
 do writer_number(out,value)
 do writer_text(out,",\\"flags\\":")
 do writer_number(out,flags)
 do writer_text(out,",\\"cleanup\\":")
 do writer_number(out,closed>>63)
 do writer_text(out,",\\"owned_cleanup\\":")
 do writer_number(out,owner_closed>>63)
 do writer_text(out,"}\\n")
 handle io_write_all(2,out.data,out.used)
 ok diagnostic
 err ignored
 end
 if failure
  return 2
 end
 return 0
end
'''
program=native_compile(source,'native-b',B)
# A baseline uses only A APIs; neither A source nor package bytes are modified.
old=native_compile(source.replace('io_write_no_sigpipe(', 'io_write_all('),'native-a',A)
init=dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2025-11-25',capabilities={},clientInfo=dict(name='test',version='1')))
ready=dict(jsonrpc='2.0',method='notifications/initialized')
call=lambda i:dict(jsonrpc='2.0',id=i,method='tools/call',params=dict(name='report',arguments={}))
ping=lambda i:dict(jsonrpc='2.0',id=i,method='ping')
encode=lambda *items:''.join(json.dumps(x,separators=(',',':'))+'\n'for x in items).encode()
def execute(name,mode,initial=0,input=b'',output=None,exe=program):
 q=subprocess.run([str(exe),mode,str(initial)],input=input,stdout=subprocess.PIPE if output is None else output,stderr=subprocess.PIPE,timeout=10,restore_signals=True)
 detail=None
 try:detail=json.loads(q.stderr)
 except ValueError:pass
 row=dict(name=name,executableSHA256=sha(exe),mode=mode,initial=initial,exit=q.returncode,inputSHA256=hashlib.sha256(input).hexdigest(),stdoutSHA256=hashlib.sha256(q.stdout or b'').hexdigest(),stdoutBytes=len(q.stdout or b''),stderr=q.stderr.decode(errors='replace'),detail=detail);executions.append(row)
 return q,detail
def broken(name,mode,initial=0,exe=program):
 read,write=os.pipe();os.close(read)
 try:return execute(name,mode,initial,input=encode(init) if mode.startswith('mcp')else b'',output=write,exe=exe)
 finally:os.close(write)
for initial in (0,1):
 for mode in ('io','mcp'):
  q,d=execute('pipe success '+mode,mode,initial,input=encode(init)if mode=='mcp'else b'')
  record('ordinary pipe '+mode+' flag'+str(initial),q.returncode==0 and d['error']==0 and d['flags']==initial and d['cleanup']==1,d)
  with(D/('regular-'+mode+'-'+str(initial))).open('wb')as out:q,d=execute('regular output '+mode,mode,initial,input=encode(init)if mode=='mcp'else b'',output=out)
  record('regular file '+mode+' flag'+str(initial),q.returncode==0 and d['flags']==initial and d['cleanup']==1,d)
  q,d=broken('closed reader '+mode,mode,initial)
  record('EPIPE recoverable '+mode+' flag'+str(initial),q.returncode==2 and d['error']==errno.EPIPE and d['flags']==initial and d['cleanup']==1,d)
 for mode in ('io-output-closed','mcp-output-closed'):
  q,d=execute('closed output '+mode,mode,initial,input=encode(init)if mode.startswith('mcp')else b'')
  record('EBADF output '+mode+' flag'+str(initial),q.returncode==2 and d['error']==errno.EBADF and d['cleanup']==1,d)
 q,d=execute('closed input','mcp-input-closed',initial)
 record('EBADF read flag'+str(initial),q.returncode==2 and d['error']==errno.EBADF and d['flags']==initial and d['cleanup']==1,d)
 q,d=execute('empty write no descriptor effect','io-empty',initial)
 record('empty write flag'+str(initial),q.returncode==0 and d['value']==0 and d['cleanup']==1,d)
 # Fill a real nonblocking pipe without a reader drain: actual EAGAIN, no hooks.
 for mode in ('io','mcp'):
  read,write=os.pipe();fcntl.fcntl(write,fcntl.F_SETFL,fcntl.fcntl(write,fcntl.F_GETFL)|os.O_NONBLOCK)
  try:
   filled=0
   while True:
    try:filled+=os.write(write,b'x'*4096)
    except BlockingIOError:break
   q,d=execute('full nonblocking pipe '+mode,mode,initial,input=encode(init)if mode=='mcp'else b'',output=write)
   record('EAGAIN recoverable '+mode+' flag'+str(initial),q.returncode==2 and d['error']in(errno.EAGAIN,errno.EWOULDBLOCK)and d['flags']==initial and d['cleanup']==1,dict(result=d,filled=filled))
  finally:os.close(read);os.close(write)
 # The receiving side closes after an observed prefix of a larger real write.
 read,write=os.pipe();observed=[]
 def receiver():
  try:observed.append(len(os.read(read,4096)))
  finally:os.close(read)
 t=threading.Thread(target=receiver);t.start()
 try:q,d=execute('partial output then receiver close','io-large',initial,output=write)
 finally:os.close(write)
 t.join(timeout=2)
 record('partial delivery EPIPE flag'+str(initial),q.returncode==2 and d['error']==errno.EPIPE and d['flags']==initial and d['cleanup']==1 and not t.is_alive()and 0<sum(observed)<131072,dict(result=d,observedBytes=sum(observed)))
q,d=broken('A default signal failure','mcp',0,exe=old)
record('old A SIGPIPE reproduced',q.returncode==-signal.SIGPIPE,dict(exit=q.returncode,detail=d))
q,d=execute('A fatal IO exit','mcp-output-closed',0,input=encode(init),exe=old)
record('old A fatal exit1 reproduced',q.returncode==1 and d is None,dict(exit=q.returncode,detail=d))
# Ordinary protocol handling and callback errors stay recoverable on one session.
payload=encode(init,ready,call(2),ping(3),call(4))
q,d=execute('callback failure then recovery','mcp',input=payload)
responses=[json.loads(x)for x in q.stdout.splitlines()]
record('callback failure remains a tool error',responses[1]['id']==2 and responses[1]['result']['isError']is True and 'structuredContent'not in responses[1]['result'])
record('session usable after callback refusal',responses[2]['id']==3 and responses[2]['result']=={} and responses[3]['id']==4 and responses[3]['result']['structuredContent']==dict(ok=True))
record('normal EOF restores descriptor and cleanup',q.returncode==0 and d['flags']==0 and d['cleanup']==1,d)
record('owned caller resource closed across ordinary B returns',all(x['detail']['owned_cleanup']==1 for x in executions if x['executableSHA256']==sha(program)and x['detail']is not None))
# Explicitly source-hooked restore failures test precedence, not kernel behavior.
hook=D/'sdk-restore-failure';hook.mkdir()
for p in B.iterdir():
 if p.is_file():(hook/p.name).write_bytes(p.read_bytes())
for name,line in [('io.flow','let restored=syscall6(92,fd,73,previous,0,0,0)'),('mcp.flow','let restored=syscall6(92,1,73,previous,0,0,0)')]:
 p=hook/name;s=p.read_text();assert s.count(line)==1;p.write_text(s.replace(line,'let restored=0-9'))
(hook/'rf2-sdk.manifest').write_text('rf2-sdk-v1\n'+''.join(sha(hook/name)+' '+name+'\n'for name in pack.FILES))
hook_program=native_compile(source,'native-hooked-restore',hook)
for mode in ('io','mcp'):
 q,d=execute('hooked restore-only error '+mode,mode,input=encode(init)if mode=='mcp'else b'',exe=hook_program)
 record('hooked restore-only failure '+mode,q.returncode==2 and d['error']==65536+errno.EBADF and d['cleanup']==1,d)
 q,d=broken('hooked primary plus restore failure '+mode,mode,exe=hook_program)
 record('hooked primary error preserved '+mode,q.returncode==2 and d['error']==errno.EPIPE and d['cleanup']==1,d)
headers={}
for relative in ('sys/fcntl.h','sys/syscall.h'):
 p=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include')/relative;s=p.read_text();headers[str(p)]=dict(SHA256=sha(p),constants=[line for line in s.splitlines()if any(token in line for token in ('#define F_SETNOSIGPIPE','#define F_GETNOSIGPIPE','#define\tSYS_fcntl '))])
record('local Apple headers match descriptor constants',any('73'in line for h in headers.values()for line in h['constants'])and any('74'in line for h in headers.values()for line in h['constants'])and any('92'in line for h in headers.values()for line in h['constants']),headers)
record('frozen original SDK A bytes unchanged',before=={p.name:sha(p)for p in A.iterdir()if p.is_file()})
report=json.loads((D/'RESULTS.json').read_text());report.update(count=len(checks),headers=headers,sourceSHA256=sha(D/'native-b/main.flow'),sdkFiles={p.name:sha(p)for p in B.iterdir()if p.is_file()},testSourceSHA256=sha(__file__));(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(directory=str(D),checks=len(checks),allPassed=report['allPassed'])))
