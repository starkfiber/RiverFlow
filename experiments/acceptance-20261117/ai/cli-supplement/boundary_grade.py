"""Independent supplemental CLI boundaries. Uses existing reviewed binaries only."""
from pathlib import Path
import argparse,hashlib,html,json,os,subprocess,errno

def main():
    p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True,help='Reviewed task B CLI reference');p.add_argument('--callback-error',type=Path);p.add_argument('--writer-error',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);source=d/'input';source.write_bytes(b'a'*256);rows=[];unavailable=[]
    def run(label,args,wanted=None,binary=None):
        q=subprocess.run([bytes(str((binary or a.binary).resolve()),'utf8'),*args],capture_output=True,timeout=5)
        okay=q.returncode==0 and q.stdout==wanted if wanted is not None else q.returncode>0 and not q.stdout
        rows.append({'case':label,'passed':okay,'exit':q.returncode,'stdoutHex':q.stdout[:1600].hex(),'expectedHex':wanted[:1600].hex()if wanted is not None else None})
    path=str(source).encode()
    for mode in [b'',b'j',b'js',b'jso',b'jsonx',b'json ',b' json',b'h',b'ht',b'htm',b'htmlx',b'html ',b'HTML',b'\xff']:
        run('invalid-mode-'+mode.hex(),[mode,path,b'a'])
    for query in [b'a'*127,b'a'*128,('😀'*32).encode()]:
        text=query.decode();hits=max(0,257-len(query))if query.startswith(b'a')else 0
        fields=[('Path',str(source)),('Query',text),('Matches',hits),('First byte',0 if hits else'none'),('Last byte',hits-1 if hits else'none')]
        js=(json.dumps({'title':'Match metrics','fields':[{'name':k,'value':v}for k,v in fields]},ensure_ascii=False,separators=(',',':'))+'\n').encode()
        esc=lambda x:html.escape(str(x),quote=True).replace('&#x27;','&#39;')
        ht=('<!doctype html><html lang="en"><meta charset="utf-8"><title>Match metrics</title><main><h1>Match metrics</h1><dl>'+''.join('<dt>'+k+'</dt><dd>'+esc(v)+'</dd>'for k,v in fields)+'</dl></main></html>\n').encode()
        for fmt,want in [(b'json',js),(b'html',ht)]:run('valid-query-bytes-'+str(len(query))+'-'+fmt.decode()+'-'+query[:4].hex(),[fmt,path,query],want)
    for query in [b'',b'a'*129,b'a'+('😀'*32).encode(),b'\xff',b'\xc0\x80',b'\xed\xa0\x80',b'\xf4\x90\x80\x80',b'\xe2\x82',b'\x01']:
        run('invalid-query-'+query[:12].hex()+'-'+str(len(query)),[b'json',path,query])
    for raw in [b'\xf4\x90\x80\x80',b'\xe2\x82',b'\x80',b'\xc0\x80',b'\xed\xa0\x80',b'\x00',b'\x1f']:
        source.write_bytes(raw);run('invalid-input-'+raw.hex(),[b'json',path,b'a'])
    source.write_bytes(b'a')
    invalid_path=str(d).encode()+b'/invalid-path-\xff'
    try:
        with open(invalid_path,'wb')as f:f.write(b'a')
    except OSError as e:
        if e.errno!=errno.EILSEQ:raise
        unavailable.append({'fixture':'invalid-UTF8-existing-path','reason':'Host filesystem refuses invalid UTF8 filename','errno':e.errno,'countedAsPass':False})
    else:
        for fmt in [b'json',b'html']:run('invalid-UTF8-path-'+fmt.decode(),[fmt,invalid_path,b'a'])
    for label,binary in [('callback-error',a.callback_error),('writer-error',a.writer_error)]:
        if binary:
            for fmt in [b'json',b'html']:run(label+'-'+fmt.decode(),[fmt,path],binary=binary)
    result={'schema':'rf2.cli-boundary-supplement.v1','allPassed':all(x['passed']for x in rows),'passed':sum(x['passed']for x in rows),'total':len(rows),'binaries':{label:hashlib.sha256(p.read_bytes()).hexdigest()for label,p in [('taskB',a.binary),('callbackError',a.callback_error),('writerError',a.writer_error)]if p},'cases':rows,'unavailableFixtures':unavailable,'scope':'Supplemental independent boundary fixtures, not a changed frozen task grader'}
    (d/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='cases'}));return 0 if result['allPassed']else 1
if __name__=='__main__':raise SystemExit(main())
