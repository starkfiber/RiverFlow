"""Independent native complete-task oracle: text and byte semantics, real IO faults."""
import argparse,hashlib,html,json,os,re,subprocess
from pathlib import Path
def expected(task,path,raw,query=''):
    if task=='A':
        lines=raw.split(b'\n')
        lengths=[len(x[:-1]if x.endswith(b'\r')else x)for x in lines[:-1]]
        if lines[-1]:lengths.append(len(lines[-1]))
        fields=[('Path',str(path)),('Lines',raw.count(b'\n')+int(bool(raw)and not raw.endswith(b'\n'))),('Words',len(re.findall(rb'[^\x09\x0a\x0d\x20]+',raw))),('Longest bytes',max(lengths,default=0))]
    else:
        qb=query.encode();hits=[i for i in range(len(raw)-len(qb)+1)if raw[i:i+len(qb)]==qb]
        fields=[('Path',str(path)),('Query',query),('Matches',len(hits)),('First byte',hits[0]if hits else'none'),('Last byte',hits[-1]if hits else'none')]
    title='Line metrics'if task=='A'else'Match metrics'
    js=(json.dumps({'title':title,'fields':[{'name':k,'value':v}for k,v in fields]},ensure_ascii=False,separators=(',',':'))+'\n').encode()
    e=lambda s:html.escape(str(s),quote=True).replace('&#x27;','&#39;')
    ht=(f'<!doctype html><html lang="en"><meta charset="utf-8"><title>{title}</title><main><h1>{title}</h1><dl>'+''.join(f'<dt>{k}</dt><dd>{e(v)}</dd>'for k,v in fields)+'</dl></main></html>\n').encode()
    return {'json':js,'html':ht}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('task',choices=['A','B']);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);binary=str(a.binary.resolve());rows=[]
    def run(label,args,want=None):
        try:p=subprocess.run([binary,*args],capture_output=True,timeout=5);rc=p.returncode;out=p.stdout;err=p.stderr
        except subprocess.TimeoutExpired:rc=-999;out=b'';err=b'timeout'
        okay=(rc==0 and out==want)if want is not None else(rc>0 and not out)
        rows.append({'case':label,'passed':okay,'exit':rc,'stdout':out[:1200].decode(errors='replace'),'expected':want[:1200].decode(errors='replace')if want is not None else'nonzero exit; no stdout','stderr':err[:500].decode(errors='replace')})
    samples=[b'',b'a',b'\n',b'\n\n',b'a\r\nb\r',b'a\rb\n',b' a\t b\n\r\n', 'café 中 😀\n中'.encode(),b'aaaa',b'quote"\\<>&\'\r\n',b'a'*4096]
    queries=['a','aa','中','not present','"','\n']if a.task=='B'else['']
    for i,raw in enumerate(samples):
        path=d/f'file-{i}-<&\"';path.write_bytes(raw)
        for query in queries:
            wanted=expected(a.task,path,raw,query)
            for fmt in ['json','html']:run(f'valid-{i}-{fmt}-{query!r}',[fmt,str(path)]+([query]if a.task=='B'else[]),wanted[fmt])
    for i,raw in enumerate([b'\xff',b'\xc0\x80',b'\xed\xa0\x80',b'\x01',b'\x00',b'x'*4097]):
        path=d/f'bad-{i}';path.write_bytes(raw)
        for fmt in ['json','html']:run(f'invalid-{i}-{fmt}',[fmt,str(path)]+(['a']if a.task=='B'else[]))
    path=str(d/'file-8-<&"');tail=['a']if a.task=='B'else[]
    for label,args in [('noargs',[]),('fewargs',['json']),('badmode',['JSON',path]+tail),('extra',['json',path]+tail+['extra']),('missing',['json',str(d/'missing')]+tail),('directory',['html',str(d)]+tail)]:run(label,args)
    link=d/'symlink';link.symlink_to(path);run('symlink',['json',str(link)]+tail)
    fifo=d/'fifo';os.mkfifo(fifo);run('fifo',['json',str(fifo)]+tail)
    if a.task=='B':
        for query in ['', 'a'*129,'\x01','\tbad\x02']:run('invalid-query-'+repr(query),['json',path,query])
    for fmt in ['json','html']:
        with open('/dev/null','rb')as target:p=subprocess.run([binary,fmt,path]+tail,stdout=target,stderr=subprocess.PIPE,timeout=5)
        rows.append({'case':fmt+'-readonly-stdout','passed':p.returncode>0,'exit':p.returncode})
        rd,wr=os.pipe();os.close(rd)
        try:p=subprocess.run([binary,fmt,path]+tail,stdout=wr,stderr=subprocess.PIPE,timeout=5)
        finally:os.close(wr)
        rows.append({'case':fmt+'-broken-pipe','passed':p.returncode>0,'exit':p.returncode})
    result={'schema':'rf2.useful-output.grade.v1','task':a.task,'passed':sum(x['passed']for x in rows),'total':len(rows),'allPassed':all(x['passed']for x in rows),'binarySHA256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'cases':rows}
    (d/'RESULTS.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='cases'}));return 0 if result['allPassed']else 1
if __name__=='__main__':raise SystemExit(main())
