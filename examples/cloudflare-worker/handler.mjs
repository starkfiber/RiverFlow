// Platform glue only. All admitted arithmetic executes the RF2-emitted module.
export function makeHandler(module) {
  return function fetch(request) {
    const headers={'Content-Type':'application/json','Cache-Control':'no-store'};
    const send=(code,value)=>new Response(JSON.stringify(value)+'\n',{status:code,headers});
    if(request.method!=='GET')return send(405,{error:'method'});
    if(request.url.length>12288)return send(414,{error:'url-limit'});
    const url=new URL(request.url);
    if(url.pathname==='/health')return send(200,{ok:true,backend:'RF2 WebAssembly'});
    if(url.pathname!=='/sum')return send(404,{error:'route'});
    if([...url.searchParams.keys()].some(k=>k!=='values')||url.searchParams.getAll('values').length!==1)return send(400,{error:'arguments'});
    const text=url.searchParams.get('values');
    const parts=text===''?[]:text.split(',');
    if(parts.length>1024)return send(400,{error:'count'});
    const data=[];
    for(const p of parts){if(!/^(0|[1-9][0-9]{0,9})$/.test(p)||Number(p)>4294967295)return send(400,{error:'value'});data.push(Number(p));}
    const e=new WebAssembly.Instance(module).exports;
    new Uint32Array(e.memory.buffer).set(data);
    const value=e.run(0,data.length,data.length)>>>0;
    return send(e.status()===0?200:422,{value,status:e.status(),work:e.work(),backend:'RF2 WebAssembly'});
  };
}
