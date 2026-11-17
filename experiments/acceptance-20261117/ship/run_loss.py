"""Fresh actual guest loss/reconnect acceptance; preserves red/green separately."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('acceptance',HERE/'run_acceptance.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--fixed',action='store_true',help='Compatibility alias; fixed is now the default');p.add_argument('--original-policy',action='store_true');p.add_argument('--prepared-root',type=Path,default=HERE/'prepared');p.add_argument('--host-only',action='store_true');args=p.parse_args()
    assert os.environ.get('TMPDIR','').startswith('/Volumes/Mac Work Cache/')
    output=args.out.resolve();output.mkdir(parents=True,exist_ok=False)
    cache=Path(os.environ['TMPDIR'])/('loss-'+output.name);cache.mkdir(exist_ok=False)
    source=HERE/('loss-source-'+output.name);shutil.copytree(args.prepared_root/'candidate-normal',source,ignore=shutil.ignore_patterns('__pycache__'))
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.update(RF2_SHIP_CACHE=str(cache),RF2_SHIP_EVIDENCE=str(output))
    if args.host_only:
        rows=[]
        for variant in ['baseline','candidate']:
            original=args.prepared_root/(variant+'-normal');d=output/variant;d.mkdir();env['RF2_SHIP_EVIDENCE']=str(d)
            lib=cache/(variant+'.dylib');oracle=cache/(variant+'-oracle')
            subprocess.run(['clang','-O2','-ffreestanding','-fno-builtin','-dynamiclib',str(original/'aead_reference.c'),'-o',str(lib)],check=True)
            subprocess.run(['swiftc','-O',str(original/'CryptoOracle.swift'),'-o',str(oracle)],check=True)
            (d/'aead-host.dylib').symlink_to(lib);(d/'crypto-oracle').symlink_to(oracle)
            script=source/(variant+'-crypto_verify.py');script.write_text(a.adapt_test((HERE/'snapshot/original/crypto_verify.py').read_text(),original))
            with(d/'RUN.log').open('wb')as log:q=subprocess.run([sys.executable,str(script)],cwd=ROOT,env=env,stdout=log,stderr=log,timeout=60)
            rows.append({'variant':variant,'passed':q.returncode==0,'exit':q.returncode,'scriptSHA256':a.sha(script)});print(variant,q.returncode,flush=True)
        (output/'RESULTS.json').write_text(json.dumps({'schema':'rf2ship.host-replay.v1','rows':rows,'allPassed':all(r['passed']for r in rows),'reason':'Initial host checks executed900each but receipt used old relative source path; corrected path only'},indent=2));return 0 if all(r['passed']for r in rows)else 1
    client=source/'intent_client.py';before=a.sha(client)
    if not args.original_policy:
        assert a.sha(HERE/'intent_client.py')=='ba26053fd5453235fa1161094dfa5cefacd5f7f642e632f36523950a729e74a2'
        client.write_bytes((HERE/'intent_client.py').read_bytes())
    else:
        client.write_bytes((HERE/'snapshot/original/intent_client.py').read_bytes())
    s=a.loss_test(source)
    (source/'loss_verify.py').write_text(s);(source/'build.py').write_text(a.adapt_build((HERE/'snapshot/original/build.py').read_text(),source))
    a.encode(source,cache)
    with(output/'BUILD.log').open('wb')as log:subprocess.run([sys.executable,str(source/'build.py'),str(output),str(source)],cwd=ROOT,env=env,stdout=log,stderr=log,check=True,timeout=60)
    t=time.monotonic()
    with(output/'RUN.log').open('wb')as log:q=subprocess.run([sys.executable,str(source/'loss_verify.py')],cwd=ROOT,env=env,stdout=log,stderr=log,timeout=120)
    result={'schema':'rf2ship.loss-controls.v1','fixedTimeoutPolicy':not args.original_policy,'clientBeforeSHA256':before,'clientAfterSHA256':a.sha(client),'guestCryptoSHA256':a.sha(source/'aead_reference.c'),'guestImageSHA256':a.sha(output/'rf2ship.img'),'scriptSHA256':a.sha(source/'loss_verify.py'),'fixtureSHA256':a.sha(HERE/'loss_cases.py.in'),'exit':q.returncode,'elapsedSeconds':round(time.monotonic()-t,3),'passed':q.returncode==0,'scope':'Real local guest requests/replies; controller-owned intentional drop/delay, not physical loss'}
    (output/'RESULTS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return q.returncode
if __name__=='__main__':raise SystemExit(main())
