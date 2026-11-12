"""Development-only phase binaries. OS process timing of batched native phases."""
from pathlib import Path
import subprocess,json,time,statistics,hashlib,os
R=Path(__file__).resolve().parents[1];D=R/'output/profile-0.8-optimized-final';D.mkdir();C=Path(os.environ.get('RF2_PROFILE_COMPILER',str(R/'output/native-compiler/rf2c')))
base=''.join((R/x).read_text()for x in ['native/rf2.rf2','native/core.rf2','native/attendance.rf2','native/attendance-kernel.rf2','native/fingerprint.rf2','native/invoice.rf2','native/invoice-kernel.rf2','native/prepared.rf2','native/workspace.rf2'])
a=base.index('fn ivbuild(');b=base.index('\nfn ivrender',a);original=base[a:b];cut=original.index(' set subtotal = ivg_entry')
validate=original[:cut].replace('fn ivbuild(','fn ivvalidate(')+' do store64(buffer("invoice_state", 80) + 32, count)\n return 1\nend\n'
calc='fn ivcalc()\n let count = load64(buffer("invoice_state", 80) + 32)\n let subtotal = 0\n let tax = 0\n let total = 0\n let data = buffer("invoice_words", 8000)\n'+original[cut:]
base=base[:a]+validate+calc+'\nfn ivbuild(lines)\n do ivvalidate(lines)\n return ivcalc()\nend\n'+base[b:];base=base.replace('fn main(argc, argv)','fn rf2_original_main(argc, argv)',1)
main='''\nfn main(argc, argv)
 let src = read_source(load64(argv + 8))
 let size = load64(state() + 88)
 let rounds = unsigned(load64(argv + 16), slen(load64(argv + 16)))
 let i = 0
 do json_parse(src, size)
 do ivplan("rf2 app v1 invoice total currency MYR tax 600 bps", 46)
 do ivvalidate(0)
 while i < rounds
 PHASE
  set i = i + 1
 end
 if load64(state()) != 0
  return 1
 end
 return 0
end
'''
# Literal length is derived, never guessed.
plan='rf2 app v1 invoice total currency MYR tax 600 bps';main=main.replace(', 46)',', '+str(len(plan))+')')
commands={'parse':'do json_parse(src, size)','plan':'do ivplan("'+plan+'", '+str(len(plan))+')','validate':'do ivvalidate(0)','kernel_tax':'do ivcalc()'}
report={'scope':'Development phase binaries, cached bytes/tokens/validated words as applicable; process wall time includes startup and one setup validation. 1000 iterations amortize setup. Phase results are not additive whole-request latency or an independent profiler.','iterations':1000,'lines':1000,'trials':{},'sourceHashes':{}}
fixture=D/'lines.json';fixture.write_text(json.dumps([{'quantity':1+i%5,'unit_cents':100+i%97}for i in range(1000)],separators=(',',':')))
for name,command in commands.items():
 p=D/(name+'.rf2');p.write_text(base+main.replace('PHASE',command));binary=D/name;subprocess.run([C,p,binary],check=True,capture_output=True);subprocess.run(['/usr/bin/codesign','-s','-',binary],check=True,capture_output=True);values=[]
 for _ in range(3):
  start=time.perf_counter_ns();subprocess.run([binary,fixture,'1000'],check=True,env={'PATH':'/nonexistent'},capture_output=True);values.append((time.perf_counter_ns()-start)/1000/1000)
 report['trials'][name]={'microsecondsPerIteration':values,'medianUs':statistics.median(values)};report['sourceHashes'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
(R/'docs/INVOICE-PHASE-PROFILE-OPTIMIZED-0.8.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['trials'],indent=2))
