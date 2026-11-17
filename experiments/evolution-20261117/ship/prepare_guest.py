"""Materialize isolated RF2Ship0.18 snapshots; never write to the input tree."""
from pathlib import Path
import subprocess,hashlib,json,shutil,re,sys
S=Path(__file__).resolve().parent;R=S.parents[2];A=R/'artifacts/evolution-20261117/ship'
orig=Path(sys.argv[1] if len(sys.argv)>1 else '/Users/ik/Projects/RiverFlow');V=orig/'experiments/rf2ship/secure-transport-018';G=A/'guest-source';C=A/'guest-candidate-source';G.mkdir(parents=True,exist_ok=True)
expected='7a58bfcd20f6bd9a15555bd2052cadc6b2dae63e108d6d2d27dbbb95a35eb222'
assert hashlib.sha256((V/'aead_reference.c').read_bytes()).hexdigest()==expected,'source changed: review before rebuilding'
manifest={}
for p in list(V.glob('*.s'))+[V/n for n in ['build.py','wire_peer.py','route_oracle.py','intent_client.py','secure_verify.py']]:
 b=p.read_bytes();(G/p.name).write_bytes(b);manifest[p.name]=hashlib.sha256(b).hexdigest()
b=(orig/'experiments/rf2boot/guards.flow').read_bytes();(G/'guards.flow').write_bytes(b);manifest['guards.flow']=hashlib.sha256(b).hexdigest()
s=(G/'build.py').read_text().replace("Path('experiments/rf2boot/guards.flow')","(V/'guards.flow')").replace("'experiments/rf2ship/secure-transport-018/loader.s'","str(V/'loader.s')").replace("'experiments/rf2ship/secure-transport-018/bios-memory.s'","str(V/'bios-memory.s')").replace("Path('artifacts/rf2decision-sustained/compiler-opt').resolve()",repr(str(orig/'artifacts/sdk-050-builder-final/program')))
# compiler expression is a Path, not a string.
s=s.replace("compiler="+repr(str(orig/'artifacts/sdk-050-builder-final/program'))+';',"compiler=Path("+repr(str(orig/'artifacts/sdk-050-builder-final/program'))+');')
(G/'build.py').write_text(s)
s=(G/'secure_verify.py').read_text().replace("D=Path('artifacts/rf2ship-secure-018')","D=Path(sys.argv[1])");(G/'secure_verify.py').write_text(s)
shutil.copytree(G,C,dirs_exist_ok=True)
cmd=['clang','-target','x86_64-apple-macos11','-Oz','-ffreestanding','-fno-builtin','-fno-stack-protector','-mno-red-zone','-mno-sse','-mno-mmx','-fno-vectorize','-fno-slp-vectorize','-S',str(S/'candidate.c'),'-o',str(A/'candidate-x86.s')];subprocess.run(cmd,check=True)
s=(A/'candidate-x86.s').read_text();s=re.sub(r'\b_(rf2_aead|block|qr|addp|mulp|poly|cipher|wipe|l32|l64|s32|s64)\b',r'Lcrypto_\1',s);s='\n'.join(l for l in s.splitlines() if not any(x in l for x in ['.globl','.build_version','.subsections_via_symbols']))+'\n';assert not re.search(r'callq\s+_',s);assert all('__TEXT,__text' in l for l in s.splitlines() if '.section' in l);(C/'crypto.s').write_text(s)
parts=['relay.s','nat.s','clock.s','service.s','arp.s','stats.s','icmp.s','routes.s','pending.s','tcp.s','intent.s','secure.s','crypto.s'];(C/'console.s').write_text((C/'console-head.s').read_text()+'\n'.join((C/n).read_text() for n in parts))
(A/'GUEST-SOURCE-HASHES.json').write_text(json.dumps(manifest,indent=2)+'\n')
for name,source in [('baseline',G),('candidate',C)]:
 out=A/('guest-'+name);subprocess.run([sys.executable,str(source/'build.py'),str(out),str(source)],cwd=R,check=True)
 subprocess.run([sys.executable,str(source/'secure_verify.py'),str(out)],cwd=R,check=True)
print('Both isolated guest campaigns passed; no live VM or network touched.')
