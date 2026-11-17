"""Bounded lexical RF2 repair advice, not a parser, compiler or security gate.

Importing is inert. Only explicit source bytes are inspected; no imports, files,
processes, or network calls are followed. Locations are one-based UTF8 byte columns.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path
MAX_SOURCE=65536
MAX_DIAGNOSTICS=128
TOKEN=re.compile(r'[A-Za-z_][A-Za-z0-9_]*|[^\s]')
IDENT=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
RESERVED={'fn','end','let','set','if','else','while','handle','ok','err','return','do','try','profile','use','result','record'}

def collect(source,*,max_diagnostics=MAX_DIAGNOSTICS):
    if not isinstance(source,bytes)or len(source)>MAX_SOURCE:raise ValueError('Source must be at most 65536 bytes')
    if type(max_diagnostics)is not int or not 1<=max_diagnostics<=MAX_DIAGNOSTICS:raise ValueError('Invalid diagnostic limit')
    text=source.decode('utf-8',errors='strict')
    rows=[];total=0;stack=[];current=None;bindings={};in_string=False;escape=False
    def add(code,line,index,message,original,**extra):
        nonlocal total
        total+=1
        if len(rows)>=max_diagnostics:return
        # Context is bounded and control characters are made visible in JSON.
        prefix=original[:index];column=len(prefix.encode('utf-8'))+1
        context=original[max(0,index-50):index+100]
        rows.append(dict(code=code,line=line,byteColumn=column,function=current,
                         message=message,context=context,advisory=True,**extra))
    for number,original in enumerate(text.split('\n'),1):
        masked=list(original)
        for i,ch in enumerate(original):
            if in_string:
                masked[i]=' '
                if escape:escape=False
                elif ch=='\\':escape=True
                elif ch=='"':in_string=False
            elif ch=='#':
                masked[i:]=[' ']*(len(masked)-i);break
            elif ch=='"':in_string=True;masked[i]=' '
        tokens=[(m.group(),m.start())for m in TOKEN.finditer(''.join(masked))]
        if not tokens:continue
        values=[x[0]for x in tokens];first=values[0]
        if first=='fn':
            current=values[1]if len(values)>1 and IDENT.fullmatch(values[1])else None
            bindings={};stack=['fn'];annotation=None
            # Recognize only one ordinary function header on one line.
            if '('in values and ')'in values:
                start=values.index('(')+1;stop=values.index(')')
                for pos in range(start,stop):
                    if (pos==start or values[pos-1]==',')and IDENT.fullmatch(values[pos]):
                        bindings[values[pos]]={'line':number,'byteColumn':len(original[:tokens[pos][1]].encode())+1}
                if stop+2<len(values)and values[stop+1]==':':annotation=values[stop+2]
            current_info={'annotation':annotation}
            continue
        if current is None:continue
        def bind(pos):
            if pos>=len(values)or not IDENT.fullmatch(values[pos]):return
            name=values[pos];index=tokens[pos][1]
            if name in RESERVED:
                add('RF2A_RESERVED_BINDING',number,index,'Use a non-keyword local name.',original)
            if name in bindings:
                add('RF2A_DUPLICATE_LOCAL',number,index,'Use a distinct function-local binding name; set an existing mutable local instead of declaring it twice.',original,previous=bindings[name])
            else:bindings[name]={'line':number,'byteColumn':len(original[:index].encode())+1}
        if first=='let':bind(1)
        if first in ('ok','err')and 'handle'in stack:bind(1)
        if first=='break':add('RF2A_BREAK',number,tokens[0][1],'RF2 has no break statement. Use an explicit loop condition/scanning flag.',original)
        if first=='else'and len(values)>1 and values[1]=='if':
            add('RF2A_ELSE_IF',number,tokens[1][1],'Place the nested if on the next line and give it its own end.',original)
            stack.append('if')
        if first in ('if','while','handle'):stack.append(first)
        for pos,(value,index)in enumerate(tokens):
            if value=='try'and current_info['annotation']is None:
                add('RF2A_TRY_UNTYPED',number,index,'try requires a compatible result-returning function. In untyped main, handle ok/err explicitly.',original)
            if value in ('and','or')and pos>0 and pos+1<len(values):
                prior=values[pos-1];following=values[pos+1]
                # Avoid declarations, field names, ordinary identifiers/calls.
                if prior not in RESERVED|{'.',',','(' ,'='}and following not in {'(',')',',','.','='}:
                    add('RF2A_BOOLEAN_WORD',number,index,'RF2 does not use word boolean operators. Use all(a,b)/any(a,b) for short circuiting, or &/| when eager evaluation is intended.',original)
        if first=='end':
            if stack:stack.pop()
            if not stack:current=None;bindings={}
    if in_string:add('RF2A_LEXICAL_INCOMPLETE',max(1,len(text.split('\n'))),0,'Unterminated string: advice after its opening quote is incomplete.',text.split('\n')[-1])
    return {'schema':'rf2.ai.repair-context.v1','sourceSHA256':hashlib.sha256(source).hexdigest(),
            'sourceBytes':len(source),'diagnostics':rows,'diagnosticsObserved':total,
            'truncated':total>len(rows),'advisoryOnly':True,'nativeAcceptance':False,
            'scope':'Lexical advice for known RF2 construction mistakes; no full grammar, type/effect check, import resolution, source rewriting or execution.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    with a.source.open('rb')as stream:source=stream.read(MAX_SOURCE+1)
    result=collect(source);raw=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.out:
        with a.out.open('x',encoding='utf-8')as stream:stream.write(raw)
    else:sys.stdout.write(raw)
if __name__=='__main__':main()
