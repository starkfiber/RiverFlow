"""Independent deterministic acceptance checks for the native Number Lab CLI."""
from pathlib import Path
import hashlib,json,os,random,subprocess,time
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_TEST_COMPILER']).resolve()
SOURCE=R/'examples/number-lab/main.rf2'
D=R/'artifacts/number-lab'/('verify-'+str(time.time_ns()));D.mkdir(parents=True)
CONTROLLER=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
HEAD=b'Number Lab\nPlay with bytes, bits and logic. Type help to begin.\n'
BYE=b'See you next time!\n'
ROWS=[]
def run(args,**kw):return subprocess.run([str(x)for x in args],capture_output=True,timeout=30,env={'PATH':'/nonexistent'},**kw)
def show(n):
    ascii_text="'"+chr(n)+"'"if 32<=n<=126 else 'control byte'if n<128 else 'outside ASCII'
    return f'Decimal: {n}  Binary: {n:08b}  Hex: {n:02X}  ASCII: {ascii_text}\n'.encode()
def cleaned(raw):return raw.replace(b'> ',b'')
def session(binary,label,data,expected=None,code=0):
    q=run([binary],input=data)
    assert q.returncode==code and q.stderr==b'',(label,q.returncode,q.stderr)
    if expected is not None:assert cleaned(q.stdout)==HEAD+expected,(label,q.stdout[:500])
    ROWS.append({'case':label,'exit':q.returncode,'stdoutSHA256':hashlib.sha256(q.stdout).hexdigest()})
    return q.stdout
binaries=[]
for optimized in [False,True]:
    for compact in [False,True]:
        out=D/f'number-lab-{optimized}-{compact}'
        flags=(['--opt']if optimized else[])+(['--compact']if compact else[])
        q=run([C,SOURCE,out,*flags]);assert q.returncode==0,q.stderr
        subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True)
        binaries.append(out)
B=binaries[-1]
# Complete byte conversions, NOT and representative binary gates use independent arithmetic.
session(B,'all 256 byte conversions',b''.join(f'show {n}\n'.encode()for n in range(256))+b'quit\n',b''.join(show(n)for n in range(256))+BYE)
session(B,'all 256 byte complements',b''.join(f'not {n}\n'.encode()for n in range(256))+b'quit\n',b''.join(b'NOT flips each of the eight bits.\n'+show(n^255)for n in range(256))+BYE)
generator=random.Random(29013);commands=[];expected=[]
for _ in range(96):
    a=generator.randrange(256);b=generator.randrange(256)
    for op,value,description in [('and',a&b,b'AND keeps shared 1 bits.\n'),('or',a|b,b'OR keeps either 1 bit.\n'),('xor',a^b,b'XOR keeps different bits.\n')]:
        commands.append(f'{op} {a} {b}\n'.encode());expected.append(description+show(value))
session(B,'288 independently computed binary gates',b''.join(commands)+b'quit\n',b''.join(expected)+BYE)
for a in [0,1]:
    for b in [0,1]:
        target=a&b;other=target^1
        session(B,f'quiz truth table {a}/{b}',f'quiz {a} {b}\nanswer {other}\nanswer 2\nanswer {target}\nanswer {target}\nquit\n'.encode(),
            f'AND gate: {a} AND {b} = ? Type answer 0 or answer 1.\n'.encode()+b'Not quite. AND needs two 1 inputs. Try answer again.\nA gate answer is one bit: 0 or 1.\nCorrect! AND is 1 only when both inputs are 1.\nStart a question first, for example: quiz 1 0\n'+BYE)
session(B,'guess feedback, win and reset',b'guess 0\nguess 255\nguess 42\nguess 42\nquiz 1 1\nreset\nanswer 1\nguess 42\nquit\n',
    b'Higher. Try a bigger byte.\nLower. Try a smaller byte.\nYou found it! Here is the secret byte:\n'+show(42)+b'You already found it! Type reset for another round.\nAND gate: 1 AND 1 = ? Type answer 0 or answer 1.\nNew game! Guess a byte from 0 to 255.\nStart a question first, for example: quiz 1 0\nYou found it! Here is the secret byte:\n'+show(42)+BYE)
invalid=[b'wat',b'SHOW 65',b'show',b'show -1',b'show +1',b'show 256',b'show 999',b'show 0000',b'show 1e2',b'show 0x41',b'show 1.0',b'show 1 2',b'and 1',b'and 1 2 3',b'or -1 0',b'xor 1 256',b'not 256',b'quit now',b'reset now',b'help now',b'show \x00',b'show \xff',b'\x1b[2J',b'show 65;quit',b'../../file',b'guess 1000']
for i,line in enumerate(invalid):
    session(B,f'invalid command recovery {i}',line+b'\nshow 65\nquit\n',b'Try a command from help. Use decimal numbers from 0 to 255.\n'+show(65)+BYE)
session(B,'invalid quiz preserves pending question',b'quiz 1 1\nquiz 2 0\nanswer 1\nquit\n',b'AND gate: 1 AND 1 = ? Type answer 0 or answer 1.\nQuiz inputs are single bits: use only 0 or 1.\nCorrect! AND is 1 only when both inputs are 1.\n'+BYE)
session(B,'ASCII whitespace and leading decimal zeros',b'\t show\t065 \t\r\n\n\t\nquit\n',show(65)+BYE)
session(B,'63-byte line',b'show 65'+b' '*56+b'\nquit\n',show(65)+BYE)
session(B,'63-byte CRLF line',b'show 65'+b' '*56+b'\r\nquit\r\n',show(65)+BYE)
warning=b'That line is too long. Keep commands under 64 characters.\n'
session(B,'64-byte line recovery',b'show 65'+b' '*57+b'\nshow 42\nquit\n',warning+show(42)+BYE)
session(B,'4095-byte line drain recovery',b'x'*4095+b'\nshow 42\nquit\n',warning+show(42)+BYE)
session(B,'4096-byte nonnewline line ends session',b'x'*4096+b'\nshow 42\n',b'That line is too long. Session ended safely.\n',2)
session(B,'empty EOF',b'',BYE)
session(B,'final partial command EOF',b'show 65',show(65)+BYE)
session(B,'oversized partial EOF',b'x'*64,warning+BYE)
session(B,'session line limit',b'\n'*1024,b'Session limit reached. Start Number Lab again to keep learning.\n',2)
help_output=session(B,'help and exit',b'help\nquit\n');assert b'A byte is a number from 0 to 255.'in help_output
sample=b'show 0\nshow 32\nshow 39\nshow 127\nshow 255\nand 255 17\nquiz 1 1\nanswer 1\nguess 42\nquit\n'
observations=[]
for binary in binaries:
    q=run([binary],input=sample);assert q.returncode==0 and q.stderr==b'';observations.append(q.stdout)
assert len(set(observations))==1
ROWS.append({'case':'default/optimized and legacy/compact execution match','variants':4})
q=run([B,'unexpected'],input=b'quit\n');assert q.returncode==1 and b'no arguments are accepted'in q.stderr;ROWS.append({'case':'unexpected arguments refuse','exit':1})
q=run([B],preexec_fn=lambda:os.close(0));assert q.returncode==1 and q.stderr==b'Input could not be read.\n';ROWS.append({'case':'stdin read error reported','exit':1})
# Explicit native function cache must not change this real app image or behavior.
cache=D/'units';cache.mkdir(mode=0o700)
for label in ['first','warm']:
    out=D/('cache-'+label);q=run([C,SOURCE,out,'--opt','--compact','--reuse-cache',cache]);assert q.returncode==0,q.stderr
    oracle=D/('clean-'+label);q=run([C,SOURCE,oracle,'--opt','--compact']);assert q.returncode==0,q.stderr;assert out.read_bytes()==oracle.read_bytes()
    receipt=json.loads(Path(str(out)+'.reuse.json').read_text());assert receipt['reused']==0 if label=='first'else receipt['reused']>0
    subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True);q=run([out],input=sample);assert q.returncode==0 and q.stdout==observations[-1]
    ROWS.append({'case':'function cache '+label+' clean bytes and execution match','reuse':receipt})
report={'passed':True,'schema':'rf2.number.lab.verification.v1','cases':len(ROWS),'conversionValues':256,'complementValues':256,'binaryGateValues':288,'quizInputPairs':4,'rows':ROWS,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'controllerSHA256':CONTROLLER,'limits':'Local macOS ARM64 native CLI application. No graphical toolkit, education field study, cross-platform, network, hardware-acceleration, energy or token-saving claim.'}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'passed':True,'cases':len(ROWS)}))
