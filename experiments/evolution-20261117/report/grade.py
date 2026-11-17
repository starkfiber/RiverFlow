"""Fixed independent full-task oracle, used unchanged for model and reference apps."""
import argparse,hashlib,html,json,os,subprocess
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);binary=str(a.binary.resolve())
    rows=[]
    def run(args,want=None):
        p=subprocess.run([binary,*map(str,args)],capture_output=True,timeout=10)
        okay=(p.returncode==0 and p.stdout==want)if want is not None else(p.returncode!=0 and not p.stdout)
        rows.append({'arguments':list(map(str,args)),'passed':okay,'exit':p.returncode,'stdoutSHA256':hashlib.sha256(p.stdout).hexdigest(),'expectedSHA256':hashlib.sha256(want).hexdigest()if want is not None else None});return p
    samples=[b'',b'one two\nthree',b'quote"\\<>&\'\t\r\n', 'café 中 😀\nend'.encode(),b'a'*4096,b' '*4096]
    for i,raw in enumerate(samples):
        path=d/f'file-{i}-<&\".txt';path.write_bytes(raw);text=raw.decode();words=len(__import__('re').findall(r'[^\x09\x0a\x0d\x20]+',text))
        fields=[('Path',str(path)),('Text',text),('Bytes',len(raw)),('Words',words)]
        want=(json.dumps({'title':'File summary','fields':[{'name':k,'value':v}for k,v in fields]},ensure_ascii=False,separators=(',',':'))+'\n').encode()
        run(['json',path],want)
        e=lambda s:html.escape(str(s),quote=True).replace('&#x27;','&#39;')
        want=('<!doctype html><html lang="en"><meta charset="utf-8"><title>File summary</title><main><h1>File summary</h1><dl>'+''.join(f'<dt>{k}</dt><dd>{e(v)}</dd>'for k,v in fields)+'</dl></main></html>\n').encode()
        run(['html',path],want)
    for i,raw in enumerate([b'\xff',b'\xc0\x80',b'\x01',b'\x00',b'x'*4097,b'\xed\xa0\x80']):
        path=d/f'bad-{i}';path.write_bytes(raw)
        for fmt in ['json','html']:run([fmt,path])
    for args in [[],['json'],['JSON',d/'file-0'],['x',d/'file-0'],['json',d/'missing'],['html',d],['json',d/'file-0','extra']]:run(args)
    symlink=d/'link';symlink.symlink_to(d/'file-0-<&".txt');run(['json',symlink])
    fifo=d/'fifo';os.mkfifo(fifo);run(['json',fifo])
    for fmt in ['json','html']:
        with open('/dev/null','rb')as target:
            p=subprocess.run([binary,fmt,str(d/'file-1-<&".txt')],stdout=target,stderr=subprocess.PIPE,timeout=10)
        rows.append({'case':'output-fault-'+fmt,'passed':p.returncode!=0,'exit':p.returncode})
        readfd,writefd=os.pipe();os.close(readfd)
        try:p=subprocess.run([binary,fmt,str(d/'file-1-<&".txt')],stdout=writefd,stderr=subprocess.PIPE,timeout=10)
        finally:os.close(writefd)
        rows.append({'case':'broken-pipe-'+fmt,'passed':p.returncode>0,'exit':p.returncode})
    result={'schema':'rf2.complete-report.grade.v1','passed':sum(x['passed']for x in rows),'total':len(rows),'binarySHA256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'cases':rows}
    (d/'RESULTS.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='cases'}));return 0 if all(x['passed']for x in rows)else 1
if __name__=='__main__':raise SystemExit(main())
