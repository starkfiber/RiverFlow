from pathlib import Path
import subprocess,struct,json,hashlib,tempfile,sys
D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('artifacts/rf2ship-secure-018');V=Path(sys.argv[2]) if len(sys.argv)>2 else Path('experiments/rf2ship/secure-transport-018')
D.mkdir(parents=True,exist_ok=True)
if (V/'relay.s').is_file() and (V/'nat.s').is_file():
 assert (V/'console.s').read_text().endswith((V/'relay.s').read_text()+'\n'+(V/'nat.s').read_text()+'\n'+(V/'clock.s').read_text()+'\n'+(V/'service.s').read_text()+'\n'+(V/'arp.s').read_text()+'\n'+(V/'stats.s').read_text()+'\n'+(V/'icmp.s').read_text()+'\n'+(V/'routes.s').read_text()+'\n'+(V/'pending.s').read_text()+'\n'+(V/'tcp.s').read_text()+'\n'+(V/'intent.s').read_text()+'\n'+(V/'secure.s').read_text()+'\n'+(V/'crypto.s').read_text()),'regenerate the combined console after editing relay/NAT fragments'
if (V/'console-head.s').is_file():
 assert (V/'console.s').read_text()==(V/'console-head.s').read_text()+'\n'.join((V/n).read_text() for n in ['relay.s','nat.s','clock.s','service.s','arp.s','stats.s','icmp.s','routes.s','pending.s','tcp.s','intent.s','secure.s','crypto.s']), 'regenerate combined console from current head/fragments'
# Checked assembly-reference regeneration prevents accidental stale-object reuse.
subprocess.run(['clang','-target','x86_64-apple-macos11','-c',str(V/'console.s'),'-o',str(D/'console.o')],check=True)
raw=(D/'console.o').read_bytes();at=32;code=None;symbols={}
for _ in range(struct.unpack_from('<I',raw,16)[0]):
 cmd,size=struct.unpack_from('<II',raw,at)
 if cmd==0x19:
  for j in range(struct.unpack_from('<I',raw,at+64)[0]):
   p=at+72+j*80
   if raw[p:p+16].rstrip(b'\0')==b'__text':
    length=struct.unpack_from('<Q',raw,p+40)[0];off=struct.unpack_from('<I',raw,p+48)[0];assert struct.unpack_from('<I',raw,p+60)[0]==0;code=raw[off:off+length]
 if cmd==2:
  symoff,nsyms,stroff,strsize=struct.unpack_from('<4I',raw,at+8);strings=raw[stroff:stroff+strsize]
  for i in range(nsyms):
   nameoff,kind,sect,desc,value=struct.unpack_from('<IBBHQ',raw,symoff+16*i);name=strings[nameoff:].split(b'\0',1)[0].decode();symbols[name]=value
 at+=size
assert code and symbols['_rf2ship_console']==0
prologue=bytes.fromhex('5053515256575541504151415241534154415541564157');assert code.count(prologue)==1;symbols['_rf2ship_pf']=code.index(prologue)
source=Path('experiments/rf2boot/guards.flow').read_text()
# Forty loaded BIOS sectors:17 at8000,18 ata200,5 atc600, endd000.
source=source.replace('4608','32768').replace('8192','32768')
def emit(bs):return ''.join(' do byte(%d)\n'%b for b in bs)
subprocess.run(['clang','-target','x86_64-apple-macos11','-c','experiments/rf2ship/secure-transport-018/loader.s','-o',str(D/'loader.o')],check=True)
obj=(D/'loader.o').read_bytes();off=32;loader=None
for _ in range(struct.unpack_from('<I',obj,16)[0]):
 command,size=struct.unpack_from('<II',obj,off)
 if command==0x19:
  for k in range(struct.unpack_from('<I',obj,off+64)[0]):
   sec=off+72+k*80
   if obj[sec:sec+16].rstrip(b'\0')==b'__text':
    assert struct.unpack_from('<I',obj,sec+60)[0]==0
    start=struct.unpack_from('<I',obj,sec+48)[0];length=struct.unpack_from('<Q',obj,sec+40)[0];loader=obj[start:start+length]
 off+=size
assert loader and len(loader)<510

a=source.index(' do byte(250)\n',source.index('fn main('));b=source.index(' do store8(buffer("image",32768)+510',a)
source=source[:a]+emit(loader)+source[b:]
# Copy code into formerly unused old IST pages; move guarded PF stack to12000..13000.
old=bytes.fromhex('c7055040000000000000')
new=bytes.fromhex('c7055040000001a00000c7055840000001b00000c7056040000001c00000c7059040000003200100c7056840000001d00000c7057040000001e00000c7057840000001f00000')
assert source.count(emit(old))==1
source=source.replace(emit(old),emit(new),1)
old=bytes.fromhex('48c704252458000000c00000');new=bytes.fromhex('48c704252458000000300100')
assert source.count(emit(old))==1
source=source.replace(emit(old),emit(new),1)

# Relocate the GDT after scratch RAM initialization and before paging.
# Page6 remains the main-stack guard; owned metadata stays in mapped page5.
copy_gdt=' do byte(190)\n let gdt_copy_ref=position()\n do dword(0)\n do byte(191)\n do dword(0x5700)\n do byte(185)\n do dword(48)\n do byte(243)\n do byte(164)\n do byte(15)\n do byte(1)\n do byte(21)\n let relocated_gdtr_ref=position()\n do dword(0)\n'
clear=' do byte(243)\n do byte(171)\n'
assert source.count(clear)==1
source=source.replace(clear,clear+copy_gdt,1)
relocated=' let relocated_gdtr=position()+0x7e00\n do word(47)\n do dword(0x5700)\n do patch16(gdt_copy_ref,gdt)\n do patch16(relocated_gdtr_ref,relocated_gdtr)\n'
source=source.replace(' let gdtr=position()+0x7e00\n',relocated+' let gdtr=position()+0x7e00\n',1)
# BIOS conventional RAM check covers both DMA arenas and reserved metadata.
subprocess.run(['clang','-target','x86_64-apple-macos11','-c','experiments/rf2ship/secure-transport-018/bios-memory.s','-o',str(D/'bios-memory.o')],check=True)
obj=(D/'bios-memory.o').read_bytes();off=32;bios=None
for _ in range(struct.unpack_from('<I',obj,16)[0]):
 command,size=struct.unpack_from('<II',obj,off)
 if command==0x19:
  for k in range(struct.unpack_from('<I',obj,off+64)[0]):
   sec=off+72+k*80
   if obj[sec:sec+16].rstrip(b'\0')==b'__text':
    assert struct.unpack_from('<I',obj,sec+60)[0]==0
    start=struct.unpack_from('<I',obj,sec+48)[0];length=struct.unpack_from('<Q',obj,sec+40)[0];bios=obj[start:start+length]
 off+=size
assert bios
entry=' do byte(250)\n do port(1017,0)'
assert source.count(entry)==1
source=source.replace(entry,' do byte(250)\n'+emit(bios)+' do port(1017,0)',1)
needle=' do byte(186)\n do byte(248)\n do byte(3)\n do byte(0)\n do byte(0)\n do byte(176)\n do byte(76)\n do byte(238)\n';assert source.count(needle)==1
packed=''.join(' do dword(%d)\n'%int.from_bytes(code[i:i+4],'little') for i in range(0,len(code)-len(code)%4,4))
packed+=''.join(' do byte(%d)\n'%b for b in code[len(code)-len(code)%4:])
source=source.replace(needle,' let ship_start=position()\n'+packed+needle,1)
source=source.replace(' let pf=position()+0x7e00',' let pf=ship_start+%d+0x7e00'%symbols['_rf2ship_pf'],1)
p=V/'boot.flow';p.write_text(source);compiler=Path('artifacts/rf2decision-sustained/compiler-opt').resolve();exe=Path(tempfile.mkdtemp(prefix='build-',dir=D))/'emitter'
subprocess.run([str(compiler),str(p),str(exe),'--compact','--opt'],check=True);subprocess.run(['codesign','-s','-',str(exe)],check=True)
b=subprocess.check_output([str(exe.resolve())]);assert len(b)==32768 and b[510:512]==b'\x55\xaa'
assert b.count(code)==1,'RF2 emitter must preserve the exact relocation-free reference text'
(D/'rf2ship.img').write_bytes(b.ljust(1474560,b'\0'))
folder=D/'iso-root';folder.mkdir(exist_ok=True);(folder/'boot.img').write_bytes(b.ljust(1474560,b'\0'));(folder/'README.txt').write_text('RF2Ship0.18-dev: isolated PCI inventory and timer/recovery lab, not hypervisor/installer/firewall.\n')
subprocess.run(['xorriso','-as','mkisofs','-V','RF2SHIP_IFACE','-b','boot.img','-c','boot.cat','-o',str(D/'rf2ship.iso'),str(folder)],check=True)
(D/'MANIFEST.json').write_text(json.dumps(dict(version='0.18-dev',compilerSHA256=hashlib.sha256(compiler.read_bytes()).hexdigest(),symbols=symbols,files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [V/'console.s',V/'boot.flow',D/'rf2ship.img',D/'rf2ship.iso']}),indent=2)+'\n')
