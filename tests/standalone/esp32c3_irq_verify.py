"""ESP32-C3 interrupt ABI and checked lease tests, no physical devices.

Vendor QEMU and GNU binutils are independent development oracles. Explicit
binary/hook fault controls never count as physical hardware observations.
"""
from pathlib import Path
import hashlib, importlib.util, json, os, re, shutil, struct, subprocess, time, traceback
ROOT=Path(__file__).resolve().parents[2]
C=Path(os.environ['RF2_ESP_COMPILER']).resolve()
Q=Path(os.environ['RF2_ESP_QEMU']).resolve()
D=ROOT/'artifacts/sprint-036'/('irq-verify-'+str(time.time_ns()));D.mkdir(parents=True)
LIB=ROOT/'examples/esp32c3/lib'
B=Path(os.environ.get('RF2_RISCV_TOOLS',str(ROOT/'artifacts/sprint-034/review/toolchain/riscv32-esp-elf/bin')))
spec=importlib.util.spec_from_file_location('rv_oracle',ROOT/'tests/standalone/embedded_verify.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle);oracle.TOOLROOT=B
ROWS=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def emit(t):return ''.join(f' do serial_byte({b})\n'for b in t.encode())
def invoke(args):
 q=subprocess.run(list(map(str,args)),capture_output=True,timeout=30);assert q.returncode==0,(args,q.returncode,q.stderr);return q

def image_mutate(prefix,offset,payload):
 elf=prefix.with_suffix('.elf').read_bytes();e=oracle.elf(elf);code=bytearray(e['code']);assert offset+len(payload)<=len(code)
 code[offset:offset+len(payload)]=payload
 image=bytearray(prefix.with_suffix('.bin').read_bytes());image[32:32+len(code)]=code
 checksum=0xef
 for b in code:checksum^=b
 image[-33]=checksum;image[-32:]=hashlib.sha256(image[:-32]).digest();prefix.with_suffix('.bin').write_bytes(image)
 changed=bytearray(elf);changed[e['offset']:]=code;prefix.with_suffix('.elf').write_bytes(changed)
 oracle.image(bytes(image),oracle.elf(bytes(changed)))


def compile_case(name,body,handler='return owned_timer_interrupt(cause)',extra='',hook=None,binary_patch=None):
 folder=D/name;folder.mkdir();shutil.copytree(LIB,folder/'lib')
 if hook:
  p=folder/'lib/peripheral.flow';s=p.read_text().replace('load32(','fault_read32(');s+='''\nfn fault_read32(address)
 if (address==0x600C2104)&(load32(0x3FCA8340)!=0)
  return load32(address)|2
 end
 return load32(address)
end
''';p.write_text(s)
 text='profile RF2_ESP32C3_V1\n'+''.join('use "lib/'+n+'.flow"\n'for n in ['time','watchdog','uart','peripheral'])
 text+=('interrupt fn dispatch(cause)\n '+handler+'\nend\n'if handler is not None else '')+extra+'fn test()\n'+body+'\nend\nfn main()\n'+emit('BOOT ')+' do serial_hex(reset_cause())\n do serial_byte(10)\n let result=test()\n let saved=irq_save()\n'+emit('RESULT ')+' do serial_hex(result)\n do serial_byte(10)\n return result\nend\n'
 source=folder/'main.flow';source.write_text(text);prefix=folder/'firmware';invoke([C,source,prefix])
 if binary_patch:
  offsets={line.split()[0]:int(line.split()[1])for line in prefix.with_suffix('.map').read_text().splitlines()[3:]}
  binary_patch(prefix,offsets)
 e=oracle.elf(prefix.with_suffix('.elf').read_bytes());oracle.image(prefix.with_suffix('.bin').read_bytes(),e)
 enc=oracle.encoding_oracle(e['code'],prefix)
 return prefix,dict(sourceSHA256=sha(source),firmwareSHA256=sha(prefix.with_suffix('.bin')),encodingWords=enc['words'],binaryFaultInjection=bool(binary_patch),testHook=bool(hook))


def run_image(prefix,done=b'RESULT ',shift=6,fault=None,resets=None,timeout=20,application=False):
 image=prefix.with_suffix('.bin').read_bytes();flash=prefix.with_suffix('.flash.bin');flash.write_bytes(image+b'\xff'*(4*1024*1024-len(image)))
 uart=prefix.with_suffix('.uart');dump=prefix.with_suffix('.runtime.bin');canary=prefix.with_suffix('.canary.bin')
 args=[Q,'-display','none','-monitor','stdio','-serial','file:'+str(uart),'-icount',str(shift),'-machine','esp32c3','-drive','file='+str(flash)+',if=mtd,format=raw','-nic','none']
 p=subprocess.Popen(list(map(str,args)),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out=err=b''
 try:
  deadline=time.monotonic()+timeout;start=time.monotonic();satisfied=False
  while time.monotonic()<deadline:
   data=uart.read_bytes()if uart.exists()else b'';assert len(data)<1024*1024,'UART output budget exceeded'
   satisfied=(time.monotonic()-start>.15)if fault is not None else data.count(b'BOOT ')>=3 if resets is not None else done in data
   if satisfied or p.poll()is not None:break
   time.sleep(.005)
  time.sleep(.01)
  command='stop\ninfo registers\npmemsave 0x3fca8100 0x300 '+json.dumps(str(dump))+'\npmemsave 0x3fcbc000 0x40 '+json.dumps(str(canary))+'\nquit\n'
  out,err=p.communicate(command.encode(),timeout=5)
 finally:
  if p.poll()is None:p.kill();out,err=p.communicate(timeout=5)
  prefix.with_suffix('.monitor').write_bytes(out);prefix.with_suffix('.stderr').write_bytes(err)
 assert p.returncode==0,err
 assert satisfied,('observation deadline; monitor and memory retained',data[-1000:])
 data=uart.read_bytes();assert b'comparison failed'not in data and b'Checksum mismatch'not in data,data
 regs=out.decode(errors='replace')
 def reg(n):
  m=re.search(n+r'\s+([0-9a-f]+)',regs);assert m,(n,regs);return int(m.group(1),16)
 state=dict(pc=reg(r'\bpc'),sp=reg(r'x2/sp'),a0=reg(r'x10/a0'),mie=reg(r'\bmie'),mstatus=reg(r'\bmstatus'),mscratch=reg(r'\bmscratch'))
 words=struct.unpack('<192I',dump.read_bytes());state['runtime']=list(words[:8]);state['leases']=list(words[64:70])
 if resets is not None:
  causes=[int(x,16)for x in re.findall(rb'BOOT ([0-9A-F]{8})',data)];assert causes[:3]==[1,resets,resets],(causes,data);assert b'RESULT 'not in data,data;state['resetCauses']=causes[:3]
 elif fault is not None:
  assert words[1]==fault,(hex(fault),state,data)
  if fault==0x80000404:assert words[0]==0 and words[6]==64,state
  if fault==0x80000405:assert state['sp']==0 and words[7]==1,state
  assert state['mstatus']&8==0 and state['mie']==0,state
  assert b'RESULT 'not in data,data
 else:
  value=0 if application else int(re.search(rb'RESULT ([0-9A-F]{8})',data).group(1),16)
  assert value==0 and state['a0']==0 and state['sp']==0x3fcc0000 and state['pc']==0x40380018,state
  assert state['mstatus']&8==0 and state['mie'] in [0,2048],state
  assert data.count(b'entry ')==1,data
 return state,data

INIT=' let status=irq_install(dispatch)\n if status\n  return status\n end\n do watchdog_disarm()\n do timer_init()\n'
START=INIT+' let timer=peripheral_claim(1)\n if timer&0x80000000\n  return timer\n end\n set status=owned_timer_start(timer,1000)\n if status\n  return status\n end\n'
def run(name,body,**opts):
 runtime={k:opts.pop(k)for k in list(opts)if k in ['fault','resets','shift']}
 prefix,meta=compile_case(name,body,**opts);state,data=run_image(prefix,**runtime)
 ROWS.append(dict(name=name,passed=True,**meta,state=state,uartSHA256=sha(prefix.with_suffix('.uart'))));print(json.dumps(dict(case=name,passed=True)),flush=True)


def register_patch(prefix,offsets):
 asm=prefix.with_suffix('.registers.s');obj=prefix.with_suffix('.registers.o');raw=prefix.with_suffix('.registers.bin')
 lines=['.option norvc','.option norelax','.text','addi sp,sp,-128']
 for r in range(1,32):
  if r!=2:lines.append(f'sw x{r},{r*4}(sp)')
 for r in range(1,32):
  if r not in [2,5]:lines.append(f'li x{r},{(0x81230000+r*0x10203)&0xffffffff}')
 lines+=['li x5,100000','loop: addi x5,x5,-1','bne x5,x0,loop']
 for r in range(1,32):
  if r not in [2,5]:lines += [f'li x5,{(0x81230000+r*0x10203)&0xffffffff}',f'bne x{r},x5,bad']
 lines+=['li a0,0','j restore','bad: li a0,1','restore:']
 for r in range(1,32):
  if r not in [2,10]:lines.append(f'lw x{r},{r*4}(sp)')
 lines+=['addi sp,sp,128','ret'];asm.write_text('\n'.join(lines)+'\n')
 invoke([B/'riscv32-esp-elf-as','-march=rv32im_zicsr','-mabi=ilp32',asm,'-o',obj]);invoke([B/'riscv32-esp-elf-objcopy','-O','binary','-j','.text',obj,raw])
 payload=raw.read_bytes();assert len(payload)<offsets['test']-offsets['register_probe']
 image_mutate(prefix,offsets['register_probe'],payload)

try:
 run('interrupt-delivery-and-release',START+' do irq_enable()\n do timer_delay_us(20000,100000)\n let saved=irq_save()\n let count=owned_timer_ticks(timer)\n if count<10\n  return 1\n end\n do peripheral_release(timer)\n do timer_delay_us(5000,100000)\n return load32(0x3FCA8300)!=count\n')
 run('restore-disabled-state',START+' do irq_enable()\n do irq_restore(0)\n do timer_delay_us(10000,100000)\n let count=owned_timer_ticks(timer)\n if count\n  return 1\n end\n do irq_restore(8)\n do timer_delay_us(10000,100000)\n let saved=irq_save()\n set count=owned_timer_ticks(timer)\n do peripheral_release(timer)\n return count<5\n')
 run('duplicate-install-preserves-owner',START+' let again=irq_install(dispatch)\n if again!=0x80000402\n  return 1\n end\n do peripheral_release(timer)\n return 0\n')
 run('register-preservation',START+' do irq_enable()\n let result=register_probe()\n let saved=irq_save()\n let count=owned_timer_ticks(timer)\n do peripheral_release(timer)\n return result|(count<5)\n',extra='fn register_probe()\n'+(' do load32(0x3FCA8300)\n'*300)+' return 0\nend\n',binary_patch=register_patch)
 run('storm-budget-fails-closed',START+' do irq_enable()\n while 1\n end\n return 1\n',handler='return 0',fault=0x80000404)
 run('foreground-starvation-budget',START+' do irq_enable()\n while 1\n end\n return 1\n',fault=0x80000404)
 run('unexpected-cpu-line',START+' do irq_enable()\n do store32(0x600C2094,2)\n do store32(0x600C211C,1)\n do store32(0x600C2104,4)\n while 1\n end\n return 1\n',fault=0x80000403)
 run('handler-error-fails-closed',START+' do irq_enable()\n while 1\n end\n return 1\n',handler='return 42',fault=42)
 def trap_patch(prefix,offsets):image_mutate(prefix,offsets['explode'],struct.pack('<I',0x00100073))
 run('nested-synchronous-fault',START+' do irq_enable()\n while 1\n end\n return 1\n',handler='return explode()',extra='fn explode()\n return 0\nend\n',binary_patch=trap_patch,fault=0x80000405)
 run('storm-watchdog-reset',START+' do watchdog_arm_ms(100)\n do irq_enable()\n while 1\n end\n return 1\n',handler='return 0',resets=7)
 run('duplicate-and-stale-leases',INIT+' let first=peripheral_claim(1)\n if peripheral_claim(1)!=0x80000502\n  return 1\n end\n if peripheral_validate(first,2)!=0x80000503\n  return 2\n end\n do peripheral_release(first)\n let next=peripheral_claim(1)\n if first==next\n  return 3\n end\n if peripheral_release(first)!=0x80000503\n  return 4\n end\n if peripheral_validate(next,1)\n  return 5\n end\n return peripheral_release(next)\n')
 run('invalid-lease-arguments',INIT+' let bad=peripheral_claim(0)|peripheral_claim(3)|peripheral_validate(0,1)\n return (bad&0x80000000)==0\n')
 run('generation-exhaustion-no-wrap',INIT+' let first=peripheral_claim(2)\n do peripheral_release(first)\n do store32(0x3FCA8208,0x007FFFFF)\n return peripheral_claim(2)!=0x80000505\n')
 run('release-failure-retains-lease',INIT+' do store32(0x3FCA8340,0)\n let timer=peripheral_claim(1)\n do store32(0x3FCA8340,1)\n if peripheral_release(timer)!=0x80000504\n  return 1\n end\n if peripheral_validate(timer,1)\n  return 2\n end\n do store32(0x3FCA8340,0)\n return peripheral_release(timer)\n',hook=True)
 run('ownership-without-dispatcher',' do watchdog_disarm()\n let token=peripheral_claim(2)\n if token&0x80000000\n  return token\n end\n do peripheral_release(token)\n return irq_restore(8)!=0x80000401\n',handler=None)
 run('enable-before-install-refused',' do watchdog_disarm()\n if irq_enable()!=0x80000401\n  return 1\n end\n let status=irq_install(dispatch)\n return status\n')
 run('owned-watchdog-lifecycle',INIT+' let token=peripheral_claim(2)\n if owned_watchdog_arm(token,100)\n  return 1\n end\n do timer_delay_us(20000,100000)\n if owned_watchdog_feed(token)\n  return 2\n end\n do peripheral_release(token)\n if owned_watchdog_feed(token)!=0x80000503\n  return 3\n end\n return timer_delay_us(200000,100000)\n')
 # Refusals are compile-only, before any target image publication.
 good='profile RF2_ESP32C3_V1\ninterrupt fn dispatch(cause)\n return 0\nend\nfn main()\n do irq_install(dispatch)\n return 0\nend\n'
 bad={
 'handler-loop':good.replace('return 0\nend\nfn main','while 1\n end\n return 0\nend\nfn main'),
 'handler-enable':good.replace('interrupt fn dispatch(cause)\n return 0','interrupt fn dispatch(cause)\n do irq_enable()\n return 0'),
 'handler-restore':good.replace('interrupt fn dispatch(cause)\n return 0','interrupt fn dispatch(cause)\n do irq_restore(8)\n return 0'),
 'handler-replenish':good.replace('interrupt fn dispatch(cause)\n return 0','interrupt fn dispatch(cause)\n do irq_replenish()\n return 0'),
 'ordinary-handler-call':good.replace('return 0\nend\n','return 0\nend\n',1).replace('do irq_install(dispatch)','do irq_install(dispatch)\n do dispatch(1)'),
 'wrong-handler-arity':good.replace('dispatch(cause)','dispatch()'),
 'two-dispatchers':good+'interrupt fn another(cause)\n return 0\nend\n',
 'missing-install':good.replace('do irq_install(dispatch)','do load32(0)'),
 'non-handler-install':good.replace('interrupt fn dispatch','fn dispatch'),
 'indirect-blocking-handler':good.replace('return 0\nend\nfn main','return blocked()\nend\nfn blocked()\n while 1\n end\n return 0\nend\nfn main'),
 'handler-lease-release':good.replace('interrupt fn dispatch(cause)\n return 0','use "lib/time.flow"\nuse "lib/watchdog.flow"\nuse "lib/peripheral.flow"\ninterrupt fn dispatch(cause)\n return peripheral_release(257)'),
 }
 for name,text in bad.items():
  folder=D/name;folder.mkdir();shutil.copytree(LIB,folder/'lib');p=folder/'bad.flow';p.write_text(text);prefix=folder/'bad';q=subprocess.run([str(C),str(p),str(prefix)],capture_output=True,timeout=15);assert q.returncode!=0,(name,q.stdout);assert not prefix.with_suffix('.bin').exists(),name
  (folder/'stderr').write_bytes(q.stderr);ROWS.append(dict(name=name,passed=True,kind='source refusal',stderr=q.stderr.decode(errors='replace')[:300],sourceSHA256=sha(p)))
 for shift in [8,10]:
  prefix=D/('long-irq-'+str(shift));source=ROOT/'examples/esp32c3/interrupt-heartbeat.flow';invoke([C,source,prefix]);e=oracle.elf(prefix.with_suffix('.elf').read_bytes());enc=oracle.encoding_oracle(e['code'],prefix);state,data=run_image(prefix,done=b'DONE\n',shift=shift,timeout=30,application=True)
  match=re.search(rb'\n([0-9A-F]{8}) ([0-9A-F]{8}) ([0-9A-F]{8})\nDONE\n',data);assert match,data;elapsed,ticks,total=[int(x,16)for x in match.groups()]
  expected=0
  for _ in range(2400):expected=(expected*1664525+1013904223)&0xffffffff
  assert 600000000<=elapsed<625000000 and 60000<=ticks<=62500 and total==expected,(elapsed,ticks,total,expected)
  assert state['runtime'][1]==0 and state['runtime'][6]==ticks and state['runtime'][7]==0,state
  assert state['leases'][4]==0 and state['leases'][5]==0,state
  ROWS.append(dict(name='long-irq-'+str(shift),passed=True,virtualMicroseconds=elapsed,interrupts=ticks,foregroundArithmetic=total,encodingWords=enc['words'],sourceSHA256=sha(source),firmwareSHA256=sha(prefix.with_suffix('.bin')),state=state))
 report=dict(schema='rf2.esp32c3.interrupt-ownership.v1',passed=True,cases=len(ROWS),rows=ROWS,compilerSHA256=sha(C),qemuSHA256=sha(Q),controllerSHA256=sha(__file__),encodingOracleSHA256=sha(ROOT/'tests/standalone/embedded_verify.py'),sources={str(p.relative_to(ROOT)):sha(p)for p in [ROOT/'native/embedded/compiler.flow',ROOT/'examples/esp32c3/interrupt-heartbeat.flow',LIB/'peripheral.flow']},scope='Actual vendor QEMU interrupts/reset and GNU encoding checks; register probe and nested exception use explicit binary fixture injection, release readback uses a test hook. Checked boot-local leases are not a sandbox against trusted raw MMIO. No physical board/timing, nested asynchronous ISR, FPU, RTOS or performance claim.')
except BaseException:
 (D/'report.json').write_text(json.dumps(dict(passed=False,rows=ROWS,failure=traceback.format_exc()),indent=2)+'\n');raise
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(ROWS),report=str(D/'report.json'))))
