"""Actual ESP32-C3 QEMU ROM boot and UART TX/RX; never physical hardware."""
from pathlib import Path
import os,subprocess,hashlib,json,time,tempfile,socket,re
R=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_ESP_COMPILER']).resolve()
Q=Path(os.environ['RF2_ESP_QEMU']).resolve()
D=R/'artifacts/sprint-034'/('uart-verify-'+str(time.time_ns()));D.mkdir(parents=True)
source=R/'examples/esp32c3/uart-echo.flow';prefix=D/'echo'
subprocess.run([C,source,prefix],capture_output=True,check=True,timeout=20)
image=prefix.with_suffix('.bin').read_bytes();flash=D/'flash.bin';flash.write_bytes(image+b'\xff'*(4*1024*1024-len(image)))
rows=[]
for value in [0,90,255,None]:
 label='timeout'if value is None else str(value)
 with tempfile.TemporaryDirectory(prefix='rf2-uart-',dir='/tmp')as td:
  endpoint=Path(td)/'serial.sock'
  command=[Q,'-display','none','-monitor','stdio','-S','-chardev','socket,id=uart,path='+str(endpoint)+',server=on,wait=off','-serial','chardev:uart','-icount','3','-machine','esp32c3','-drive','file='+str(flash)+',if=mtd,format=raw','-nic','none']
  p=subprocess.Popen(list(map(str,command)),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(10);raw=b''
  try:
   deadline=time.monotonic()+10
   while not endpoint.exists():
    assert p.poll()is None,'QEMU exited before UART socket';assert time.monotonic()<deadline,'UART socket startup timeout';time.sleep(.02)
   s.connect(str(endpoint));p.stdin.write(b'cont\n');p.stdin.flush()
   while b'READY\n'not in raw:
    chunk=s.recv(4096);assert chunk,'UART closed before READY';raw+=chunk;assert len(raw)<65536
   if value is not None:s.sendall(bytes([value]))
   expected=b'ERR\n'if value is None else b'RX '+bytes([value])+b'\n'
   while expected not in raw:
    chunk=s.recv(4096);assert chunk,'UART closed before result';raw+=chunk;assert len(raw)<65536
   # Stop only after the result. The monitor verifies return, stack and interrupt state.
   time.sleep(.02)
   monitor,stderr=p.communicate(b'stop\ninfo registers\nquit\n',timeout=5)
  finally:
   s.close()
   if p.poll()is None:p.kill();p.communicate(timeout=5)
  assert p.returncode==0,(label,stderr)
  assert b'comparison failed'not in raw and b'Attempting to boot anyway'not in raw,raw
  regs=monitor.decode(errors='replace')
  a0=int(re.search(r'x10/a0\s+([0-9a-f]+)',regs).group(1),16)
  sp=int(re.search(r'x2/sp\s+([0-9a-f]+)',regs).group(1),16)
  pc=int(re.search(r'\bpc\s+([0-9a-f]+)',regs).group(1),16)
  assert a0==(0x80000001 if value is None else 0),(label,hex(a0))
  assert sp==0x3fcc0000 and pc==0x40380018,(label,hex(sp),hex(pc))
  (D/(label+'.uart')).write_bytes(raw);(D/(label+'.monitor')).write_bytes(monitor);(D/(label+'.stderr')).write_bytes(stderr)
  rows.append(dict(case=label,receivedByte=value,expectedReturn=a0,stackRestored=True,returnedToEntryLoop=True,uartSHA256=hashlib.sha256(raw).hexdigest(),passed=True))
report=dict(schema='rf2.esp32c3.uart.v1',passed=True,compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),qemuSHA256=hashlib.sha256(Q.read_bytes()).hexdigest(),sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),firmwareSHA256=hashlib.sha256(image).hexdigest(),controllerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,scope='Actual vendor QEMU ROM/SPI boot and UART model with Unix-socket supplied bytes, including 0/90/255 and bounded no-input timeout. No physical board, UART wiring, calibrated baud, sensor or throughput claim.')
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(D/'report.json'),cases=len(rows))))
