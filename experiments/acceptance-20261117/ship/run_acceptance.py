"""Run the implemented RF2Ship0.18 local acceptance contracts in isolated copies.

Source and unique evidence stay persistent. Rebuildable objects/images/emitters
use an explicit guarded-cache job. No remote, physical or live-network effects.
"""
from pathlib import Path
import argparse,ast,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
ORIGIN=Path('/Users/ik/Projects/RiverFlow')
SOURCE=ORIGIN/'experiments/rf2ship/secure-transport-018'
COMPILER=Path(os.environ.get('RF2_COMPILER',str(ORIGIN/'artifacts/sdk-050-builder-final/program'))).resolve()
COMPILER_SHA='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
BASE_SHA='7a58bfcd20f6bd9a15555bd2052cadc6b2dae63e108d6d2d27dbbb95a35eb222'
SCRIPTS=['secure_verify.py','tcp_verify.py','baseline_verify.py','baseline_multiflow_verify.py','start_verify.py','regression_verify.py','regression_irq_verify.py','fault_verify.py','guard_verify.py','mmio_guard_verify.py','new_page_guard_verify.py','crypto_verify.py','peer_crypto_verify.py']
COMMON=['build.py','wire_peer.py','route_oracle.py','intent_client.py','CryptoOracle.swift','aead_reference.c']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def adapt_build(s,source):
    s=s.replace('import subprocess,struct,json,hashlib,tempfile,sys','import subprocess,struct,json,hashlib,tempfile,sys,os')
    s=s.replace("Path('experiments/rf2boot/guards.flow')",repr(str(HERE/'snapshot/guards.flow')))
    s=s.replace('source='+repr(str(HERE/'snapshot/guards.flow'))+'.read_text()','source=Path('+repr(str(HERE/'snapshot/guards.flow'))+').read_text()')
    for name in ['loader.s','bios-memory.s']:s=s.replace(repr('experiments/rf2ship/secure-transport-018/'+name),'str(Path('+repr(str(source/name))+'))')
    s=s.replace("Path('artifacts/rf2decision-sustained/compiler-opt').resolve()",'Path('+repr(str(COMPILER))+')')
    # The source emitter stays in V; only generated objects/image bytes use B.
    s=s.replace('D/','B/').replace('dir=D','dir=B')
    s=s.replace('D.mkdir(parents=True,exist_ok=True)','D.mkdir(parents=True,exist_ok=True)\nB=Path(os.environ["RF2_SHIP_CACHE"])/hashlib.sha256(str(D.resolve()).encode()).hexdigest()[:16]\nB.mkdir(parents=True,exist_ok=False)')
    s=s.replace("(B/'MANIFEST.json').write_text", "(D/'MANIFEST.json').write_text")
    s+='''\n# Logical evidence paths retain hashes, not sole unique binary evidence.\nfor name in ["rf2ship.img","rf2ship.iso","console.o","loader.o","bios-memory.o"]:\n target=D/name\n assert not target.exists() and not target.is_symlink(), str(target)\n target.symlink_to(B/name)\n'''
    ast.parse(s);return s

def adapt_test(s,source):
    s=s.replace('from pathlib import Path','from pathlib import Path\nimport os',1)
    s=s.replace("Path('artifacts/rf2ship-secure-018')",'Path(os.environ["RF2_SHIP_EVIDENCE"])')
    s=s.replace("Path('experiments/rf2ship/secure-transport-018')",'Path('+repr(str(source))+')')
    s=re.sub(r"Path\('experiments/rf2ship/secure-transport-018/([^']+)'\)",lambda m:'Path('+repr(str(source/m[1]))+')',s)
    s=s.replace("dir='/tmp'","dir=os.environ['TMPDIR']")
    if 'CredentialStore(Path(tmp)' in s:
        s=s.replace("with tempfile.TemporaryDirectory(prefix='rf2if-',dir=os.environ['TMPDIR']) as tmp:","with tempfile.TemporaryDirectory(prefix='rf2if-',dir=os.environ['TMPDIR']) as tmp, tempfile.TemporaryDirectory(prefix='rf2keys-',dir='/private/tmp') as keytmp:")
        s=s.replace("Path(tmp)/'credentials'","Path(keytmp)/'credentials'")
    s=s.replace("tempfile.TemporaryDirectory(prefix='rf2-private-')","tempfile.TemporaryDirectory(prefix='rf2-private-',dir='/private/tmp')")
    # Mutant images are reproducible byte copies; generated hook source stays in D.
    helper='''\ndef write_image(path,data):\n bank=Path(os.environ["RF2_SHIP_CACHE"])/"mutants"\n bank.mkdir(parents=True,exist_ok=True)\n target=bank/(hashlib.sha256(str(path.resolve()).encode()).hexdigest()+".img")\n assert not target.exists(), str(target)\n target.write_bytes(data)\n if path.is_symlink():path.unlink()\n assert not path.exists(), str(path)\n path.symlink_to(target)\n'''
    if 'hashlib' not in s.split('\nD=')[0]:s=s.replace('import os\n','import os,hashlib\n',1)
    s=s.replace('D=Path(os.environ["RF2_SHIP_EVIDENCE"])',helper+'\nD=Path(os.environ["RF2_SHIP_EVIDENCE"])',1)
    s=s.replace('target.write_bytes(mutate(label))','write_image(target,mutate(label))').replace('image.write_bytes(changed(label))','write_image(image,changed(label))').replace('image.write_bytes(mutated)','write_image(image,mutated)')
    ast.parse(s);return s

def loss_test(source):
    s=adapt_test((HERE/'snapshot/original/secure_verify.py').read_text(),source)
    anchor="   mark=len(out);p.stdin.write(b'U');p.stdin.flush();until(b'RF2Ship> ',mark);"
    assert s.count(anchor)==1
    return s.replace(anchor,(HERE/'loss_cases.py.in').read_text()+anchor,1)

def prepare(destination):
    snapshot=HERE/'snapshot';snapshot.mkdir(exist_ok=True)
    assert sha(COMPILER)==COMPILER_SHA
    original=snapshot/'original'
    if (snapshot/'SOURCE-MANIFEST.json').exists():
        # A published single reviewed baseline snapshot makes live-tree access
        # unnecessary. Hashes establish identity, not publisher authentication.
        manifest=json.loads((snapshot/'SOURCE-MANIFEST.json').read_text())
        for name,want in manifest.items():
            if name=='experiments/rf2boot/guards.flow':p=snapshot/'guards.flow'
            else:
                prefix='experiments/rf2ship/secure-transport-018/'
                assert name.startswith(prefix)and '/'not in name[len(prefix):]and '..'not in name[len(prefix):]
                p=original/name[len(prefix):]
            assert p.is_file()and not p.is_symlink()and sha(p)==want,name
    else:
        assert sha(SOURCE/'aead_reference.c')==BASE_SHA
        files=sorted({*SOURCE.glob('*.s'),*(SOURCE/n for n in [*COMMON,*SCRIPTS])})
        manifest={str(p.relative_to(ORIGIN)):sha(p)for p in files}
        guards=ORIGIN/'experiments/rf2boot/guards.flow';manifest[str(guards.relative_to(ORIGIN))]=sha(guards)
        (snapshot/'guards.flow').write_bytes(guards.read_bytes());original.mkdir()
        for p in files:shutil.copyfile(p,original/p.name)
        (snapshot/'SOURCE-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert sha(original/'aead_reference.c')==BASE_SHA
    destination=destination.resolve();destination.mkdir(parents=True,exist_ok=False)
    assert sha(HERE/'intent_client.py')=='ba26053fd5453235fa1161094dfa5cefacd5f7f642e632f36523950a729e74a2'
    for variant in ['baseline','candidate']:
        for flavor in ['normal','debug']:
            d=destination/(variant+'-'+flavor);shutil.copytree(original,d)
            if variant=='candidate':
                shutil.copyfile(ROOT/'experiments/evolution-20261117/ship/candidate.c',d/'aead_reference.c')
                shutil.copyfile(HERE/'intent_client.py',d/'intent_client.py')
            if flavor=='debug':
                s=(d/'console-head.s').read_text()
                for key,label in [('f','Lrelay0'),('g','Lrelay1'),('a','Lif_open0'),('b','Lif_open1'),('t','Lif_transfer0'),('u','Lif_transfer1'),('v','Lnet_negotiate'),('d','Lnet_dma'),('p','Lfault')]:
                    old=" cmpb $'%s',%%al\n je Ldebug_refused"%key;assert s.count(old)==1;s=s.replace(old," cmpb $'%s',%%al\n je %s"%(key,label),1)
                (d/'console-head.s').write_text(s)
            (d/'build.py').write_text(adapt_build((original/'build.py').read_text(),d))
            for name in SCRIPTS:
                s=adapt_test((original/name).read_text(),d)
                if name=='tcp_verify.py':
                    anchor="    table=memory(0x53000,3072)\n"
                    assert s.count(anchor)==1
                    s=s.replace(anchor,anchor+"    neighbor_before=memory(0x55100,256)\n",1)
                    anchor="actual=exact(target,n);assert actual==wanted"
                    assert s.count(anchor)==1
                    s=s.replace(anchor,"actual=exact(target,n)\n"+(HERE/'tcp_neighbor.py.in').read_text()+"     assert actual==wanted",1)
                if name=='new_page_guard_verify.py':
                    insert="cases += [(label,base.replace(key,' movq $'+hex(at)+',%rax\\n callq *%rax\\n'+key,1),17,at) for label,at in [('credential-nx',0x5b000),('crypto-work-nx',0x5c000)]]\n"
                    s=s.replace('for label,source,error,address in cases:',insert+'for label,source,error,address in cases:').replace('planned=14','planned=16')
                (d/name).write_text(s)
            if variant=='candidate'and flavor=='normal':(d/'loss_verify.py').write_text(loss_test(d))
    return destination

def encode(source,cache):
    asm=cache/(source.name+'.s')
    subprocess.run(['clang','-target','x86_64-apple-macos11','-Oz','-ffreestanding','-fno-builtin','-fno-stack-protector','-mno-red-zone','-mno-sse','-mno-mmx','-fno-vectorize','-fno-slp-vectorize','-S',str(source/'aead_reference.c'),'-o',str(asm)],check=True)
    s=asm.read_text();s=re.sub(r'\b_(rf2_aead|block|qr|addp|mulp|poly|cipher|wipe|l32|l64|s32|s64)\b',r'Lcrypto_\1',s);s='\n'.join(l for l in s.splitlines()if not any(x in l for x in ['.globl','.build_version','.subsections_via_symbols']))+'\n';assert not re.search(r'callq\s+_',s)
    (source/'crypto.s').write_text(s)
    parts=['relay.s','nat.s','clock.s','service.s','arp.s','stats.s','icmp.s','routes.s','pending.s','tcp.s','intent.s','secure.s','crypto.s']
    (source/'console.s').write_text((source/'console-head.s').read_text()+'\n'.join((source/n).read_text()for n in parts))

def run(output,prepared,build_only=False):
    assert os.environ.get('TMPDIR','').startswith('/Volumes/Mac Work Cache/'),'Use the guarded disposable work-cache runner'
    snapshot=HERE/'snapshot';assert snapshot.is_dir()and prepared.is_dir(),'Run --prepare first'
    output=output.resolve();output.mkdir(parents=True,exist_ok=False)
    # A stable bank label reuses its slot; each invocation still needs fresh output.
    cache=Path(tempfile.mkdtemp(prefix='rf2ship-acceptance-',dir=os.environ['TMPDIR']))
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['RF2_SHIP_CACHE']=str(cache)
    rows=[];results={'schema':'rf2ship.local-acceptance.v1','compilerSHA256':sha(COMPILER),'sourceManifestSHA256':sha(snapshot/'SOURCE-MANIFEST.json'),'variants':{},'runs':rows,'scope':'Existing local0.18 contracts only; no VM102, live network, physical hardware or whole24gate qualification'}
    def save():(output/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n')
    def command(label,args,d,timeout=180):
        d.mkdir(parents=True,exist_ok=True);env['RF2_SHIP_EVIDENCE']=str(d);t=time.monotonic()
        with (d/'RUN.log').open('ab')as log:
            p=subprocess.run(args,cwd=ROOT,env=env,stdout=log,stderr=log,timeout=timeout)
        row={'label':label,'exit':p.returncode,'elapsedSeconds':round(time.monotonic()-t,3),'passed':p.returncode==0,'log':str((d/'RUN.log').relative_to(ROOT))};rows.append(row);save();print(label,p.returncode,flush=True)
        return p.returncode==0
    if build_only:
        source=prepared/'candidate-normal';assert sha(source/'intent_client.py')==sha(HERE/'intent_client.py')
        encode(source,cache);d=output/'candidate-build';d.mkdir()
        assert command('candidate/build',[sys.executable,str(source/'build.py'),str(d),str(source)],d)
        results.update(buildOnly=True,guestLaunched=False,clientSHA256=sha(source/'intent_client.py'),cryptoSHA256=sha(source/'aead_reference.c'),imageSHA256=sha(d/'rf2ship.img'),logicalImage=str(d/'rf2ship.img'),binaryExpiresWithCompletedCache=True);save();return 0
    for variant in ['baseline','candidate']:
        destinations={}
        for flavor in ['normal','debug']:
            source=prepared/(variant+'-'+flavor);encode(source,cache);d=output/variant/(flavor+'-build');d.mkdir(parents=True)
            assert command(variant+'/'+flavor+'/build',[sys.executable,str(source/'build.py'),str(d),str(source)],d)
            destinations[flavor]=d
        normal=prepared/(variant+'-normal');debug=prepared/(variant+'-debug')
        binary_cache=cache/(variant+'-host');binary_cache.mkdir(exist_ok=False)
        subprocess.run(['clang','-O2','-ffreestanding','-fno-builtin','-dynamiclib',str(normal/'aead_reference.c'),'-o',str(binary_cache/'aead-host.dylib')],check=True)
        subprocess.run(['swiftc','-O',str(normal/'CryptoOracle.swift'),'-o',str(binary_cache/'crypto-oracle')],check=True)
        for name in SCRIPTS+(['loss_verify.py']if variant=='candidate'else[]):
            flavor='debug'if name in ['regression_verify.py','regression_irq_verify.py','fault_verify.py','guard_verify.py','mmio_guard_verify.py','new_page_guard_verify.py']else'normal'
            source=debug if flavor=='debug'else normal;d=output/variant/name[:-3];d.mkdir(parents=True)
            for image in ['rf2ship.img','rf2ship.iso']:(d/image).symlink_to((destinations[flavor]/image).resolve())
            for host in ['aead-host.dylib','crypto-oracle']:(d/host).symlink_to(binary_cache/host)
            command(variant+'/'+name,[sys.executable,str(source/name)],d,timeout=240)
        results['variants'][variant]={'sourceSHA256':sha(normal/'console.s'),'clientSHA256':sha(normal/'intent_client.py'),'cryptoSHA256':sha(normal/'aead_reference.c'),'normalImageSHA256':sha(destinations['normal']/'rf2ship.img'),'debugImageSHA256':sha(destinations['debug']/'rf2ship.img')};save()
    manifest=json.loads((snapshot/'SOURCE-MANIFEST.json').read_text())
    results['originalSourceUnchanged']=all(sha(ORIGIN/name)==want for name,want in manifest.items())if SOURCE.is_dir()else None
    results['allPassed']=all(x['passed']for x in rows);save();print(json.dumps({'allPassed':results['allPassed'],'runs':len(rows),'evidence':str(output)}))
    return 0 if results['allPassed']else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--prepared-root',type=Path,default=HERE/'prepared');p.add_argument('--build-only',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    if a.prepare:print(prepare(a.prepared_root))
    else:
        assert a.out,'Select a fresh persistent evidence directory';raise SystemExit(run(a.out,a.prepared_root.resolve(),a.build_only))
