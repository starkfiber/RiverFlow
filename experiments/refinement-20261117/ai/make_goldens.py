"""Controller-only golden sources. Never include these solutions in model prompts."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
HELPERS='''fn emit_begin(out:Writer,format,title,n)
 if format==0
  do writer_text(out,"{\\"title\\":")
  do writer_json(out,title,n)
  do writer_text(out,",\\"fields\\":[")
 else
  do writer_text(out,"<!doctype html><html lang=\\"en\\"><meta charset=\\"utf-8\\"><title>")
  do writer_html(out,title,n)
  do writer_text(out,"</title><main><h1>")
  do writer_html(out,title,n)
  do writer_text(out,"</h1><dl>")
 end
 return 0
end
fn emit_start(out:Writer,format,index,name,n)
 if format==0
  if index
   do writer_text(out,",")
  end
  do writer_text(out,"{\\"name\\":")
  do writer_json(out,name,n)
  do writer_text(out,",\\"value\\":")
 else
  do writer_text(out,"<dt>")
  do writer_html(out,name,n)
  do writer_text(out,"</dt><dd>")
 end
 return 0
end
fn emit_finish(out:Writer,format)
 if format==0
  do writer_text(out,"}")
 else
  do writer_text(out,"</dd>")
 end
 return 0
end
fn emit_number(out:Writer,format,index,name,n,value)
 do emit_start(out,format,index,name,n)
 do writer_number(out,value)
 return emit_finish(out,format)
end
fn emit_text(out:Writer,format,index,name,n,value,m)
 do emit_start(out,format,index,name,n)
 if format==0
  do writer_json(out,value,m)
 else
  do writer_html(out,value,m)
 end
 return emit_finish(out,format)
end
fn emit_end(out:Writer,format)
 if format==0
  do writer_text(out,"]}\\n")
 else
  do writer_text(out,"</dl></main></html>\\n")
 end
 return 0
end
'''
C_HELP='''fn severity_token(p,n,token,m)
 if n<m
  return 0
 end
 if text_equal(p,m,token,m)==0
  return 0
 end
 if n==m
  return 1
 end
 let after=load8(p+m)
 return (after==32)|(after==9)
end
fn severity(data,span:TextSpan)
 let offset=0
 while all(offset<span.length,(load8(data+span.start+offset)==32)|(load8(data+span.start+offset)==9))
  set offset=offset+1
 end
 let p=data+span.start+offset
 let n=span.length-offset
 if severity_token(p,n,"INFO",4)
  return 1
 end
 if severity_token(p,n,"WARN",4)
  return 2
 end
 if severity_token(p,n,"ERROR",5)
  return 3
 end
 return 0
end
'''
C_DECL=''' let cursor=TextCursor(0,0,0,0)
 let span=TextSpan(0,0)
'''
C_BODY=''' let lines=0
 let infos=0
 let warns=0
 let errors=0
 let others=0
 let more=text_next_line(data,n,cursor,span)
 while more
  set lines=lines+1
  let level=severity(data,span)
  if level==1
   set infos=infos+1
  else
   if level==2
    set warns=warns+1
   else
    if level==3
     set errors=errors+1
    else
     set others=others+1
    end
   end
  end
  set more=text_next_line(data,n,cursor,span)
 end
 if cursor.status
  return err(cursor.status)
 end
'''
D_HELP='''fn identifier_valid(data,span:TextSpan)
 if span.length>32
  return 0
 end
 let at=0
 while at<span.length
  let c=load8(data+span.start+at)
  if ((c>=65)&(c<=90))|((c>=48)&(c<=57))|(c==95)|(c==45)
   set at=at+1
  else
   return 0
  end
 end
 return 1
end
fn identifier_seen(data,n,item:TextSpan)
 let prior=TextCursor(0,0,0,0)
 let span=TextSpan(0,0)
 let more=text_next_line(data,n,prior,span)
 while all(more,span.start<item.start)
  if span.length
   if text_equal(data+span.start,span.length,data+item.start,item.length)
    return 1
   end
  end
  set more=text_next_line(data,n,prior,span)
 end
 if prior.status
  return 2
 end
 return 0
end
'''
D_DECL=C_DECL
D_BODY=''' let identifiers=0
 let distinct=0
 let duplicates=0
 let first=0
 let more=text_next_line(data,n,cursor,span)
 while more
  if span.length
   if identifier_valid(data,span)==0
    return err(22)
   end
   set identifiers=identifiers+1
   let seen=identifier_seen(data,n,span)
   if seen==2
    return err(22)
   end
   if seen
    set duplicates=duplicates+1
    if first==0
     set first=cursor.line
    end
   else
    set distinct=distinct+1
   end
  end
  set more=text_next_line(data,n,cursor,span)
 end
 if cursor.status
  return err(cursor.status)
 end
'''
ENTRY='''fn main(argc,argv)
 if argc!=3
  return 2
 end
 let mode=load64(argv+8)
 let format=0
 if text_equal(mode,io_size(mode),"json",4)==0
  if text_equal(mode,io_size(mode),"html",4)==0
   return 2
  end
  set format=1
 end
 handle work(load64(argv+16),format)
 ok value
  return 0
 err cause
  return 2
 end
 return 2
end
'''
def source(task,condition):
    title='Log severity'if task=='C'else'Identifier audit'
    helper=C_HELP if task=='C'else D_HELP;decl=C_DECL if task=='C'else D_DECL;body=C_BODY if task=='C'else D_BODY
    fields=[('Path','path','text'),('Lines','lines','number'),('INFO','infos','number'),('WARN','warns','number'),('ERROR','errors','number'),('Other','others','number')]if task=='C'else[('Path','path','text'),('Identifiers','identifiers','number'),('Distinct','distinct','number'),('Duplicate occurrences','duplicates','number')]
    out=''
    for i,(name,value,kind)in enumerate(fields):
        if condition=='cli':out+=' do report_'+kind+'(report,out,"'+name+'",'+str(len(name))+','+value+(',io_size(path)'if kind=='text'else'')+')\n'
        else:out+=' do emit_'+kind+'(out,format,'+str(i)+',"'+name+'",'+str(len(name))+','+value+(',io_size(path)'if kind=='text'else'')+')\n'
    if task=='D':
        out+=' if first\n'
        out+=('  do report_number(report,out,"First duplicate line",20,first)\n'if condition=='cli'else'  do emit_number(out,format,4,"First duplicate line",20,first)\n')
        out+=' else\n'
        out+=('  do report_text(report,out,"First duplicate line",20,"none",4)\n'if condition=='cli'else'  do emit_text(out,format,4,"First duplicate line",20,"none",4)\n')
        out+=' end\n'
    if condition=='cli':
        return 'profile RF2_SYSTEM_A64_V1\nuse "@rf2/v1/text-report-cli.flow"\n'+helper+'fn text_report_fields(input:TextReportInput,report:Report,out:Writer):IO\n'+decl+' let data=input.data\n let n=input.size\n let path=input.path\n'+body+out+' if out.error\n  return err(out.error)\n end\n return ok(0)\nend\nfn main(argc,argv)\n return text_report_entry(argc,argv,"'+title+'",'+str(len(title))+',0)\nend\n'
    return 'profile RF2_SYSTEM_A64_V1\nuse "@rf2/v1/text.flow"\n'+HELPERS+helper+'fn work(path,format):IO\n let info=TextInfo(0,0,0,0)\n'+decl+' let out=Writer(buffer("golden_output",32768),32768,0,0)\n let data=buffer("golden_input",4097)\n let n=try io_regular(path,data,4096)\n do text_measure(data,n,info)\n if info.status\n  return err(info.status)\n end\n'+body+' do emit_begin(out,format,"'+title+'",'+str(len(title))+')\n'+out+' do emit_end(out,format)\n if out.error\n  return err(out.error)\n end\n do try io_write_no_sigpipe(1,out.data,out.used)\n return ok(0)\nend\n'+ENTRY
if __name__=='__main__':
    for task in ['C','D']:
        for condition in ['manual','cli']:
            p=HERE/('golden-'+task+'-'+condition+'.flow');assert not p.exists();p.write_text(source(task,condition))
