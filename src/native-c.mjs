import {compile} from './riverflow.mjs';
// C11 emission from validated RF² Core AST. No source text is interpolated as C identifiers.
export function emitC(source,{optimize=true}={}) {
 const p=compile(source),ids=new Map(p.functions.map((f,i)=>[f.name,i]));let serial=0;
 const name=()=>`v${serial++}`;
 const literal=v=>/^(0[xX][0-9a-fA-F]+|[0-9]+)$/.test(v);
 const prototypes=p.functions.map((f,i)=>`static uint32_t f${i}(const uint32_t*, size_t, uint32_t*, int*${f.params.filter(x=>x.type==='u32').map(()=>', uint32_t').join('')});`);
 const bodies=p.functions.map((f,i)=>{
  const env=new Map(),params=[];for(const v of f.params){if(v.type==='u32[]')env.set(v.name,'data');else{const n=name();env.set(v.name,n);params.push(`uint32_t ${n}`);}}
  // Recognize only an exact zero-initialized, two-step input sum.
  const [init,loop]=f.body, [load,add]=loop?.body??[];
  const isSum=optimize && f.name==='main' && f.body.length===2 && init?.kind==='var' && literal(init.value) && BigInt(init.value)===0n && loop?.kind==='for' && loop.end===f.params[1].name && loop.body.length===2 && load?.operation==='LOAD' && load.args.array===f.params[0].name && load.args.index===loop.index && load.args.result!==init.name && add?.operation==='ADD' && add.args.result===init.name && ((add.args.a===init.name && add.args.b===load.args.result)||(add.args.b===init.name && add.args.a===load.args.result)) && f.result===init.name;
  if(isSum){const count=env.get(f.params[1].name);return `/* Exact sum reduction: words<=65536; work=3+3*count<=196611. */
static uint32_t f${i}(const uint32_t *data,size_t words,uint32_t *steps,int *error,${params[0]}) {
 (void)words; *steps=3;
 if(${count}>UINT32_C(${loop.limit})){*error=-4;return 0;}
 uint64_t sum=0;
 for(uint32_t index=0;index<${count};++index){
  *steps+=3; sum+=data[index];
  ${p.arithmetic==='checked'?'if(sum>UINT32_MAX){*error=-2;return 0;}':''}
 } return (uint32_t)sum;
}`;}
  const out=[`static uint32_t f${i}(const uint32_t *data, size_t words, uint32_t *steps, int *error${params.length?', '+params.join(', '):''}) {`,` if (!rf2_tick(steps,error)) return 0;`];
  function emit(body,e,depth=1){const pad=' '.repeat(depth);const get=v=>literal(v)?`UINT32_C(${BigInt(v)})`:e.get(v);
   for(const n of body){out.push(`${pad}if (!rf2_tick(steps,error)) return 0;`);
    if(n.kind==='var'){const v=name();out.push(`${pad}uint32_t ${v} = ${get(n.value)};`);e.set(n.name,v);}
    else if(n.kind==='for'){const end=name(),ind=name();out.push(`${pad}{ uint32_t ${end} = ${get(n.end)};`,`${pad} if (${end} > UINT32_C(${n.limit})) { *error=-4; return 0; }`,`${pad} for (uint32_t ${ind}=0; ${ind}<${end}; ++${ind}) {`,`${pad}  if (!rf2_tick(steps,error)) return 0;`);const inner=new Map(e);inner.set(n.index,ind);emit(n.body,inner,depth+2);out.push(`${pad} }`,`${pad}}`);}
    else {const a=n.args;let value;
     if(['ADD','MUL'].includes(n.operation)){const t=name();out.push(`${pad}uint64_t ${t} = (uint64_t)${get(a.a)} ${n.operation==='ADD'?'+':'*'} (uint64_t)${get(a.b)};`);if(p.arithmetic==='checked')out.push(`${pad}if (${t} > UINT32_MAX) { *error=-2; return 0; }`);value=`(uint32_t)${t}`;}
     else if(n.operation==='LOAD'){const t=name();out.push(`${pad}uint32_t ${t} = ${get(a.index)};`,`${pad}if ((size_t)${t} >= words) { *error=-3; return 0; }`);value=`data[${t}]`;}
     else if(n.operation==='NONZERO')value=`(${get(a.value)} != 0)`;
     else if(n.operation==='POPCOUNT')value=`rf2_popcount(${get(a.value)})`;
     else {const callee=p.functions[ids.get(n.operation.slice(5))],t=name();out.push(`${pad}uint32_t ${t} = f${ids.get(callee.name)}(data,words,steps,error${callee.params.length?', '+callee.params.map(v=>get(a[v.name])).join(', '):''});`,`${pad}if (*error) return 0;`);value=t;}
     if(!e.has(a.result)){const v=name();out.push(`${pad}uint32_t ${v} = ${value};`);e.set(a.result,v);}else out.push(`${pad}${e.get(a.result)} = ${value};`);
    }
   }
  }
  emit(f.body,env);const result=literal(f.result)?`UINT32_C(${BigInt(f.result)})`:env.get(f.result);out.push(` return ${result};`,'}');return out.join('\n');
 });
 return `/* RF2 Core C11 backend. Caller owns truthful, valid u32 input and writable output.\n   No device/network effects. Work events preserve the Core interpreter contract. */\n#include <stdint.h>\n#include <stddef.h>\n#include <limits.h>\nstatic int rf2_tick(uint32_t *steps,int *error) { if (*steps>=UINT32_C(1048576)) { *error=-5; return 0; } ++*steps; return 1; }\nstatic uint32_t rf2_popcount(uint32_t x) { uint32_t n=0; while(x){x&=x-1; ++n;} return n; }\n${prototypes.join('\n')}\n${bodies.join('\n')}\nint rf2_eval(const uint32_t *data,size_t words,uint32_t count,uint32_t *out,uint32_t *work) {\n if (!out || words>65536 || count>words || (words && !data)) return -1;\n uintptr_t a=(uintptr_t)data, o=(uintptr_t)out, w=(uintptr_t)work; size_t bytes=words*sizeof(uint32_t);\n if ((a%_Alignof(uint32_t)) || (o%_Alignof(uint32_t)) || (work && w%_Alignof(uint32_t))) return -1;\n if (a>UINTPTR_MAX-bytes || o>UINTPTR_MAX-sizeof(uint32_t) || (work && w>UINTPTR_MAX-sizeof(uint32_t))) return -1;\n if (words && o<a+bytes && a<o+sizeof(uint32_t)) return -1;\n if (work && ((w<o+sizeof(uint32_t) && o<w+sizeof(uint32_t)) || (words && w<a+bytes && a<w+sizeof(uint32_t)))) return -1;\n uint32_t steps=0; int error=0; uint32_t result=f${ids.get('main')}(data,words,&steps,&error,count);\n if(work) *work=steps; if(error) return error; *out=result; return 0;\n}\n`;
}
