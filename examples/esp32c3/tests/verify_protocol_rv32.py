"""Execute the actual TMP102 protocol/formatter with scripted GPIO in ESP QEMU.

This substitutes GPIO hooks only. UART registers, RV32 compiled instructions and
ESP ROM/SPI boot are real emulator paths. Scripted temperatures are not sensor
observations, and nothing here establishes physical board or I2C timing support.
"""
from pathlib import Path
import hashlib,json,os,re,subprocess,time
R=Path(__file__).resolve().parents[3]
ROOT=Path(__file__).resolve().parents[1]
C=Path(os.environ.get('RF2_ESP_COMPILER',R/'artifacts/sprint-034/engine-build-v6/rf2-esp32c3')).resolve()
Q=Path(os.environ.get('RF2_ESP_QEMU',R/'artifacts/sprint-034/espressif-qemu/qemu/bin/qemu-system-riscv32')).resolve()
D=R/'artifacts/sprint-034'/('tmp102-rv32-model-'+str(time.time_ns()));D.mkdir(parents=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=(ROOT/'tmp102.flow').read_text()
assert hashlib.sha256(source.encode()).hexdigest()=='19dd66516deb46fe17b1ae8599f303486c9273db816aaf4ef0b25b7c4c76e333','production driver changed; re-review before testing'
protocol=source[source.index('fn bus_wait_scl()'):source.index('fn uart_byte(value)')]
uart=source[source.index('fn uart_byte(value)'):source.index('fn main()')]
board_main=source[source.index('fn main()'):].replace('fn main()','fn board_main()',1)
# Test-only DRAM, distinct from code alias3fc80000 and stack top3fcc0000.
# 0:SDA cursor,4:SCL reads,8:line events,12:SDA release,16:SCL release,
# 20:script exhaustion,24:script length,28:clock fault start,32:duration.
hooks='''fn bus_delay()
 return 0
end
fn bus_setup()
 return 0
end
fn bus_sda(high)
 do store32(0x3FCA000C,high)
 do store32(0x3FCA0008,load32(0x3FCA0008)+1)
 return 0
end
fn bus_scl(high)
 do store32(0x3FCA0010,high)
 do store32(0x3FCA0008,load32(0x3FCA0008)+1)
 return 0
end
fn bus_read_sda()
 let index=load32(0x3FCA0000)
 do store32(0x3FCA0000,index+1)
 if index>=load32(0x3FCA0018)
  do store32(0x3FCA0014,load32(0x3FCA0014)+1)
  return 1
 end
 return load8(0x3FCA0040+index)
end
fn bus_read_scl()
 let count=load32(0x3FCA0004)+1
 do store32(0x3FCA0004,count)
 let start=load32(0x3FCA001C)
 if start
  if count>=start
   if count-start<load32(0x3FCA0020)
    return 0
   end
  end
 end
 return 1
end
'''
def emit(text):return ''.join(' do uart_byte('+str(b)+')\n'for b in text.encode())
def bits(word):return[(word>>n)&1 for n in reversed(range(16))]
def register(word):return[1,0,0,1,0]+bits(word)+[1]
CASES=[dict(name='positive25C',samples=register(0x60a0)+register(0x1900),start=0,duration=0,status=0,sda=44,scl=96,text='TMP102 00001900 25.0000C\n'),dict(name='negative25C',samples=register(0x60a0)+register(0xe700),start=0,duration=0,status=0,sda=44,scl=96,text='TMP102 0000E700 -25.0000C\n'),dict(name='addressNACK',samples=[1,1,1],start=0,duration=0,status=0x80000001,sda=3,scl=11,text='TMP102 80000001\n'),dict(name='stuckSCL',samples=[],start=1,duration=10000,status=0x80000002,sda=0,scl=1000,text='TMP102 80000002\n')]
extended=os.environ.get('RF2_SENSOR_EXTENDED')=='1'
if extended:
 # Full signed-code boundaries test conversion, not physical measurement range.
 for raw,display in [(0,'0.0000'),(0x10,'0.0625'),(0xfff0,'-0.0625'),(0x7ff0,'127.9375'),(0x8000,'-128.0000'),(0x0640,'6.2500'),(0xf9c0,'-6.2500')]:
  CASES.append(dict(name='signedCode'+format(raw,'04X'),samples=register(0x60a0)+register(raw),start=0,duration=0,status=0,sda=44,scl=96,text=f'TMP102 {raw:08X} {display}C\n'))
 for config,raw,status in [(0x60b0,0x1900,0x80000006),(0x20a0,0x1900,0x80000006),(0x60a1,0x1900,0x80000005),(0x60a0,0x1901,0x80000005),(0x60a0,0xffff,0x80000005)]:
  CASES.append(dict(name=f'rejected_{config:04X}_{raw:04X}',samples=register(config)+register(raw),start=0,duration=0,status=status,sda=44,scl=96,text=f'TMP102 {status:08X}\n'))
 for poll in [1,48,96]:
  CASES.append(dict(name='stretch999At'+str(poll),samples=register(0x60a0)+register(0x1900),start=poll,duration=999,status=0,sda=44,scl=1095,text='TMP102 00001900 25.0000C\n'))
 CASES.append(dict(name='lastSTOPClockTimeout',samples=register(0x60a0)+register(0x1900),start=96,duration=10000,status=0x80000002,sda=43,scl=1095,text='TMP102 80000002\n'))
rows=[]
for case in CASES:
 name=case['name'];prefix=D/name;path=prefix.with_suffix('.flow')
 initialize=''.join(' do store32('+hex(0x3fca0000+offset)+',0)\n'for offset in range(0,36,4))
 initialize+=' do store32(0x3FCA000C,1)\n do store32(0x3FCA0010,1)\n'
 initialize+=' do store32(0x3FCA0018,'+str(len(case['samples']))+')\n do store32(0x3FCA001C,'+str(case['start'])+')\n do store32(0x3FCA0020,'+str(case['duration'])+')\n'
 initialize+=''.join(' do store8('+hex(0x3fca0040+i)+','+str(v)+')\n'for i,v in enumerate(case['samples']))
 main='fn main()\n'+initialize+' let result=board_main()\n'+emit('MODEL RETURN ')+' do uart_hex(result)\n'+emit(' SDA ')+' do uart_hex(load32(0x3FCA0000))\n'+emit(' SCL ')+' do uart_hex(load32(0x3FCA0004))\n'+emit(' RELEASE ')+' do uart_hex(load32(0x3FCA000C))\n do uart_hex(load32(0x3FCA0010))\n'+emit(' EXHAUST ')+' do uart_hex(load32(0x3FCA0014))\n'+emit('\n')+' return result\nend\n'
 path.write_text('profile RF2_ESP32C3_V1\n'+hooks+protocol+uart+board_main+main)
 q=subprocess.run([str(C),str(path),str(prefix)],capture_output=True,timeout=30)
 prefix.with_suffix('.compile.stdout').write_bytes(q.stdout);prefix.with_suffix('.compile.stderr').write_bytes(q.stderr)
 assert q.returncode==0,(name,q.returncode,q.stderr)
 image=prefix.with_suffix('.bin').read_bytes();assert len(image)<4*1024*1024
 flash=prefix.with_suffix('.flash.bin');flash.write_bytes(image+b'\xff'*(4*1024*1024-len(image)))
 uartlog=prefix.with_suffix('.uart.log');monitorlog=prefix.with_suffix('.monitor.log');stderrlog=prefix.with_suffix('.stderr.log')
 command=[str(Q),'-display','none','-monitor','stdio','-serial','file:'+str(uartlog),'-icount','3','-machine','esp32c3','-drive','file='+str(flash)+',if=mtd,format=raw','-nic','none']
 expected=f"MODEL RETURN {case['status']:08X} SDA {case['sda']:08X} SCL {case['scl']:08X} RELEASE 0000000100000001 EXHAUST 00000000\n".encode()
 p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  deadline=time.monotonic()+10
  while time.monotonic()<deadline:
   data=uartlog.read_bytes()if uartlog.exists()else b''
   if expected in data or p.poll()is not None:break
   time.sleep(.03)
  time.sleep(.03)
  stdout,stderr=p.communicate(b'stop\ninfo registers\nquit\n',timeout=3)
 finally:
  if p.poll()is None:p.kill();p.communicate(timeout=3)
 monitorlog.write_bytes(stdout);stderrlog.write_bytes(stderr)
 data=uartlog.read_bytes()if uartlog.exists()else b''
 assert p.returncode==0,(name,p.returncode,stderr)
 assert case['text'].encode()in data,(name,'application output mismatch',data)
 assert expected in data,(name,'status/count/release mismatch',data,expected)
 assert b'comparison failed'not in data and b'Checksum mismatch'not in data and b'Attempting to boot anyway'not in data,(name,'bad ROM image',data)
 registers=stdout.decode(errors='replace')
 def reg(pattern):
  match=re.search(pattern,registers);assert match,(name,pattern,registers);return int(match.group(1),16)
 a0=reg(r'x10/a0\s+([0-9a-f]+)');sp=reg(r'x2/sp\s+([0-9a-f]+)');pc=reg(r'\bpc\s+([0-9a-f]+)');mie=reg(r'\bmie\s+([0-9a-f]+)')
 assert a0==case['status']and sp==0x3fcc0000 and pc==0x40380018 and mie==0,(name,hex(a0),hex(sp),hex(pc),hex(mie))
 rows.append(dict(case=name,passed=True,suppliedFixture=True,sensorHardware=False,applicationOutput=case['text'].strip(),mainReturn=hex(a0),sdaSamples=case['sda'],sclSamples=case['scl'],scriptExhaustions=0,bothLinesReleased=True,stackRestored=True,returnedToEntry=True,interruptsDisabled=True,testSourceSHA256=sha(path),firmwareSHA256=sha(prefix.with_suffix('.bin')),flashSHA256=sha(flash),uartSHA256=sha(uartlog),monitorSHA256=sha(monitorlog)))
assert hashlib.sha256((ROOT/'tmp102.flow').read_bytes()).hexdigest()==hashlib.sha256(source.encode()).hexdigest(),'production source changed'
report=dict(schema='rf2.tmp102.rv32.scripted.protocol.v1',passed=True,cases=len(rows),rows=rows,compilerSHA256=sha(C),qemuSHA256=sha(Q),controllerSHA256=sha(__file__),driverSHA256=hashlib.sha256(source.encode()).hexdigest(),protocolSHA256=hashlib.sha256(protocol.encode()).hexdigest(),formattingAndUARTSHA256=hashlib.sha256(uart.encode()).hexdigest(),boardMainSHA256=hashlib.sha256(board_main.encode()).hexdigest(),scratchDRAM='0x3FCA0000..0x3FCA0100',protocolExtractUnchanged=True,boardMainOnlyNameChanged=True,scope='Actual unchanged protocol and formatting functions cross-compiled to RV32 and run through Espressif QEMU ROM/SPI boot. GPIO inputs are explicitly supplied fixtures, not a physical or emulated TMP102. Actual emulator UART MMIO and main return/count/release states verified. No physical sensor readings, calibrated I2C timing, throughput or board qualification.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),report=str(D/'report.json'))))
