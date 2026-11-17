"""Small reviewed parser-only transform; all other lease logic remains intact."""
import hashlib
def apply(text):
    start=text.index('  if ended==1\n')
    end=text.index('\n end\n if any(ended==0',start)
    block=text[start:end]
    prefix='  if ended==1\n   if kind!=0\n    return 10\n   end\n  else\n'
    if not block.startswith(prefix)or not block.endswith('\n  end'):raise ValueError('Parser source shape drifted; review before applying')
    core=block[len(prefix):-len('\n  end')]
    core='\n'.join(line[1:]if line.startswith(' ')else line for line in core.split('\n'))
    if core.count('   set ended=1')!=1:raise ValueError('END branch shape drifted')
    core=core.replace('   set ended=1','''   set ended=1
   # END switches permanently to padding validation; no parser redispatch.
   while i<n
    if p[i]!=0
     return 10
    end
    set i=i+1
   end''',1)
    return text[:start]+core+text[end:]
