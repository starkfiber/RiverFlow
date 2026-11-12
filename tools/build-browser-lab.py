"""Fixed static routing atop the tested RF2 HTTP subset. Generated composition is retained."""
from pathlib import Path
import sys,subprocess,hashlib,json,shutil,os
R=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False);base=(R/'examples/stack-lab/server.rf2').read_text();start=base.index(' if eq(path,size,"/")');end=base.index(' if eq(path,size,"/health")',start);routing=''
for path,name,kind in [('/','index.html','text/html; charset=utf-8'),('/app.js','app.js','text/javascript; charset=utf-8'),('/app.css','app.css','text/css; charset=utf-8'),('/sum.wasm','sum.wasm','application/wasm'),('/sum.flow','sum.flow','text/plain; charset=utf-8')]:routing+=f' if eq(path,size,"{path}")\n  return serve_asset(fd,"{name}","{kind}")\n end\n'
text=base[:start]+routing+base[end:];text=text.replace('fn main(argc,argv)\n','fn main(argc,argv)\n if argc!=2\n  return 1\n end\n do store64(asset_root(),load64(argv+8))\n').replace('store8(address+3,92)','store8(address+3,102)').replace('18780/','18790/').replace('0.18-dev','0.19-dev');text+='\n'+(R/'examples/browser-lab/assets.rf2').read_text();(out/'server.rf2').write_text(text);c=R/'output/foundation-0.19-final/rf2c-self';subprocess.run([c,out/'server.rf2',out/'rf2-browser-lab','--opt'],check=True);subprocess.run(['/usr/bin/codesign','-s','-',out/'rf2-browser-lab'],check=True)
wc=Path(os.environ.get('RF2_WASM_COMPILER',R/'output/wasm-0.19-final/rf2-wasm'));subprocess.run([wc,R/'examples/browser-lab/sum.flow',out/'sum.wasm'],check=True)
for root in [R/'site/lab',R/'docs/lab']:
 root.mkdir(exist_ok=True)
 for name in ['index.html','app.css','app.js','sum.flow']:shutil.copy2(R/'examples/browser-lab'/name,root/name)
 shutil.copy2(out/'sum.wasm',root/'sum.wasm')
(out/'BUILD.json').write_text(json.dumps({'compilerSHA256':hashlib.sha256(c.read_bytes()).hexdigest(),'binarySHA256':hashlib.sha256((out/'rf2-browser-lab').read_bytes()).hexdigest(),'generatedSourceSHA256':hashlib.sha256((out/'server.rf2').read_bytes()).hexdigest(),'scope':'Derived fixed-asset serving on loopback18790, same bounded HTTP subset as0.18; explicit root argument, no caller filesystem routing'},indent=2)+'\n')
