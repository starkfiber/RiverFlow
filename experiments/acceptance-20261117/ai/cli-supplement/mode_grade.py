"""Task A CLI short/suffix mode supplement, separate from the frozen task oracle."""
from pathlib import Path
import argparse,hashlib,html,json,subprocess,errno

def main():
    p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);f=d/'input';f.write_bytes(b'a');rows=[];unavailable=[]
    for mode in [b'',b'j',b'js',b'jso',b'jsonx',b'json ',b' json',b'h',b'ht',b'htm',b'htmlx',b'html ',b'HTML',b'\xff']:
        q=subprocess.run([str(a.binary.resolve()).encode(),mode,str(f).encode()],capture_output=True,timeout=5);rows.append({'case':'invalid-mode-'+mode.hex(),'passed':q.returncode>0 and not q.stdout,'exit':q.returncode,'stdoutHex':q.stdout.hex()})
    fields=[('Path',str(f)),('Lines',1),('Words',1),('Longest bytes',1)]
    js=(json.dumps({'title':'Line metrics','fields':[{'name':k,'value':v}for k,v in fields]},ensure_ascii=False,separators=(',',':'))+'\n').encode()
    esc=lambda x:html.escape(str(x),quote=True).replace('&#x27;','&#39;')
    ht=('<!doctype html><html lang="en"><meta charset="utf-8"><title>Line metrics</title><main><h1>Line metrics</h1><dl>'+''.join('<dt>'+k+'</dt><dd>'+esc(v)+'</dd>'for k,v in fields)+'</dl></main></html>\n').encode()
    for mode,wanted in [('json',js),('html',ht)]:
        q=subprocess.run([str(a.binary.resolve()),mode,str(f)],capture_output=True,timeout=5);rows.append({'case':'valid-'+mode,'passed':q.returncode==0 and q.stdout==wanted,'exit':q.returncode,'stdoutHex':q.stdout.hex()})
    invalid_path=str(d).encode()+b'/invalid-path-\xff'
    try:
        with open(invalid_path,'wb')as invalid:invalid.write(b'a')
    except OSError as e:
        if e.errno!=errno.EILSEQ:raise
        unavailable.append({'fixture':'invalid-UTF8-existing-path','reason':'Host filesystem refuses invalid UTF8 filename','errno':e.errno,'countedAsPass':False})
    else:
        for fmt in [b'json',b'html']:
            q=subprocess.run([str(a.binary.resolve()).encode(),fmt,invalid_path],capture_output=True,timeout=5);rows.append({'case':'invalid-UTF8-path-'+fmt.decode(),'passed':q.returncode>0 and not q.stdout,'exit':q.returncode,'stdoutHex':q.stdout.hex()})
    result={'schema':'rf2.cli-mode-supplement.v1','binarySHA256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'allPassed':all(x['passed']for x in rows),'total':len(rows),'passed':sum(x['passed']for x in rows),'cases':rows,'unavailableFixtures':unavailable};(d/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='cases'}));return 0 if result['allPassed']else 1
if __name__=='__main__':raise SystemExit(main())
