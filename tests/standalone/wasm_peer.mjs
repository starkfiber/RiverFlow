// Development oracle host only; emitted WebAssembly does not require Node.
import fs from'node:fs';import readline from'node:readline';
const cache=new Map();
for await(const line of readline.createInterface({input:process.stdin,crlfDelay:Infinity})){
 try{const q=JSON.parse(line);let e=cache.get(q.module);if(!e){const bytes=fs.readFileSync(q.module);const m=new WebAssembly.Module(bytes);if(WebAssembly.Module.imports(m).length)throw Error('unexpected imports');e=new WebAssembly.Instance(m).exports;cache.set(q.module,e);}
 const ptr=q.ptr??0;const view=new DataView(e.memory.buffer);if(ptr>=0&&ptr+q.data.length*4<=view.byteLength)q.data.forEach((v,i)=>view.setUint32(ptr+i*4,v,true));const value=e.run(ptr,q.words??q.data.length,q.count??q.data.length)>>>0;console.log(JSON.stringify({value,status:e.status()>>>0,work:e.work()>>>0}));
 }catch(e){console.log(JSON.stringify({error:String(e)}));}
}
