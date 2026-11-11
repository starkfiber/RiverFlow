#!/usr/bin/env python3
"""RF2_SYSTEM_A64_V1 seed: direct AArch64/Mach-O encoding, no C/assembler/linker.
Build-time Python only. The emitted executable has no language runtime imports.
This trusted bootstrap is not a self-hosted compiler or a general Core backend.
"""
import ast, hashlib, json, re, struct, subprocess, sys
from pathlib import Path
BASE=0x100000000
PAGE=16384
class Compiler:
 def __init__(self):self.words=[];self.labels={};self.fix=[];self.data=bytearray();self.objects={};self.functions={};self.unique=0;self.object_sizes={}
 def emit(self,w):self.words.append(w)
 def label(self,s):
  if s in self.labels:raise ValueError('Duplicate label '+s)
  self.labels[s]=len(self.words)*4
 def fresh(self):self.unique+=1;return 'L'+str(self.unique)
 def jump(self,label,cond=None):
  self.fix.append((len(self.words),label,'branch' if cond is None else 'cond'));self.emit(0x14000000 if cond is None else 0x54000000|cond)
 def call(self,name):self.fix.append((len(self.words),name,'branch'));self.emit(0x94000000)
 def imm(self,r,n):
  n&=(1<<64)-1;self.emit(0xd2800000|((n&65535)<<5)|r)
  for i in range(1,4):
   v=(n>>(16*i))&65535
   if v:self.emit(0xf2800000|(i<<21)|(v<<5)|r)
 def mov(self,r,s):self.emit(0xaa0003e0|(s<<16)|r)
 def obj(self,key,data=None,size=0):
  if key in self.objects and data is None and self.object_sizes[key]!=size:raise ValueError('Inconsistent buffer size '+key)
  if key not in self.objects:
   self.data+=b'\0'*((-len(self.data))%8);self.objects[key]=len(self.data);self.data+=data if data is not None else bytes(size);self.object_sizes[key]=len(data) if data is not None else size
  return key
 def address(self,r,key):
  self.fix.append((len(self.words),key,'address'));self.emit(0x90000000|r);self.emit(0x91000000|(r<<5)|r)
 def local(self,r,name,store=False):
  off=self.locals[name]*8
  self.emit((0xf9000000 if store else 0xf9400000)|((off//8)<<10)|(29<<5)|r)
 def push(self):self.emit(0xd10043ff);self.emit(0xf90003e0)
 def pop1(self):self.emit(0xf94003e1);self.emit(0x910043ff)
 def expr(self,node):
  if isinstance(node,str):node=ast.parse(node,mode='eval').body
  if isinstance(node,ast.Constant):
   if type(node.value) is int:self.imm(0,node.value)
   elif isinstance(node.value,str):self.address(0,self.obj('str:'+node.value,node.value.encode()+b'\0'))
   else:raise ValueError('Unsupported literal')
  elif isinstance(node,ast.Name):self.local(0,node.id)
  elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.Invert)):
   self.expr(node.operand);self.emit(0xcb0003e0 if isinstance(node.op,ast.USub) else 0xaa2003e0)
  elif isinstance(node,(ast.BinOp,ast.Compare)):
   left=node.left;right=node.right if isinstance(node,ast.BinOp) else node.comparators[0]
   if isinstance(node,ast.Compare) and len(node.ops)!=1:raise ValueError('One comparison at a time')
   self.expr(left);self.push();self.expr(right);self.pop1()
   if isinstance(node,ast.Compare):
    # Unsigned 64-bit comparisons; raw negative syscall returns must be checked against 2^63.
    cond={ast.Eq:0,ast.NotEq:1,ast.Lt:3,ast.GtE:2,ast.Gt:8,ast.LtE:9}[type(node.ops[0])]
    self.emit(0xeb00003f);self.emit(0x9a9f07e0|((cond^1)<<12))
   else:
    op=type(node.op)
    codes={ast.Add:0x8b000020,ast.Sub:0xcb000020,ast.Mult:0x9b007c20,ast.BitAnd:0x8a000020,ast.BitOr:0xaa000020,ast.BitXor:0xca000020,ast.LShift:0x9ac02020,ast.RShift:0x9ac02420,ast.FloorDiv:0x9ac00820}
    if op not in codes:raise ValueError('Unsupported operator')
    self.emit(codes[op])
  elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
   name=node.func.id
   if node.keywords or len(node.args)>8:raise ValueError('Positional arity limit')
   if name=='buffer':
    if len(node.args)!=2:raise ValueError('buffer arity')
    key=ast.literal_eval(node.args[0]);size=ast.literal_eval(node.args[1]);self.address(0,self.obj('buf:'+key,size=size));return
   expected={'load8':1,'load32':1,'load64':1,'store8':2,'store32':2,'store64':2,'read':3,'write':3,'open':3,'close':1,'exit':1}.get(name)
   if expected is not None and len(node.args)!=expected:raise ValueError('Builtin arity')
   for a in node.args:self.expr(a);self.push()
   for i in range(len(node.args)-1,-1,-1):self.emit(0xf94003e0|i);self.emit(0x910043ff)
   if name in ('load8','load32','load64'):self.emit({'load8':0x39400000,'load32':0xb9400000,'load64':0xf9400000}[name])
   elif name in ('store8','store32','store64'):self.emit({'store8':0x39000001,'store32':0xb9000001,'store64':0xf9000001}[name])
   elif name in ('read','write','open','close','exit'):
    self.imm(16,{'read':3,'write':4,'open':5,'close':6,'exit':1}[name]);self.emit(0xd4001001)
    skip=self.fresh();self.jump(skip,3);self.emit(0xcb0003e0);self.label(skip)
   else:
    if name not in self.functions or self.functions[name]!=len(node.args):raise ValueError('Unknown function/arity '+name)
    self.call(name)
  else:raise ValueError('Unsupported expression '+ast.dump(node))
 def block(self,lines,pos=0):
  while pos<len(lines):
   line=lines[pos];pos+=1
   if line in ('end','else'):return pos,line
   if line.startswith(('let ','set ')):
    name,expr=line[4:].split(' = ',1);self.expr(expr);self.local(0,name,True)
   elif line.startswith('do '):self.expr(line[3:])
   elif line.startswith('return '):self.expr(line[7:]);self.jump(self.end)
   elif line.startswith('if '):
    other=self.fresh();done=self.fresh();self.expr(line[3:]);self.emit(0xf100001f);self.jump(other,0)
    pos,stop=self.block(lines,pos)
    if stop=='else':self.jump(done);self.label(other);pos,stop=self.block(lines,pos);self.label(done)
    else:self.label(other)
    if stop!='end':raise ValueError('Missing if end')
   elif line.startswith('while '):
    start=self.fresh();done=self.fresh();self.label(start);self.expr(line[6:]);self.emit(0xf100001f);self.jump(done,0);pos,stop=self.block(lines,pos)
    if stop!='end':raise ValueError('Missing while end')
    self.jump(start);self.label(done)
   else:raise ValueError('Unsupported statement '+line)
  return pos,None
 def compile(self,source):
  lines=[s.strip() for s in source.splitlines() if s.strip() and not s.strip().startswith('#')]
  if lines.pop(0)!='profile RF2_SYSTEM_A64_V1':raise ValueError('Explicit machine profile required')
  groups=[];i=0
  while i<len(lines):
   m=re.fullmatch(r'fn ([a-zA-Z_][a-zA-Z_0-9]*)\((.*?)\)',lines[i]);i+=1
   if not m:raise ValueError('Expected fn')
   name,params=m.groups();params=[p.strip() for p in params.split(',') if p.strip()];depth=1;body=[]
   while i<len(lines):
    l=lines[i];i+=1
    if l.startswith(('if ','while ')):depth+=1
    if l=='end':depth-=1
    if not depth:break
    body.append(l)
   if depth or name in self.functions or len(params)>8:raise ValueError('Invalid function')
   self.functions[name]=len(params);groups.append((name,params,body))
  if self.functions.get('main')!=2:raise ValueError('main needs argc, argv')
  self.label('_start');self.call('main');self.imm(16,1);self.emit(0xd4001001)
  for name,params,body in groups:
   self.label(name);self.locals={p:i for i,p in enumerate(params)}
   for l in body:
    if l.startswith('let '):
     n=l[4:].split(' = ',1)[0]
     if not re.fullmatch(r'[a-zA-Z_][a-zA-Z_0-9]*',n) or n in self.locals:raise ValueError('Duplicate/invalid local '+n)
     self.locals[n]=len(self.locals)
   for l in body:
    if l.startswith('set ') and l[4:].split(' = ',1)[0] not in self.locals:raise ValueError('Unknown local')
   frame=((len(self.locals)*8+15)//16)*16
   if frame>4095:raise ValueError('Frame too large')
   self.emit(0xa9bf7bfd);self.emit(0xd10003ff|(frame<<10));self.emit(0x910003fd)
   for j,p in enumerate(params):self.local(j,p,True)
   self.end=self.fresh();pos,stop=self.block(body)
   if stop is not None:raise ValueError('Unexpected block end')
   self.imm(0,0);self.label(self.end);self.emit(0x910003bf);self.emit(0x910003ff|(frame<<10));self.emit(0xa8c17bfd);self.emit(0xd65f03c0)
  # __TEXT begins at BASE, first code page at +16KiB. Data follows code on a page boundary.
  codeoff=PAGE;dataoff=((codeoff+len(self.words)*4+PAGE-1)//PAGE)*PAGE
  for idx,label,kind in self.fix:
   pc=codeoff+idx*4
   target=dataoff+self.objects[label] if kind=='address' else codeoff+self.labels[label]
   delta=target-pc
   if kind=='address':
    pages=(target//4096)-(pc//4096)
    if not -(1<<20)<=pages<(1<<20):raise ValueError('ADRP reach')
    self.words[idx]|=((pages&3)<<29)|(((pages>>2)&0x7ffff)<<5)
    self.words[idx+1]|=(target&4095)<<10
   elif kind=='cond':
    if delta%4 or not -(1<<20)<=delta<(1<<20):raise ValueError('Conditional reach')
    self.words[idx]|=((delta//4)&0x7ffff)<<5
   else:
    if delta%4 or not -(1<<27)<=delta<(1<<27):raise ValueError('Branch reach')
    self.words[idx]|=(delta//4)&0x3ffffff
  code=b''.join(struct.pack('<I',w) for w in self.words);end=dataoff+len(self.data);datasize=((len(self.data)+PAGE-1)//PAGE)*PAGE
  seg=lambda name,vm,size,off,fs,prot:struct.pack('<II16sQQQQiiII',0x19,72,name.encode(),vm,size,off,fs,prot,prot,0,0)
  commands=seg('__PAGEZERO',0,BASE,0,0,0)+seg('__TEXT',BASE,dataoff,0,dataoff,5)+seg('__DATA',BASE+dataoff,datasize,dataoff,datasize,3)
  commands+=struct.pack('<IIQQ',0x80000028,24,codeoff,0)
  def stringcmd(cmd,text,prefix):
   raw=prefix+text.encode()+b'\0';size=(8+len(raw)+7)//8*8
   return struct.pack('<II',cmd,size)+raw+bytes(size-8-len(raw))
  commands+=stringcmd(0xe,'/usr/lib/dyld',struct.pack('<I',12))
  commands+=stringcmd(0xc,'/usr/lib/libSystem.B.dylib',struct.pack('<IIII',24,0,0x10000,0x10000))
  commands+=struct.pack('<II',0x1b,24)+hashlib.sha256(source.encode()).digest()[:16]
  commands+=struct.pack('<IIIIII',0x32,24,1,0x000e0000,0x001a0000,0)
  # Apple code-signing requires __LINKEDIT; codesign appends its signature there.
  linkoff=dataoff+datasize
  commands+=seg('__LINKEDIT',BASE+linkoff,0,linkoff,0,1)
  hdr=struct.pack('<8I',0xfeedfacf,0x0100000c,0,2,9,len(commands),0x200085,0)
  result=hdr+commands;result+=bytes(codeoff-len(result))+code;result+=bytes(dataoff-len(result))+self.data;result+=bytes(linkoff-len(result))
  return result,{'schema':'rf2.native.seed.v1','profile':'RF2_SYSTEM_A64_V1','target':'macos-arm64','codeBytes':len(code),'dataBytes':len(self.data),'functions':len(groups),'importedSymbols':[],'osLoader':'dyld/libSystem, macOS system calls','compiler':'direct RF2 seed, Python build time only','selfHosted':False,'speedClaim':None}
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: python3 bootstrap/seed.py source.rf2 output')
 src=Path(sys.argv[1]);out=Path(sys.argv[2]);raw,report=Compiler().compile(src.read_text());out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw);out.chmod(0o755)
 subprocess.run(['/usr/bin/codesign','-s','-','--force',str(out)],check=True)
 report.update(sourceSHA256=hashlib.sha256(src.read_bytes()).hexdigest(),executableSHA256=hashlib.sha256(out.read_bytes()).hexdigest());out.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
