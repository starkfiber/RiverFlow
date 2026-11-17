"""Independent complete-task C/D oracle: exact bytes, refusal and real IO faults."""
from pathlib import Path
import argparse,hashlib,html,json,os,random,re,subprocess

def physical_lines(raw):
    start=0
    for at,c in enumerate(raw):
        if c==10:
            yield raw[start:at].removesuffix(b'\r');start=at+1
    if start<len(raw):yield raw[start:]
def fields(task,path,raw):
    lines=list(physical_lines(raw))
    if task=='C':
        counts={b'INFO':0,b'WARN':0,b'ERROR':0,b'Other':0}
        for line in lines:
            match=re.match(rb'^[ \t]*(INFO|WARN|ERROR)(?:[ \t]|$)',line)
            counts[match[1]if match else b'Other']+=1
        assert sum(counts.values())==len(lines)
        return [('Path',str(path)),('Lines',len(lines)),*((key.decode(),counts[key])for key in counts)]
    seen=set();total=0;duplicates=0;first=None
    for number,line in enumerate(lines,1):
        if not line:continue
        if re.fullmatch(rb'[A-Z0-9_-]{1,32}',line)is None:raise ValueError('identifier refusal')
        total+=1
        if line in seen:
            duplicates+=1
            if first is None:first=number
        else:seen.add(line)
    assert total==len(seen)+duplicates
    return [('Path',str(path)),('Identifiers',total),('Distinct',len(seen)),('Duplicate occurrences',duplicates),('First duplicate line',first if first is not None else'none')]
def expected(task,path,raw):
    title='Log severity'if task=='C'else'Identifier audit';fs=fields(task,path,raw)
    js=(json.dumps({'title':title,'fields':[{'name':k,'value':v}for k,v in fs]},ensure_ascii=False,separators=(',',':'))+'\n').encode()
    escape=lambda s:html.escape(str(s),quote=True).replace('&#x27;','&#39;')
    ht=(f'<!doctype html><html lang="en"><meta charset="utf-8"><title>{title}</title><main><h1>{title}</h1><dl>'+''.join('<dt>'+k+'</dt><dd>'+escape(v)+'</dd>'for k,v in fs)+'</dl></main></html>\n').encode()
    return {'json':js,'html':ht}
def cases(task):
    if task=='C':
        samples=[b'',b'\n',b'\n\n',b'INFO',b'WARN\nERROR\nINFO\n',b' INFO hello\n\tWARN\tmessage\nERROR detail\n',b'INFO:\nINFORMATION\nwarn\n00:00 ERROR\n\n',b'INFO\r\nWARN\r\nERROR\r',b'INFO\r',b'\r\n',b' \t \n\t',b'ERRORx\nERROR\t\nERROR \n', 'INFO café\nWARN 中\nERROR 😀\nINFO\u00a0x\nINFO \u00a0x'.encode(),b'<>&"\\\'\n',b'x'*4096,b'\n'*4096,b'INFO\n'*819+b'X',b'\x7f']
        rng=random.Random(61117);tokens=[b'INFO x',b' WARN',b'\tERROR\ty',b'INFO:',b'unknown',b'',b'warn',b'ERRORz']
        samples+=[b'\n'.join(rng.choice(tokens)for _ in range(37))+tail for tail in [b'',b'\n',b'\r\n']]
        invalid=[]
    else:
        samples=[b'',b'\n',b'\r\n\n',b'A',b'A\nB\nC\n',b'A\n\nB\nA\nB\nA',b'\n\nA\r\nB\n\nA\r\n',b'A\nA\nA\n',b'0\n_\n-\nA0_-\nA0_-',b'A'*32,b'A'*32+b'\n'+b'A'*31+b'B\n'+b'A'*32,b'A\n'*2048,b'\n'*4096,b'X\nY\nZ\nY\nX\nZ',b'\r\nA\r\n\r\nA',b'\nA\n\nA\n']
        samples+=[b'\n'.join(('%X'%i).encode()for i in range(900))]
        rng=random.Random(61118);ids=[b'A',b'B',b'AB',b'BA',b'_',b'-',b'ID-01',b'']
        samples+=[b'\n'.join(rng.choice(ids)for _ in range(61))+tail for tail in [b'',b'\n',b'\r\n']]
        invalid=[b'A'*33,b'a',b'A B',b' A',b'A ',b'\t',b'A\tB',b'A\r',b'A\nB\ninvalid',b'A\nA\n!',b'\r',b'ID.1',b'ID/1','中'.encode(),'Ａ'.encode(),b'A\n'*2047+b'a\n']
    invalid +=[b'\xff',b'\xc0\x80',b'\xed\xa0\x80',b'\xf4\x90\x80\x80',b'\xe2\x82',b'\x00',b'\x01',b'\x0b',b'\x1f',b'X'*4097]
    assert all(len(x)<=4096 for x in samples)
    return samples,invalid

def main():
    p=argparse.ArgumentParser();p.add_argument('task',choices=['C','D']);p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False);binary=str(a.binary.resolve());rows=[]
    def run(label,args,wanted=None):
        try:q=subprocess.run([binary,*args],capture_output=True,timeout=8);code=q.returncode;stdout=q.stdout;stderr=q.stderr
        except subprocess.TimeoutExpired:code=-999;stdout=b'';stderr=b'controller timeout'
        passed=(code==0 and stdout==wanted)if wanted is not None else(code>0 and not stdout)
        rows.append({'case':label,'passed':passed,'exit':code,'stdoutHex':stdout[:1600].hex(),'expectedHex':wanted[:1600].hex()if wanted is not None else None,'stderr':stderr[:300].decode(errors='replace')})
    valid,invalid=cases(a.task)
    for i,raw in enumerate(valid):
        path=d/('valid-'+str(i)+'-<&"\'中😀');path.write_bytes(raw);wanted=expected(a.task,path,raw)
        for mode in ['json','html']:run('valid-'+str(i)+'-'+mode,[mode,str(path)],wanted[mode])
    for i,raw in enumerate(invalid):
        path=d/('invalid-'+str(i));path.write_bytes(raw)
        for mode in ['json','html']:run('invalid-'+str(i)+'-'+mode,[mode,str(path)])
    good=d/'good';good.write_bytes(b'A')
    for mode in ['', 'j','js','jso','jsonx','json ',' json','h','ht','htm','htmlx','HTML',b'\xff']:
        run('invalid-mode-'+repr(mode),[mode,str(good)])
    for label,args in [('noargs',[]),('fewargs',['json']),('extra',['json',str(good),'extra']),('missing',['json',str(d/'missing')]),('directory',['html',str(d)])]:run(label,args)
    link=d/'link';link.symlink_to(good);run('symlink',['json',str(link)])
    fifo=d/'fifo';os.mkfifo(fifo);run('fifo',['html',str(fifo)])
    for mode in ['json','html']:
        with open('/dev/null','rb')as target:q=subprocess.run([binary,mode,str(good)],stdout=target,stderr=subprocess.PIPE,timeout=8)
        rows.append({'case':mode+'-readonly-stdout','passed':q.returncode>0,'exit':q.returncode})
        rd,wr=os.pipe();os.close(rd)
        try:q=subprocess.run([binary,mode,str(good)],stdout=wr,stderr=subprocess.PIPE,timeout=8)
        finally:os.close(wr)
        rows.append({'case':mode+'-broken-pipe','passed':q.returncode>0,'exit':q.returncode})
    result={'schema':'rf2.refinement.complete-task-grade.v1','task':a.task,'allPassed':all(x['passed']for x in rows),'passed':sum(x['passed']for x in rows),'total':len(rows),'binarySHA256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'oracleSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':rows,'scope':'Synthetic bounded native functional/refusal/IO acceptance, not production or hardware certification'}
    (d/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='cases'}));return 0 if result['allPassed']else 1
if __name__=='__main__':raise SystemExit(main())
