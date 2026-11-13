"""Native RF2 compiler diagnostics and literal range policy, with clean byte oracle."""
from pathlib import Path
import hashlib,json,os,re,subprocess,time
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
OLD=Path(os.environ.get('RF2_OLD_COMPILER',R/'output/rf2c-030-pack')).resolve()
D=R/'artifacts/diagnostics'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
ROWS=[];serial=0

def run(args):
 return subprocess.run(list(map(str,args)),capture_output=True,timeout=30,env={'PATH':'/nonexistent'})

def source(name,text):
 p=D/(name+'.rf2');p.write_text(text);return p

def fail(name,text,message,line=None,label='source',extra=None):
 global serial
 serial+=1;p=source(name,text)if isinstance(text,str)else text;out=D/('bad-'+str(serial))
 q=run([C,p,out,'--opt','--compact',*(extra or [])]);err=q.stderr.decode(errors='replace')
 assert q.returncode==1 and not out.exists(),(name,q.returncode,err)
 assert message in err,(name,err)
 if label:
  match=re.search(r'near '+label+r' ([0-9]+):([0-9]+) \(line:byte-column; entry ([^\n]+)\)',err)
  assert match,(name,err)
  if line is not None:assert int(match[1])==line,(name,line,err)
  assert int(match[2])>=1
 else:assert 'near source'not in err and 'near expanded-source'not in err,(name,err)
 ROWS.append(dict(case=name,refused=True,stderr=err))

HEADER='profile RF2_SYSTEM_A64_V1\nfn main(argc,argv)\n'
fail('unknown-local',HEADER+' return absent\nend\n','unknown local',3)
fail('unknown-function',HEADER+' return absent(1)\nend\n','unknown function',3)
fail('missing-end',HEADER+' return 0\n','missing end',4)
fail('no-newline-eof',HEADER+' return 0','missing end',3)
fail('bad-parameter','profile RF2_SYSTEM_A64_V1\nfn main(argc argv)\n return 0\nend\n','expected:',2)
fail('unclosed-string',HEADER+' let p="private local text\nend\n','raw control in string',3)
fail('eof-string',HEADER+' let p="private local text','unterminated string',3)
fail('unsupported-escape',HEADER+' let p="private\\q"\n return 0\nend\n','unsupported string escape',3)
fail('empty-hex',HEADER+' return 0x\nend\n','empty number',3)
fail('duplicate-local',HEADER+' let n=1\n let n=2\n return n\nend\n','duplicate local',4)
fail('raw-non-ascii',HEADER+' return π\nend\n','expression',3)
for i,value in enumerate(['18446744073709551616','184467440737095516160','99999999999999999999999999999999999999','0x10000000000000000','0xffffffffffffffffffffffffffffffff','-18446744073709551616']):
 fail('overflow-'+str(i),HEADER+' return '+value+'\nend\n','integer literal exceeds u64',3)
# Diagnostics must not emit unbounded source tokens or terminal control bytes.
for name,tail in [('bounded-token','x'*100000),('escaped-control','\x1b[31m'),('nul-control','\x00'),('tab-control','\x01')]:
 serial+=1;p=source(name,HEADER+' return 0\nend\n'+tail+'\n');out=D/('bad-'+str(serial))
 q=run([C,p,out,'--opt','--compact']);assert q.returncode==1 and not out.exists()
 assert len(q.stderr)<1024,(name,len(q.stderr))
 assert all(c==10 or 32<=c<=126 for c in q.stderr),(name,q.stderr)
 if name=='bounded-token':assert b'...'in q.stderr and b'x'*81 not in q.stderr
 ROWS.append(dict(case=name,refused=True,stderrBytes=len(q.stderr),boundedSanitized=True))
# Cache errors are not source errors; never append a stale parser location.
fail('missing-cache',HEADER+' return 0\nend\n','function cache requires existing private directory',label=None,extra=['--reuse-pack',D/'missing-directory'])
fail('missing-input',D/'not-a-file.rf2','source open failed',label=None)
# Imported offsets are expanded positions and explicitly must not be presented as original module positions.
module=D/'lib.rf2';module.write_text('module lib\nfn helper(x)\n return absent\nend\n')
entry=source('imports','profile RF2_SYSTEM_A64_V1\nuse "lib.rf2"\nfn main(argc,argv)\n return helper(1)\nend\n')
fail('imported-error',entry,'unknown local',3,label='expanded-source')
module.write_text('module lib\nfn helper(x)\n return x+1\nend\n')
# Exact unsigned bytes for valid constants, decoded strings, wrap arithmetic and imports.
valid=[('maximum','return 18446744073709551615',255),('hex-maximum','return 0xffffffffffffffff',255),('signed-minimum','return -9223372036854775808',0),('runtime-wrap','let x=18446744073709551615\n return x+1',0),('decoded-string','let p="a\\nb"\n return load8(p+1)',10)]
for name,body,expected in valid:
 p=source('valid-'+name,HEADER+' '+body+'\nend\n')
 for flags in [[],['--opt'],['--opt','--compact']]:
  serial+=1;a=D/('new-'+str(serial));b=D/('old-'+str(serial))
  q=run([C,p,a,*flags]);old=run([OLD,p,b,*flags]);assert q.returncode==old.returncode==0,(name,q.stderr,old.stderr)
  assert a.read_bytes()==b.read_bytes(),name
  subprocess.run(['/usr/bin/codesign','-s','-',a],check=True,capture_output=True)
  got=run([a]).returncode;assert got==expected,(name,got,expected)
  ROWS.append(dict(case=name,flags=flags,unsignedByteMatch=True,exit=got))
for name in ['valid-imports','valid-crlf']:
 p=entry if name=='valid-imports'else source(name,(HEADER+' return 0\nend\n').replace('\n','\r\n'))
 serial+=1;a=D/('new-'+str(serial));b=D/('old-'+str(serial))
 q=run([C,p,a,'--opt','--compact']);old=run([OLD,p,b,'--opt','--compact']);assert q.returncode==old.returncode==0,(name,q.stderr,old.stderr)
 assert a.read_bytes()==b.read_bytes()
 ROWS.append(dict(case=name,unsignedByteMatch=True))
report=dict(passed=True,schema='rf2.compiler.diagnostics.verification.v1',compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),baselineSHA256=hashlib.sha256(OLD.read_bytes()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=ROWS,limits='Finite native Apple Silicon tests. Diagnostic position means lexical token start or current parser cursor, not always the exact offending identifier. Imported source is explicitly expanded; original module provenance is not mapped. Columns count bytes, not display characters. Valid program byte equality does not establish language or platform completeness.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(D/'report.json'),passed=True,cases=len(ROWS))))
