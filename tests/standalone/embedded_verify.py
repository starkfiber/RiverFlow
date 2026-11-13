"""Independent native RF2 RV32IM/ESP32-C3 verifier.

GNU binutils and Espressif QEMU are developer oracles, never RF2 user runtime
requirements. No physical MCU, radio, USB, power or timing qualification follows.
"""
from pathlib import Path
import hashlib,json,os,random,re,struct,subprocess,time,traceback
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'artifacts/sprint-034/review'/('embedded-'+str(time.time_ns()))
DEST.mkdir(parents=True)
COMPILER=Path(os.environ.get('RF2_EMBEDDED_COMPILER',ROOT/'output/rf2-embedded')).resolve()
TOOLROOT=Path(os.environ.get('RF2_RISCV_TOOLS',ROOT/'artifacts/sprint-034/review/toolchain/riscv32-esp-elf/bin'))
QEMU=Path(os.environ.get('RF2_ESP_QEMU',ROOT/'artifacts/sprint-034/espressif-qemu/qemu/bin/qemu-system-riscv32'))
ROWS=[];SERIAL=0;MASK=0xffffffff
PROFILE='profile RF2_ESP32C3_V1\n'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def command(args,**kwargs):
 q=subprocess.run([str(x)for x in args],capture_output=True,timeout=kwargs.pop('timeout',30),**kwargs)
 assert q.returncode==0,(args,q.returncode,q.stdout.decode(errors='replace'),q.stderr.decode(errors='replace'))
 return q

def elf(data):
 assert data[:7]==b'\x7fELF\x01\x01\x01','ELF32 little-endian v1 required'
 fields=struct.unpack_from('<HHIIIIIHHHHHH',data,16)
 typ,machine,version,entry,phoff,shoff,flags,ehsz,phsz,phnum,shsz,shnum,shstr=fields
 assert typ==2 and machine==243 and version==1 and ehsz==52 and phsz==32
 assert phnum==1 and len(data)>=phoff+phsz
 pt,off,va,pa,fs,ms,pflags,align=struct.unpack_from('<IIIIIIII',data,phoff)
 assert pt==1 and fs==ms and fs%4==0 and off+fs==len(data)
 assert va==pa==entry==0x40380000 and pflags==5
 assert align and align&(align-1)==0 and off%align==va%align
 assert flags&~0x00==0,'only RV32IM soft-float without compressed instructions admitted'
 return dict(entry=entry,offset=off,size=fs,code=data[off:off+fs])

def image(data,expected):
 assert len(data)%16==0 and len(data)>=48 and data[0]==0xe9 and data[1]==1
 assert struct.unpack_from('<I',data,4)[0]==expected['entry']
 assert struct.unpack_from('<H',data,12)[0]==5,'ESP32-C3 chip ID must be 5'
 assert data[23] in [0,1],'unsupported image digest flag'
 digest_size=32 if data[23] else 0
 core=data[:-digest_size] if digest_size else data
 if digest_size:assert hashlib.sha256(core).digest()==data[-32:],'bad appended SHA-256'
 addr,size=struct.unpack_from('<II',data,24)
 assert addr==expected['entry'] and size==expected['size']
 assert data[32:32+size]==expected['code'],'ELF/image code differs'
 tail=core[32+size:];assert 1<=len(tail)<=16 and not any(tail[:-1])
 checksum=0xef
 for b in expected['code']:checksum^=b
 assert tail[-1]==checksum,('bad image checksum',tail[-1],checksum)
 return dict(chipID=5,segments=1,loadAddress=addr,payloadBytes=size,checksum=checksum,paddingBytes=len(tail)-1,hashAppended=bool(digest_size))

def signed(value,bits):return value-(1<<bits)if value&(1<<(bits-1))else value

def disassemble_word(word,pc):
 """Small independently written decoder; GNU assembler is the encoding oracle."""
 op=word&127;rd=(word>>7)&31;f3=(word>>12)&7;r1=(word>>15)&31;r2=(word>>20)&31;f7=word>>25
 reg=lambda r:'x'+str(r)
 if op==0x37:return 'lui '+reg(rd)+','+hex(word>>12)
 if op==0x17:return 'auipc '+reg(rd)+','+hex(word>>12)
 if op==0x13:
  if f3 in [0,2,3,4,6,7]:return ['addi','','slti','sltiu','xori','','ori','andi'][f3]+' '+reg(rd)+','+reg(r1)+','+str(signed(word>>20,12))
  if f3 in [1,5]and f7 in [0,32]:
   assert f3!=1 or f7==0
   return ('slli'if f3==1 else'srai'if f7==32 else'srli')+' '+reg(rd)+','+reg(r1)+','+str(r2)
 if op==0x33:
  table={(0,0):'add',(0,32):'sub',(0,1):'mul',(1,0):'sll',(2,0):'slt',(3,0):'sltu',(4,0):'xor',(4,1):'div',(5,0):'srl',(5,32):'sra',(5,1):'divu',(6,0):'or',(6,1):'rem',(7,0):'and',(7,1):'remu'}
  assert(f3,f7)in table,hex(word)
  return table[f3,f7]+' '+reg(rd)+','+reg(r1)+','+reg(r2)
 if op==0x03 and f3 in [0,1,2,4,5]:return {0:'lb',1:'lh',2:'lw',4:'lbu',5:'lhu'}[f3]+' '+reg(rd)+','+str(signed(word>>20,12))+'('+reg(r1)+')'
 if op==0x23 and f3 in [0,1,2]:
  imm=((word>>25)<<5)|((word>>7)&31)
  return {0:'sb',1:'sh',2:'sw'}[f3]+' '+reg(r2)+','+str(signed(imm,12))+'('+reg(r1)+')'
 if op==0x63 and f3 in [0,1,4,5,6,7]:
  delta=((word>>31)<<12)|(((word>>7)&1)<<11)|(((word>>25)&63)<<5)|(((word>>8)&15)<<1)
  return {0:'beq',1:'bne',4:'blt',5:'bge',6:'bltu',7:'bgeu'}[f3]+' '+reg(r1)+','+reg(r2)+',.+'+str(signed(delta,13))
 if op==0x6f:
  delta=((word>>31)<<20)|(((word>>12)&255)<<12)|(((word>>20)&1)<<11)|(((word>>21)&1023)<<1)
  return 'jal '+reg(rd)+',.+'+str(signed(delta,21))
 if op==0x67 and f3==0:return 'jalr '+reg(rd)+','+str(signed(word>>20,12))+'('+reg(r1)+')'
 if op==0x73 and f3 in [1,2,3,5,6,7]:
  return {1:'csrrw',2:'csrrs',3:'csrrc',5:'csrrwi',6:'csrrsi',7:'csrrci'}[f3]+' '+reg(rd)+','+hex(word>>20)+','+(str(r1)if f3>=5 else reg(r1))
 if word==0x00000073:return 'ecall'
 if word==0x00100073:return 'ebreak'
 if word==0x30200073:return 'mret'
 if op==0x0f and f3==0:return 'fence '+''.join(x for mask,x in [(8,'i'),(4,'o'),(2,'r'),(1,'w')]if(word>>24)&mask)+','+''.join(x for mask,x in [(8,'i'),(4,'o'),(2,'r'),(1,'w')]if(word>>20)&mask)
 raise AssertionError(('unknown emitted instruction',pc,hex(word)))

def encoding_oracle(code,prefix):
 asm=Path(str(prefix)+'.oracle.s');obj=Path(str(prefix)+'.oracle.o');raw=Path(str(prefix)+'.oracle.bin')
 lines=[disassemble_word(w,pc)for pc,(w,)in zip(range(0,len(code),4),struct.iter_unpack('<I',code))]
 asm.write_text('.option norvc\n.option norelax\n.text\n'+''.join(x+'\n'for x in lines))
 command([TOOLROOT/'riscv32-esp-elf-as','-march=rv32im_zicsr','-mabi=ilp32','-mno-relax',asm,'-o',obj])
 command([TOOLROOT/'riscv32-esp-elf-objcopy','-O','binary','-j','.text',obj,raw])
 actual=raw.read_bytes();assert actual==code,('independent assembler differs',len(code),len(actual),next((i for i,(a,b)in enumerate(zip(code,actual))if a!=b),None))
 dump=command([TOOLROOT/'riscv32-esp-elf-objdump','-d','-M','no-aliases,numeric',obj]);Path(str(prefix)+'.oracle.dis').write_bytes(dump.stdout)
 return dict(words=len(lines),oracle='official Espressif GNU assembler, RV32IM+Zicsr/ILP32/no relax',sourceSHA256=sha(asm),objectSHA256=sha(obj),matched=True)

def compile_source(name,text,refusal=False):
 global SERIAL
 SERIAL+=1;prefix=DEST/(f'{SERIAL:03}-'+name);source=Path(str(prefix)+'.flow');source.write_text(text)
 q=subprocess.run([str(COMPILER),str(source),str(prefix)],capture_output=True,timeout=20,env={'PATH':'/nonexistent'})
 Path(str(prefix)+'.stdout').write_bytes(q.stdout);Path(str(prefix)+'.stderr').write_bytes(q.stderr)
 if refusal:
  assert q.returncode!=0 and not any(Path(str(prefix)+suffix).exists()for suffix in ['.elf','.bin','.map']),(name,q.returncode,q.stdout,q.stderr)
  ROWS.append(dict(case=name,kind='source refusal',sourceSHA256=sha(source),stderr=q.stderr.decode(errors='replace')[:500]));return prefix
 assert q.returncode==0,(name,q.returncode,q.stdout,q.stderr)
 ep=Path(str(prefix)+'.elf');bp=Path(str(prefix)+'.bin');e=elf(ep.read_bytes());im=image(bp.read_bytes(),e);enc=encoding_oracle(e['code'],prefix)
 ROWS.append(dict(case=name,kind='compiled and independently encoded',sourceSHA256=sha(source),elfSHA256=sha(ep),imageSHA256=sha(bp),image=im,encoding=enc))
 return prefix

def uart(text):return ''.join(' do store8(0x60000000,'+str(c)+')\n'for c in text.encode())
def run_qemu(prefix,token,timeout=8):
 flash=Path(str(prefix)+'.flash.bin');image_bytes=Path(str(prefix)+'.bin').read_bytes();assert len(image_bytes)<4*1024*1024
 flash.write_bytes(image_bytes+b'\xff'*(4*1024*1024-len(image_bytes)))
 uartlog=Path(str(prefix)+'.qemu.uart.log');monitorlog=Path(str(prefix)+'.qemu.monitor.log')
 args=[str(QEMU),'-display','none','-monitor','stdio','-serial','file:'+str(uartlog),'-icount','3','-machine','esp32c3','-drive','file='+str(flash)+',if=mtd,format=raw','-nic','none']
 started=time.monotonic()
 with monitorlog.open('wb')as mon:
  p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=mon,stderr=subprocess.STDOUT)
  try:
   while time.monotonic()-started<timeout:
    data=uartlog.read_bytes()if uartlog.exists()else b''
    if token.encode()in data or b'RF2_FAIL'in data or p.poll()is not None:break
    time.sleep(.03)
   if p.poll()is None:
    p.communicate(b'stop\ninfo registers\nquit\n',timeout=2)
  finally:
   if p.poll()is None:p.terminate()
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
 data=uartlog.read_bytes()if uartlog.exists()else b''
 assert token.encode()in data and b'RF2_FAIL'not in data,('QEMU proof missing',prefix.name,data.decode(errors='replace'),monitorlog.read_text(errors='replace'))
 monitor=monitorlog.read_text(errors='replace')
 for pattern in [r'pc\s+40380018\b',r'x2/sp\s+3fcc0000\b',r'x10/a0\s+00000000\b',r'mie\s+00000000\b']:
  assert re.search(pattern,monitor),('returned machine state differs',pattern,monitor)
 assert b'Checksum mismatch' not in data and b'SHA-256 comparison failed' not in data
 ROWS.append(dict(returnedPC='0x40380018',restoredSP='0x3fcc0000',returnedA0=0,interruptsEnabled=False,case=prefix.name,kind='actual Espressif QEMU ESP32-C3 execution',token=token,flashSHA256=sha(flash),logSHA256=sha(uartlog),monitorSHA256=sha(monitorlog),qemuSHA256=sha(QEMU),hardware=False))

# The concrete source corpus is below; no compiler-specific output decoding is used as its result oracle.
def numeric_corpus():
 rng=random.Random(3401);ops=[('+',lambda a,b:(a+b)&MASK),('-',lambda a,b:(a-b)&MASK),('*',lambda a,b:(a*b)&MASK),('//',lambda a,b:MASK if b==0 else a//b),('%',lambda a,b:a if b==0 else a%b),('&',lambda a,b:a&b),('|',lambda a,b:a|b),('^',lambda a,b:a^b),('<<',lambda a,b:(a<<(b&31))&MASK),('>>',lambda a,b:a>>(b&31)),('<',lambda a,b:int(a<b)),('<=',lambda a,b:int(a<=b)),('>',lambda a,b:int(a>b)),('>=',lambda a,b:int(a>=b)),('==',lambda a,b:int(a==b)),('!=',lambda a,b:int(a!=b))]
 helpers='fn failed(n)\n'+uart('RF2_FAIL:numeric\n')+' return n\nend\n';body='';checks=0
 for idx,(op,fn)in enumerate(ops):
  helpers+='fn op'+str(idx)+'(a,b)\n return a'+op+'b\nend\n'
  pairs=[(0,0),(MASK,1),(0x80000000,31),(0x7fffffff,32),(0x80000001,33),(MASK,MASK)]+[(rng.getrandbits(32),rng.getrandbits(32))for _ in range(5)]
  for a,b in pairs:
   body+=' if op'+str(idx)+'('+str(a)+','+str(b)+')!='+str(fn(a,b))+'\n  return failed('+str(checks+1)+')\n end\n';checks+=1
 body+=uart('RF2_OK:numeric\n')+' return 0\n'
 return PROFILE+helpers+'fn main()\n'+body+'end\n',checks

def control_corpus():
 helpers='fn forward(a,b,c,d)\n return mix(a,b,c,d)\nend\nfn mix(a,b,c,d)\n return ((a*101+b)*103+c)*107+d\nend\n'
 helpers+='fn mark(a)\n do store32(0x3fcc4000,load32(0x3fcc4000)*10+a)\n return a\nend\n'
 body=' let i=0\n let total=0\n while i<100\n  if (i%3)==0\n   set total=total+i*7\n  else\n   set total=total+i\n  end\n  set i=i+1\n end\n'
 expected=sum(i*7 if i%3==0 else i for i in range(100))
 body+=' if total!='+str(expected)+'\n'+uart('RF2_FAIL:loop\n')+'  return 1\n end\n'
 body+=' do store32(0x3fcc4000,0)\n let packed=forward(mark(1),mark(2),mark(3),mark(4))\n if (packed!='+str(((1*101+2)*103+3)*107+4)+')|(load32(0x3fcc4000)!=1234)\n'+uart('RF2_FAIL:call-order\n')+'  return 2\n end\n'
 body+=' do store32(0x3fcc4010,0x89abcdef)\n if (load8(0x3fcc4010)!=0xef)|(load8(0x3fcc4011)!=0xcd)|(load32(0x3fcc4010)!=0x89abcdef)\n'+uart('RF2_FAIL:memory\n')+' return 3\n end\n do store8(0x3fcc4011,0x12)\n if load32(0x3fcc4010)!=0x89ab12ef\n'+uart('RF2_FAIL:byte-store\n')+' return 4\n end\n'
 body+=uart('RF2_OK:control\n')+' return 0\n'
 return PROFILE+helpers+'fn main()\n'+body+'end\n'

def frame_corpus():
 # Four parameters plus sixty named local words occupy the whole admitted frame.
 helpers='';depth=8;expected=0
 for level in reversed(range(depth)):
  helpers+='fn frame'+str(level)+'(a,b,c,d)\n'
  for i in range(60):helpers+=' let l'+str(i)+'=a+'+str(i+level)+'\n'
  # Call first; all named caller locals must remain intact afterwards.
  expression=('frame'+str(level+1)+'(a,b,c,d)+'if level+1<depth else'')+'+'.join('l'+str(i)for i in range(60))+'+b+c+d'
  helpers+=' return '+expression+'\nend\n'
  expected=(expected+sum(17+i+level for i in range(60))+3+5+7)&MASK
 body=' let value=frame0(17,3,5,7)\n if value!='+str(expected)+'\n'+uart('RF2_FAIL:frames\n')+'  return 1\n end\n'+uart('RF2_OK:frames\n')+' return 0\n'
 return PROFILE+helpers+'fn main()\n'+body+'end\n'

def refusals():
 bad=[('wrong-profile','profile RF2_SYSTEM_A64_V1\nfn main()\n return 0\nend\n'),('decimal-overflow',PROFILE+'fn main()\n return 4294967296\nend\n'),('hex-overflow',PROFILE+'fn main()\n return 0x100000000\nend\n'),('unknown-call',PROFILE+'fn main()\n return missing(1)\nend\n'),('direct-recursion',PROFILE+'fn main()\n return main()\nend\n'),('mutual-recursion',PROFILE+'fn first()\n return second()\nend\nfn second()\n return first()\nend\nfn main()\n return first()\nend\n'),('duplicate-function',PROFILE+'fn dup()\n return 1\nend\nfn dup()\n return 2\nend\nfn main()\n return dup()\nend\n'),('wrong-call-arity',PROFILE+'fn f(a,b)\n return a+b\nend\nfn main()\n return f(1)\nend\n'),('too-many-parameters',PROFILE+'fn f(a,b,c,d,e)\n return a\nend\nfn main()\n return 0\nend\n'),('unknown-local',PROFILE+'fn main()\n return absent\nend\n'),('host-syscall',PROFILE+'fn main()\n return syscall6(1,0,0,0,0,0,0)\nend\n'),('float-not-admitted',PROFILE+'fn main()\n return 1.5\nend\n'),('string-not-admitted',PROFILE+'fn main()\n return "hello"\nend\n'),('too-many-locals',PROFILE+'fn main()\n'+''.join(' let v'+str(i)+'='+str(i)+'\n'for i in range(65))+' return 0\nend\n')]
 bad += [('lifetime-after-branch',PROFILE+'fn main()\n if 1\n  let secret=9\n end\n return secret\nend\n'),('self-initialization',PROFILE+'fn main()\n let value=value+1\n return value\nend\n'),('reserved-mmio-redefinition',PROFILE+'fn store8(a,b)\n return 0\nend\nfn main()\n return 0\nend\n'),('missing-main',PROFILE+'fn other()\n return 0\nend\n'),('main-parameters',PROFILE+'fn main(a)\n return a\nend\n'),('missing-root-return',PROFILE+'fn main()\n if 1\n  return 0\n end\nend\n'),('unsupported-host-effect',PROFILE+'fn main()\n return syscall6(0)\nend\n')]
 chain=PROFILE+''.join('fn depth'+str(i)+'()\n return '+('depth'+str(i+1)+'()'if i<15 else'0')+'\nend\n'for i in range(16))+'fn main()\n return depth0()\nend\n'
 bad.append(('call-depth17',chain))
 for name,source in bad:compile_source(name,source,True)

def output_safety():
 source=PROFILE+'fn main()\n return 0\nend\n'
 for existing in ['.elf','.bin','.map']:
  prefix=DEST/('occupied'+existing);src=Path(str(prefix)+'.flow');src.write_text(source);occupied=Path(str(prefix)+existing);occupied.write_bytes(b'KEEP ORIGINAL')
  q=subprocess.run([str(COMPILER),str(src),str(prefix)],capture_output=True,timeout=10)
  assert q.returncode!=0 and occupied.read_bytes()==b'KEEP ORIGINAL'
  assert all(not Path(str(prefix)+suffix).exists()for suffix in ['.elf','.bin','.map']if suffix!=existing)
  ROWS.append(dict(case='existing-output'+existing,kind='publication refusal',preserved=True,noPartialOutputs=True))
 target=DEST/'symlink-original';target.write_bytes(b'KEEP SYMLINK TARGET');prefix=DEST/'symlink-output';src=Path(str(prefix)+'.flow');src.write_text(source);Path(str(prefix)+'.bin').symlink_to(target)
 q=subprocess.run([str(COMPILER),str(src),str(prefix)],capture_output=True,timeout=10)
 assert q.returncode!=0 and target.read_bytes()==b'KEEP SYMLINK TARGET'and Path(str(prefix)+'.bin').is_symlink()
 assert not Path(str(prefix)+'.elf').exists()and not Path(str(prefix)+'.map').exists()
 ROWS.append(dict(case='existing-symlink-image',kind='publication refusal',targetPreserved=True,noPartialOutputs=True))



def main():
 assert COMPILER.is_file() and QEMU.is_file() and (TOOLROOT/'riscv32-esp-elf-as').is_file()
 csha=sha(COMPILER)
 smoke=compile_source('uart-smoke',PROFILE+'fn main()\n'+uart('RF2_OK:smoke\n')+' return 0\nend\n');run_qemu(smoke,'RF2_OK:smoke')
 numeric,count=numeric_corpus();p=compile_source('numeric-corpus',numeric);run_qemu(p,'RF2_OK:numeric');ROWS[-1]['assertions']=count
 p=compile_source('control-memory-calls',control_corpus());run_qemu(p,'RF2_OK:control')
 p=compile_source('full-call-frames',frame_corpus());run_qemu(p,'RF2_OK:frames')
 refusals()
 output_safety()
 report=dict(passed=True,rows=ROWS,compilerSHA256=csha,compilerUnchanged=sha(COMPILER)==csha,controllerSHA256=sha(__file__),scope='Finite native RF2 cross-compilation plus independent GNU assembler and Espressif QEMU execution. No physical-board, Arduino, Xtensa, RF, power or speed claim.')
 assert report['compilerUnchanged']
 (DEST/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'rows':len(ROWS),'report':str(DEST/'report.json')}))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  (DEST/'failure.json').write_text(json.dumps({'passed':False,'error':repr(exc),'traceback':traceback.format_exc(),'rows':ROWS},indent=2)+'\n');raise
