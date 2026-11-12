"""Explicit bootstrap compatibility repair: empty dyld fixup command, no code changes.
macOS 15 dyld's legacy relocation path dereferences absent metadata in our old image.
New RF2 compiler output emits LC_DYLD_INFO_ONLY directly. This tool patches the pinned
0.17 bootstrap only, then ad-hoc signs it. Development tool, not RF2 runtime.
"""
from pathlib import Path
import struct,sys,subprocess,hashlib,json
p=Path(sys.argv[1]);b=bytearray(p.read_bytes());before=hashlib.sha256(b).hexdigest();assert struct.unpack_from('<I',b)[0]==0xfeedfacf
n,size=struct.unpack_from('<II',b,16);off=32;commands=[]
for _ in range(n):
 cmd,length=struct.unpack_from('<II',b,off);assert length>=8;commands.append(cmd);off+=length
assert off==32+size and off+48<16384 and not any(b[off:off+48]);assert 0x80000022 not in commands
b[off:off+48]=struct.pack('<12I',0x80000022,48,*([0]*10));struct.pack_into('<II',b,16,n+1,size+48);p.write_bytes(b)
subprocess.run(['/usr/bin/codesign','--force','-s','-',p],check=True)
print(json.dumps({'inputSHA256':before,'outputSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'repair':'empty LC_DYLD_INFO_ONLY; original code/data bytes unchanged before resigning'}))
