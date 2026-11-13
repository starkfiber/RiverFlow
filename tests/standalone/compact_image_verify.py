"""Native compact/legacy execution, loader layout, function-map and invalidation controls."""
from pathlib import Path
import subprocess,os,hashlib,json,struct,sys,time
R=Path(__file__).resolve().parents[2];D=R/'artifacts/compact-images'/('verify-'+str(time.time_ns()));D.mkdir(parents=True);C=Path(os.environ['RF2_TEST_COMPILER']).resolve();sys.path.insert(0,str(R/'tools'));from importlib.machinery import SourceFileLoader
impact=SourceFileLoader('impact',str(R/'tools/function-impact.py')).load_module();cases=[]
def segments(raw):
 out={};off=32
 for _ in range(struct.unpack_from('<I',raw,16)[0]):
  cmd,n=struct.unpack_from('<II',raw,off)
  if cmd==0x19:out[raw[off+8:off+24].rstrip(b'\0').decode()]=struct.unpack_from('<QQQQ',raw,off+24)
  off+=n
 return out
programs=[('zero-tail','''fn main(argc,argv)
 let a=buffer("first",8388608)
 let text="middle"
 let b=buffer("second",65)
 if load8(a)|load8(a+8388607)|load8(b+64)
  return 5
 end
 do store8(a+8388607,81)
 do store8(b+64,82)
 do write(1,text,6)
 return (load8(a+8388607)+load8(b+64))!=163
end
''',b'middle',0),('shared-buffer','''fn other()
 return buffer("shared",64)
end
fn main(argc,argv)
 let p=buffer("shared",64)
 do store64(p,123)
 return load64(other())!=123
end
''',b'',0),('call-branch','''fn twice(x)
 if x>4
  return x*2
 end
 return x+2
end
fn main(argc,argv)
 return twice(8)!=16
end
''',b'',0),('clock-binding','''fn main(argc,argv)
 let tb=buffer("tb",8)
 if clock_timebase(tb)!=0
  return 3
 end
 return (load32(tb)==0)|(load32(tb+4)==0)|(vm_clock_ticks()==0)
end
''',b'',0),('typed-array','''array Items(u64,8)
fn main(argc,argv)
 let a=Items()
 set a[7]=17
 return a[0]|(a[7]!=17)
end
''',b'',0)]
for name,body,stdout,exitcode in programs:
 p=D/(name+'.rf2');p.write_text('profile RF2_SYSTEM_A64_V1\n'+body)
 for opt in [False,True]:
  for compact in [False,True]:
   out=D/f'{name}-{opt}-{compact}';args=[C,p,out]+(['--opt']if opt else[])+(['--compact']if compact else[]);q=subprocess.run(args,capture_output=True,timeout=20);assert q.returncode==0,q.stderr;raw=out.read_bytes();seg=segments(raw);assert seg['__DATA'][1]>=seg['__DATA'][3] and seg['__DATA'][2]+seg['__DATA'][3]<=len(raw)
   if compact and name=='zero-tail':assert len(raw)<100000 and seg['__DATA'][1]>8000000 and seg['__DATA'][3]<=16384
   subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True);q=subprocess.run([out],capture_output=True,timeout=5);assert q.returncode==exitcode and q.stdout==stdout,(name,opt,compact,q.returncode,q.stderr);cases.append({'program':name,'opt':opt,'compact':compact,'unsignedBytes':len(raw)})
# Reordering may add alignment padding; reapply the original data bound.
compiler_source=(R/'native/compiler/compiler.rf2').read_text()
import re
pieces=[]
for name in ['state','die','require','length','object','image_options','layout_image_objects']:
 m=re.search(r'^fn '+name+r'\(',compiler_source,re.M);n=re.search(r'^fn ',compiler_source[m.end():],re.M);pieces.append(compiler_source[m.start():m.end()+n.start()])
p=D/'layout-bound.rf2';p.write_text('profile RF2_SYSTEM_A64_V1\n'+''.join(pieces)+'fn main(argc,argv)\n do store64(state()+72,2)\n do store64(image_options(),1)\n do store64(object(0),2)\n do store64(object(0)+16,134217704)\n do store64(object(1),1)\n do store64(object(1)+16,17)\n do layout_image_objects()\n return 0\nend\n');out=D/'layout-bound';subprocess.run([C,p,out],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True);q=subprocess.run([out],capture_output=True);assert q.returncode==1 and b'compact data size bound'in q.stderr

# A real modular SHA application must preserve output across file/VM separation.
for opt in [False,True]:
 out=D/f'checksum-{opt}';subprocess.run([C,R/'examples/file-checksum.rf2',out,'--compact',*(['--opt']if opt else[])],capture_output=True,check=True);subprocess.run(['/usr/bin/codesign','-s','-',out],capture_output=True,check=True)
 for n in [0,1,55,56,63,64,65,127,128,129,4096,65536]:
  p=D/'input';data=bytes((i*17)&255 for i in range(n));p.write_bytes(data);q=subprocess.run([out,p],capture_output=True,timeout=5);assert q.returncode==0 and q.stdout.strip().decode()==hashlib.sha256(data).hexdigest();cases.append({'program':'checksum','opt':opt,'bytes':n})
# Function fingerprints and call propagation are evidence, not code reuse.
base='''profile RF2_SYSTEM_A64_V1
record Value(n:u64)
fn leaf(x)
 return x+1
end
fn caller(x)
 return leaf(x)
end
fn separate(x)
 return x*3
end
fn main(argc,argv)
 return caller(3)!=4
end
''';maps={}
for name,source in [('base',base),('body',base.replace('x+1','x+2')),('comment',base.replace(' return x+1',' # note\n return x+1')),('record',base.replace('Value(n:u64)','Value(n:u64,m:u64)'))]:
 p=D/(name+'.rf2');p.write_text(source);out=D/name;q=subprocess.run([C,p,out,'--opt','--compact','--functions'],capture_output=True);assert q.returncode==0,q.stderr;maps[name]=Path(str(out)+'.functions');impact.read_map(maps[name])
result=impact.compare(maps['base'],maps['body']);assert result['changedFunctions']==['leaf'] and result['requiresRevalidation']==['caller','leaf','main'] and result['unchangedCandidates']==['separate'] and not result['machineCodeReused'],result
assert impact.compare(maps['base'],maps['comment'])['changedFunctions']==[]
assert impact.compare(maps['base'],maps['record'])['globalContextChanged']
refusals=0
for data in [b'',maps['base'].read_bytes()[:-4],maps['base'].read_bytes().replace(b'F leaf ',b'F 1bad '),maps['base'].read_bytes().replace(b'C leaf',b'C absent')]:
 p=D/f'bad-map-{refusals}';p.write_bytes(data)
 try:impact.read_map(p)
 except (AssertionError,ValueError,IndexError,UnicodeError):refusals+=1
 else:raise AssertionError('malformed map accepted')
# Compact compiler self-generation reaches identical unsigned output.
a=D/'self-a';b=D/'self-b';subprocess.run([C,R/'native/compiler/compiler.rf2',a,'--opt','--compact'],capture_output=True,check=True);raw=a.read_bytes();subprocess.run(['/usr/bin/codesign','-s','-',a],capture_output=True,check=True);subprocess.run([a,R/'native/compiler/compiler.rf2',b,'--opt','--compact'],capture_output=True,check=True);assert raw==b.read_bytes()
report={'passed':True,'executionCases':len(cases),'cases':cases,'functionChangeEvidence':result,'malformedMapRefusals':refusals,'reorderedDataBoundRefused':True,'compactSelfGenerationUnsignedEqual':True,'compilerSHA256':hashlib.sha256(C.read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256((R/'native/compiler/compiler.rf2').read_bytes()).hexdigest(),'limits':'One Darwin ARM64 host; map is diagnostic and machineCodeReused is false. No energy or universal performance claim.'};(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(D/'report.json'),'passed':True,'executionCases':len(cases)}))
