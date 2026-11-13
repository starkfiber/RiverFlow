"""Real vendor-QEMU timer/watchdog controls, with explicit fault-hook cases.

No physical devices are opened. Virtual time is not a speed or hardware result.
An observed QEMU protection gap is retained as a limitation, never a product pass.
"""
from pathlib import Path
import hashlib, json, os, re, subprocess, time, traceback

ROOT = Path(__file__).resolve().parents[2]
COMPILER = Path(os.environ['RF2_ESP_COMPILER']).resolve()
QEMU = Path(os.environ['RF2_ESP_QEMU']).resolve()
OUT = ROOT / 'artifacts/sprint-035' / ('time-verify-' + str(time.time_ns()))
OUT.mkdir(parents=True)
LIB = ROOT / 'examples/esp32c3/lib'
SOURCES = {name: (LIB / (name + '.flow')).read_text() for name in ['time', 'watchdog', 'uart']}
ROWS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(text):
    return ''.join(f' do serial_byte({b})\n' for b in text.encode('ascii'))


def capture(prefix, image, done, shift=10, timeout=20, reset_count=0):
    flash = prefix.with_suffix('.flash.bin')
    flash.write_bytes(image + b'\xff' * (4 * 1024 * 1024 - len(image)))
    uart = prefix.with_suffix('.uart')
    command = [str(QEMU), '-display', 'none', '-monitor', 'stdio', '-serial',
               'file:' + str(uart), '-icount', str(shift), '-machine', 'esp32c3',
               '-drive', 'file=' + str(flash) + ',if=mtd,format=raw', '-nic', 'none']
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = b'', b''
    try:
        deadline = time.monotonic() + timeout
        satisfied = False
        while time.monotonic() < deadline:
            data = uart.read_bytes() if uart.exists() else b''
            assert len(data) < 1024 * 1024, 'UART output budget exceeded'
            satisfied = (data.count(b'CASE BOOT ') >= reset_count if reset_count else done in data)
            if satisfied or p.poll() is not None:
                break
            time.sleep(.015)
        assert satisfied, ('firmware observation deadline', data[-2000:])
        # Allow the printed result's function epilogue to return before stopping.
        time.sleep(.015)
        stdout, stderr = p.communicate(b'stop\ninfo registers\nquit\n', timeout=5)
    finally:
        if p.poll() is None:
            p.kill()
            stdout, stderr = p.communicate(timeout=5)
        prefix.with_suffix('.monitor').write_bytes(stdout)
        prefix.with_suffix('.stderr').write_bytes(stderr)
    assert p.returncode == 0, stderr
    data = uart.read_bytes()
    for warning in [b'comparison failed', b'Checksum mismatch', b'Attempting to boot anyway']:
        assert warning not in data, ('ROM rejected image integrity', data)
    registers = stdout.decode(errors='replace')
    def reg(pattern):
        match = re.search(pattern, registers)
        assert match, (pattern, registers)
        return int(match.group(1), 16)
    return data, dict(a0=reg(r'x10/a0\s+([0-9a-f]+)'), sp=reg(r'x2/sp\s+([0-9a-f]+)'),
                      pc=reg(r'\bpc\s+([0-9a-f]+)'), mie=reg(r'\bmie\s+([0-9a-f]+)'))


def run(name, body, expected=0, shift=10, reset_reason=None, hooks=None, limitation=False):
    folder = OUT / name
    folder.mkdir()
    (folder / 'lib').mkdir()
    for module, text in SOURCES.items():
        if hooks and module == hooks['module']:
            text = text.replace('load32(', 'fault_load32(').replace('store32(', 'fault_store32(')
            text += hooks['source']
        (folder / 'lib' / (module + '.flow')).write_text(text)
    main = ('profile RF2_ESP32C3_V1\nuse "lib/time.flow"\nuse "lib/watchdog.flow"\nuse "lib/uart.flow"\n'
            'fn test()\n' + body + '\nend\nfn main()\n' + emit('CASE BOOT ') +
            ' do serial_hex(reset_cause())\n do serial_byte(10)\n let result=test()\n' + emit('RESULT ') +
            ' do serial_hex(result)\n do serial_byte(10)\n return result\nend\n')
    source = folder / 'main.flow'
    source.write_text(main)
    prefix = folder / 'firmware'
    q = subprocess.run([str(COMPILER), str(source), str(prefix)], capture_output=True, timeout=20)
    prefix.with_suffix('.compile.out').write_bytes(q.stdout)
    prefix.with_suffix('.compile.err').write_bytes(q.stderr)
    assert q.returncode == 0, (name, q.stderr)
    image = prefix.with_suffix('.bin').read_bytes()
    data, regs = capture(prefix, image, f'RESULT {expected:08X}\n'.encode(), shift,
                         reset_count=3 if reset_reason is not None else 0)
    if reset_reason is not None:
        causes = [int(v, 16) for v in re.findall(rb'CASE BOOT ([0-9A-F]{8})\n', data)]
        assert causes[0] == 1 and causes[1:3] == [reset_reason] * 2, (name, causes, data)
        assert b'RESULT ' not in data, (name, 'reset failed to occur before firmware deadline', data)
    else:
        assert data.count(b'CASE BOOT ') == 1, (name, 'unexpected reset', data)
        assert regs == dict(a0=expected, sp=0x3fcc0000, pc=0x40380018, mie=0), (name, regs)
        causes = [1]
    row = dict(name=name, passed=not limitation, observationComplete=True, knownEmulatorLimitation=limitation,
               faultHooks=bool(hooks), physicalHardware=False, shift=shift, resetCauses=causes[:3],
               expectedReturn=None if reset_reason is not None else expected,
               sourceSHA256=sha(source), firmwareSHA256=sha(prefix.with_suffix('.bin')),
               uartSHA256=sha(prefix.with_suffix('.uart')), registers=regs)
    ROWS.append(row)
    print(json.dumps(row), flush=True)


INIT = ' let status=watchdog_disarm()\n if status\n  return status\n end\n set status=timer_init()\n if status\n  return status\n end\n'

try:
    for shift in [6, 10]:
        run('timer-delay-shift' + str(shift), INIT +
            ' let start=timer_us32()\n set status=timer_delay_us(20000,100000)\n if status\n  return status\n end\n'
            ' do timer_capture()\n let elapsed=timer_elapsed(timer_us32(),start)\n'
            ' do serial_hex(elapsed)\n do serial_byte(10)\n'
            ' return (elapsed<20000)|(elapsed>100000)\n', shift=shift)
    run('wrapping-microseconds', INIT +
        ' do store32(0x6002300C,15)\n do store32(0x60023010,0xFFFF0000)\n do store32(0x6002305C,1)\n'
        ' do timer_capture()\n let start=timer_us32()\n'
        ' set status=timer_delay_us(20000,100000)\n if status\n  return status\n end\n'
        ' do timer_capture()\n let finish=timer_us32()\n let elapsed=timer_elapsed(finish,start)\n'
        ' return (finish>=start)|(elapsed<20000)|(elapsed>100000)\n')
    run('frozen-clock-and-recovery', INIT +
        ' do store32(0x60023000,load32(0x60023000)&0xBFFFFFFF)\n'
        ' if timer_delay_us(100,16)!=0x80000102\n  return 1\n end\n'
        ' if timer_init()\n  return 2\n end\n return timer_delay_us(2000,100000)\n')
    for duration, budget in [(0x80000000, 16), (0xffffffff, 16), (1, 0)]:
        run(f'refuse-delay-{duration}-{budget}', INIT + f' return timer_delay_us({duration},{budget})\n', expected=0x80000103)
    run('zero-delay', INIT + ' return timer_delay_us(0,1)\n')
    run('deadline-wrap-math', INIT +
        ' return (timer_elapsed(16,0xFFFFFFF0)!=32)|(timer_due(16,0xFFFFFFF0)!=1)|'
        '(timer_due(0xFFFFFFF0,16)!=0)|(timer_due(16,16)!=1)|(timer_due(0x80000000,0)!=0)\n')
    for value in [0, 9, 60001, 0xffffffff]:
        run('refuse-watchdog-' + str(value), INIT +
            f' if watchdog_arm_ms({value})!=0x80000201\n  return 1\n end\n'
            ' return load32(0x6001F048)&0x80004000\n')
    run('feed-disarmed', INIT + ' return watchdog_feed()\n', expected=0x80000203)
    run('disarm-survives-expiry', INIT +
        ' if watchdog_arm_ms(100)\n  return 1\n end\n do timer_delay_us(20000,100000)\n'
        ' if watchdog_disarm()\n  return 2\n end\n return timer_delay_us(250000,100000)\n')
    run('protected-config-write', INIT +
        ' if watchdog_arm_ms(1000)\n  return 1\n end\n let original=load32(0x6001F048)\n'
        ' do store32(0x6001F048,0)\n let changed=load32(0x6001F048)!=original\n do watchdog_disarm()\n return changed\n')
    run('unfed-reset', ' do watchdog_arm_ms(100)\n while 1\n end\n return 9\n', reset_reason=7)
    run('unfed-reset-deadline', INIT +
        ' do watchdog_arm_ms(100)\n do timer_delay_us(200000,100000)\n return 9\n', reset_reason=7)
    run('rearm-shorter-reset', INIT +
        ' do watchdog_arm_ms(1000)\n do timer_delay_us(20000,100000)\n do watchdog_arm_ms(50)\n do timer_delay_us(100000,100000)\n return 9\n', reset_reason=7)
    run('invalid-rearm-keeps-supervision', INIT +
        ' do watchdog_arm_ms(100)\n if watchdog_arm_ms(0)!=0x80000201\n  return 1\n end\n'
        ' do timer_delay_us(200000,100000)\n return 9\n', reset_reason=7)
    run('software-reset', ' do system_reset()\n return 9\n', reset_reason=3)
    latch_hooks = dict(module='time', source='''
fn fault_load32(address)
 if address==0x60023004
  do store32(0x3FCA0010,load32(0x3FCA0010)+1)
  return 0
 end
 return load32(address)
end
fn fault_store32(address,value)
 do store32(address,value)
 return 0
end
''')
    run('snapshot-never-ready', ' do watchdog_disarm()\n do store32(0x3FCA0010,0)\n'
        ' if timer_init()!=0x80000101\n  return 1\n end\n return load32(0x3FCA0010)!=64\n', hooks=latch_hooks)
    ignored_reset = dict(module='watchdog', source='''
fn fault_load32(address)
 return load32(address)
end
fn fault_store32(address,value)
 if address!=0x60008000
  do store32(address,value)
 end
 return 0
end
''')
    run('reset-write-ignored', INIT + ' return system_reset()\n', expected=0x80000204, hooks=ignored_reset)
    readback_hooks = dict(module='watchdog', source='''
fn fault_load32(address)
 if address==0x6001F050
  return 0
 end
 return load32(address)
end
fn fault_store32(address,value)
 do store32(address,value)
 return 0
end
''')
    run('watchdog-readback-failure', INIT +
        ' let result=watchdog_arm_ms(1000)\n do watchdog_disarm()\n return result\n',
        expected=0x80000202, hooks=readback_hooks)
    # Wrapper logging uses the same injected UART and cannot print a result.
    # Execute this control using the ordinary UART wrapper and a renamed copy.
    uart_body = SOURCES['uart'].split('\n',1)[1].replace('serial_byte','blocked_byte').replace('serial_hex','blocked_hex')
    uart_body = uart_body.replace('load32(0x6000001C)', '(127<<16)')
    run('uart-full-is-bounded', INIT + ' return blocked_byte(82)\n', expected=0x80000301,
        hooks=dict(module='uart',source=uart_body + '''
fn fault_load32(address)
 return load32(address)
end
fn fault_store32(address,value)
 do store32(address,value)
 return 0
end
'''))
    run('qemu-locked-stage-register-gap', INIT +
        ' do watchdog_arm_ms(1000)\n let before=load32(0x6001F050)\n'
        ' do store32(0x6001F050,before+1)\n let writable=load32(0x6001F050)!=before\n'
        ' do watchdog_disarm()\n return writable\n', expected=1, limitation=True)
    for shift in [6, 10]:
        name='heartbeat-120-virtual-seconds-shift'+str(shift)
        prefix=OUT/name
        source=ROOT/'examples/esp32c3/timed-heartbeat.flow'
        subprocess.run([str(COMPILER),str(source),str(prefix)],capture_output=True,check=True,timeout=20)
        data, regs=capture(prefix,prefix.with_suffix('.bin').read_bytes(),b'DONE\n',shift=shift,timeout=35)
        assert data.count(b'H00000001\n')==1 and data.count(b'entry ')==1,data
        assert re.search(rb'\n\.{30}\n([0-9A-F]{8})\nDONE\n',data),data
        elapsed=int(re.search(rb'\n\.{30}\n([0-9A-F]{8})\nDONE\n',data).group(1),16)
        assert 120000000<=elapsed<125000000,(elapsed,data)
        assert regs==dict(a0=0,sp=0x3fcc0000,pc=0x40380018,mie=0),regs
        ROWS.append(dict(name=name,passed=True,knownEmulatorLimitation=False,faultHooks=False,physicalHardware=False,
                         shift=shift,virtualElapsedMicroseconds=elapsed,completedIntervals=480,watchdogFeeds=480,
                         sourceSHA256=sha(source),firmwareSHA256=sha(prefix.with_suffix('.bin')),uartSHA256=sha(prefix.with_suffix('.uart')),registers=regs))
        print(json.dumps(ROWS[-1]),flush=True)
    report=dict(schema='rf2.esp32c3.time-watchdog.v1',passed=True,
                productCases=sum(not row['knownEmulatorLimitation'] for row in ROWS),
                emulatorLimitations=sum(row['knownEmulatorLimitation'] for row in ROWS),rows=ROWS,
                compilerSHA256=sha(COMPILER),qemuSHA256=sha(QEMU),controllerSHA256=sha(__file__),
                libraries={name:sha(LIB/(name+'.flow')) for name in SOURCES},
                scope='Vendor QEMU ROM/SPI/SYSTIMER/TIMG/UART execution, plus explicitly hooked latch/reset/readback/UART-full failure paths. Virtual durations are not wall-clock speed or physical timing. RTC watchdog not modeled. QEMU permits a locked stage-register write contrary to hardware protection contract; retained as a known emulator gap.')
except BaseException:
    report=dict(passed=False,rows=ROWS,failure=traceback.format_exc(),controllerSHA256=sha(__file__))
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    raise
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,report=str(OUT/'report.json'),productCases=report['productCases'],emulatorLimitations=report['emulatorLimitations'])))
