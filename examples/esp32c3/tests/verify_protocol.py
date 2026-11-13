"""Run actual unchanged RF2 protocol functions against test-only scripted GPIO.

The GPIO model is an explicitly supplied transcript, not an ESP32 or TMP102
measurement. A separately written Python wire-operation oracle compares complete
line traces, fault statuses and bounded sample counts. Host execution verifies
protocol logic only; the RISC-V backend has its own emulator qualification.
"""
from pathlib import Path
import hashlib,json,os,struct,subprocess,time
R=Path(__file__).resolve().parents[3]
ROOT=Path(__file__).resolve().parents[1]
C=Path(os.environ.get('RF2_TEST_COMPILER',str(R/'output/rf2c-033-heap-v4'))).resolve()
D=R/'artifacts/sprint-034'/('tmp102-model-'+str(time.time_ns()));D.mkdir(parents=True)
source=(ROOT/'tmp102.flow').read_text()
protocol=source[source.index('fn bus_wait_scl()'):source.index('fn uart_byte(value)')]
uart_and_main=source[source.index('fn uart_hex(value)'):].replace('fn main()','fn board_main()',1)
hooks=(ROOT/'tests/model-hooks.flow').read_text();main=(ROOT/'tests/model-main.flow').read_text()
model=D/'actual-protocol.flow';model.write_text('profile RF2_SYSTEM_A64_V1\n'+hooks+'\n'+protocol+'\n'+uart_and_main+'\n'+main)
NACK=0x80000001;CLOCK=0x80000002;STUCK=0x80000003;ARG=0x80000004;MALFORMED=0x80000005;MODE=0x80000006
class Wire:
 def __init__(self,samples,start=0,duration=0):self.samples=samples;self.start=start;self.duration=duration;self.i=0;self.clock=0;self.events=[];self.sda=1;self.scl=1;self.exhausted=0
 def data(self,v):self.sda=v;self.events.append(256+v)
 def clk(self,v):self.scl=v;self.events.append(512+v)
 def read(self):
  n=self.i;self.i+=1
  if n>=len(self.samples):self.exhausted+=1;return 1
  return self.samples[n]
 def high(self):
  for _ in range(1000):
   self.clock+=1
   if not(self.start and self.start<=self.clock<self.start+self.duration):return 0
  return CLOCK
 def release(self):self.data(1);self.clk(1)
 def begin(self):
  self.release();e=self.high()
  if e:return e
  if not self.read():return STUCK
  self.data(0);self.clk(0);return 0
 def stop(self):
  self.clk(0);self.data(0);self.clk(1);e=self.high();self.data(1)
  if e:return e
  return 0 if self.read() else STUCK
 def send(self,v):
  if v>255:self.release();return ARG
  for shift in reversed(range(8)):
   self.data((v>>shift)&1);self.clk(1);e=self.high()
   if e:self.release();return e
   self.clk(0)
  self.data(1);self.clk(1);e=self.high()
  if e:self.release();return e
  nack=self.read();self.clk(0)
  if nack:self.release();return NACK
  return 0
 def receive(self,ack):
  if ack>1:self.release();return ARG
  self.data(1);v=0
  for _ in range(8):
   self.clk(1);e=self.high()
   if e:self.release();return e
   v=(v<<1)|self.read();self.clk(0)
  self.data(1-ack);self.clk(1);e=self.high()
  if e:self.release();return e
  self.clk(0);self.data(1);return v
 def register(self,reg):
  if reg>1:self.release();return ARG
  e=self.begin()
  if e:self.release();return e
  high=low=0
  for op in [lambda:self.send(0x90),lambda:self.send(reg),self.begin,lambda:self.send(0x91)]:
   if not e:e=op()
  if not e:
   high=self.receive(1)
   if high&0x80000000:e=high
  if not e:
   low=self.receive(0)
   if low&0x80000000:e=low
  stopped=self.stop()
  return e or stopped or ((high<<8)|low)
 @staticmethod
 def validate(config,raw):
  if config>65535 or raw>65535:return ARG
  if config&0x6000!=0x6000 or config&0x10:return MODE
  if config&15 or raw&15:return MALFORMED
  return raw
 def temperature(self):
  c=self.register(1)
  if c&0x80000000:return c
  r=self.register(0)
  if r&0x80000000:return r
  return self.validate(c,r)
def temperature_text(raw):
 code=raw>>4
 if code&2048:code-=4096
 magnitude=abs(code)
 return ('-'if code<0 else'')+str(magnitude//16)+'.'+f'{(magnitude&15)*625:04d}'+'C'
def bits(word):return[(word>>n)&1 for n in reversed(range(16))]
def transaction(word):return[1,0,0,1,0]+bits(word)+[1]
def fixture(config=0x60a0,raw=0x1900):return transaction(config)+transaction(raw)
CASES=[]
def add(name,samples=None,start=0,duration=0,entry=1,a=0,b=0,required=None):CASES.append((name,fixture()if samples is None else samples,start,duration,entry,a,b,required))
for raw in [0,0x0010,0x1900,0xf600,0x7ff0,0x8000,0xfff0]:add('valid wire word '+hex(raw),fixture(raw=raw),required=raw)
for i in range(2):
 for j,name in [(1,'write address'),(2,'register pointer'),(4,'read address')]:
  index=i*22+j;add('NACK '+str(i)+' '+name,fixture()[:index]+[1,1],required=NACK)
for reg in [0,1]:
 add('SDA stuck before start '+str(reg),fixture()[:reg*22]+[0],required=STUCK)
 add('SDA stuck before repeated start '+str(reg),fixture()[:reg*22+3]+[0,1],required=STUCK)
for i in range(1,97):add('permanent clock fault at poll '+str(i),start=i,duration=10000,required=CLOCK)
for i in [1,2,10,20,48,49,70,95,96]:
 for duration in [1,99,999]:add('recoverable clock stretch '+str((i,duration)),start=i,duration=duration,required=0x1900)
for length in range(44):add('truncated scripted SDA stream '+str(length),fixture()[:length])
for raw in [1,0x1901,0xffff]:add('malformed temperature bits '+hex(raw),fixture(raw=raw),required=MALFORMED)
for config in [0x60a1,0x60af]:add('malformed reserved config '+hex(config),fixture(config=config),required=MALFORMED)
for config in [0,0x20a0,0x40a0,0x60b0]:add('unsupported config '+hex(config),fixture(config=config),required=MODE)
add('STOP observes stuck SDA',fixture()[:21]+[0],required=STUCK)
add('primary NACK survives STOP failure',[1,1,0],required=NACK)
for value in [256,0xffffffff]:add('write value refuses '+str(value),[],entry=2,a=value,required=ARG)
for value in [2,0xffffffff]:add('read ACK argument refuses '+str(value),[],entry=5,a=value,required=ARG)
for value in [2,0xffffffff]:add('register argument refuses '+str(value),[],entry=4,a=value,required=ARG)
for c,r in [(0x60a0,0x1900),(65536,0),(0x60a0,65536),(0x60a0,0xfff0),(0x60b0,0),(0x60a1,0)]:add('pure validation '+str((c,r)),[],entry=3,a=c,b=r)
# Byte-level boundaries, transmitted bits and ninth ACK/NACK clock have complete trace checks.
for value in [0,1,0x48,0x90,0x91,0xff]:add('transmitted byte '+hex(value),[0],entry=2,a=value,required=0)
for ack in [0,1]:
 for value in [0,1,0x80,0xff]:add('received byte/ACK '+str((value,ack)),[(value>>i)&1 for i in reversed(range(8))],entry=5,a=ack,required=value)
for raw in [0,0x0010,0x1900,0xf600,0x7ff0,0x8000,0xfff0]:add('board main exact Celsius '+hex(raw),fixture(raw=raw),entry=6,required=0)
add('board main preserves sensor NACK',[1,1,1],entry=6,required=NACK)
add('board main preserves sensor timeout',start=1,duration=10000,entry=6,required=CLOCK)
add('board main UART failure after valid sensor',entry=6,a=1,required=1)
add('board main sensor failure beats UART failure',[1,1,1],entry=6,a=1,required=NACK)
rows=[];images=[]
for optimize in [False,True]:
 binary=D/('model-opt'if optimize else'model-default')
 q=subprocess.run([str(C),str(model),str(binary),'--compact',*(['--opt']if optimize else[])],capture_output=True,timeout=60);assert q.returncode==0,q.stderr
 q=subprocess.run(['/usr/bin/codesign','-s','-',str(binary)],capture_output=True);assert q.returncode==0,q.stderr
 images.append(dict(path=str(binary.relative_to(R)),sha256=hashlib.sha256(binary.read_bytes()).hexdigest()))
 for name,samples,start,duration,entry,a,b,required in CASES:
  wire=Wire(samples,start,duration)
  result={1:wire.temperature,2:lambda:wire.send(a),3:lambda:wire.validate(a,b),4:lambda:wire.register(a),5:lambda:wire.receive(a),6:wire.temperature}[entry]()
  uart=b''
  if entry==6:
   sensor=result
   if not a:
    uart=(f"TMP102 {sensor:08X}"+(''if sensor&0x80000000 else ' '+temperature_text(sensor))+"\n").encode()
   result=sensor if sensor&0x80000000 else (1 if a else 0)
   wire.release()
  if required is not None:assert result==required,(name,result,required)
  if entry in [1,6]:
   assert wire.sda==1 and wire.scl==1,(name,'bus not released')
   assert wire.clock<=2096,(name,'clock polling bound exceeded')
  if 'truncated' in name and len(samples)<43:assert result&0x80000000,(name,result)
  payload=struct.pack('<6Q',len(samples),start,duration,entry,a,b)+bytes(samples)
  q=subprocess.run([str(binary)],input=payload,capture_output=True,timeout=3);assert q.returncode==0,(name,q.returncode,q.stderr)
  expected=(result,wire.i,wire.clock,len(wire.events),wire.sda,wire.scl,wire.exhausted,0,len(uart))
  assert len(q.stdout)>=72,(name,q.stdout)
  actual=struct.unpack('<9Q',q.stdout[:72]);assert actual==expected,(name,optimize,actual,expected)
  actual_events=list(struct.unpack('<'+str(actual[3])+'Q',q.stdout[72:72+actual[3]*8]));assert actual_events==wire.events,(name,optimize,'wire trace mismatch')
  assert q.stdout[72+actual[3]*8:]==uart,(name,optimize,q.stdout[72+actual[3]*8:],uart)
  rows.append(dict(name=name,optimized=optimize,result=hex(result),sdaReads=wire.i,sclReads=wire.clock,lineEvents=len(wire.events),scriptExhaustions=wire.exhausted,uart=uart.decode()))
report=dict(schema='rf2.tmp102.scripted.protocol.v1',passed=True,cases=len(rows),rows=rows,images=images,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),driverSHA256=hashlib.sha256(source.encode()).hexdigest(),extractedProtocolSHA256=hashlib.sha256(protocol.encode()).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual unchanged protocol functions compiled and run on Apple Silicon with substituted GPIO fixtures. No physical TMP102, calibrated I2C timing, ESP32 backend execution or temperature observation is established. Truncated fixture streams return high and record exhaustion; physical SDA disconnection cannot in general be distinguished from a legitimate all-high sample without additional protocol/device checks.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),report=str(D/'report.json'))))
