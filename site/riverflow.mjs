// RF² Core 0.1. Original JavaScript bootstrap, no eval or host effects.
export const PROFILE = 'RF2_U32_CORE_V0';
const NAME = /^[A-Za-z_][A-Za-z0-9_]{0,31}$/;
const MAX = 0xffffffffn;
const fail = message => { throw new Error(message); };
const literal = s => /^(0[xX][0-9a-fA-F]+|[0-9]+)$/.test(s);
const constant = s => { const n = BigInt(s); if(n>MAX) fail('u32 literal overflow'); return n; };
export function compile(source) {
  if(typeof source!=='string'||source.length>32768) fail('Source must be at most 32768 characters');
  const lines=source.split(/\r?\n/).map(x=>x.split('#')[0].trim()).filter(Boolean);
  if(!/^FLOW "[^"\r\n]{1,64}"$/.test(lines[0]??'')) fail('Expected FLOW "name"');
  if(lines[1]!==`PROFILE ${PROFILE}`) fail(`Expected PROFILE ${PROFILE}`);
  if(!['ARITHMETIC CHECKED','ARITHMETIC WRAP'].includes(lines[2])) fail('Choose CHECKED or WRAP arithmetic');
  let pos=3, nodes=0; const functions=[];
  function block(loop=false) {
    const out=[];
    while(pos<lines.length && !['END','END FOR'].includes(lines[pos]) && !lines[pos].startsWith('RETURN ')) {
      if(++nodes>512) fail('Static instruction limit exceeded');
      const line=lines[pos++]; let m;
      if(m=line.match(/^VAR (\w+) = (\w+)$/)) out.push({kind:'var',name:m[1],value:m[2]});
      else if(m=line.match(/^FOR (\w+) FROM 0 TO (\w+) LIMIT (\d+)$/)) {
        if(loop) fail('Nested loops are unsupported');
        const limit=Number(m[3]); if(limit<1||limit>65536) fail('Invalid loop limit');
        const body=block(true); if(lines[pos++]!=='END FOR') fail('Expected END FOR');
        out.push({kind:'for',index:m[1],end:m[2],limit,body});
      } else if(m=line.match(/^STEP (\w+) = (ADD|MUL|LOAD|POPCOUNT|NONZERO|CALL \w+) WITH \{(.*)\}$/)) {
        const args=Object.create(null);
        for(const item of m[3].split(',')) {const a=item.trim().match(/^(\w+):\s*(\w+)$/);if(!a||Object.hasOwn(args,a[1])) fail('Invalid or duplicate argument');args[a[1]]=a[2];}
        out.push({kind:'step',operation:m[2],args});
      } else fail(`Unsupported syntax: ${line.slice(0,100)}`);
    }
    return out;
  }
  while(pos<lines.length) {
    const m=lines[pos++].match(/^FUNCTION (\w+)\((.*)\) RETURNS u32$/);if(!m||!NAME.test(m[1])) fail('Expected typed FUNCTION');
    const params=m[2].split(',').filter(x=>x.trim()).map(x=>{const a=x.trim().match(/^(\w+):\s*(u32\[\]|u32)$/);if(!a||!NAME.test(a[1]))fail('Invalid parameter');return {name:a[1],type:a[2]};});
    if(new Set(params.map(x=>x.name)).size!==params.length)fail('Duplicate parameter');
    const body=block(); const ret=lines[pos++]?.match(/^RETURN (\w+)$/);if(!ret||lines[pos++]!=='END')fail('Expected RETURN and END');
    functions.push({name:m[1],params,body,result:ret[1]}); if(functions.length>16)fail('Function limit exceeded');
  }
  const table=new Map(functions.map(f=>[f.name,f]));if(table.size!==functions.length||!table.has('main')) fail('Unique functions and main required');
  const main=table.get('main');if(main.params.length!==2||main.params[0].type!=='u32[]'||main.params[1].type!=='u32') fail('main requires (data: u32[], count: u32)');
  const edges=new Map();
  for(const f of functions) {
    if(f.name!=='main'&&(f.params.length>4||f.params.some(p=>p.type!=='u32')))fail('Helpers accept up to four scalar arguments');
    const vars=new Map(f.params.map(p=>[p.name,p.type])); const immutable=new Set(vars.keys()); const calls=[];
    const read=(v,type='u32')=>{if(literal(v)){constant(v);if(type!=='u32')fail('Expected array');}else if(vars.get(v)!==type) fail(`Unknown or wrong type: ${v}`);};
    const write=v=>{if(!NAME.test(v)||immutable.has(v)||vars.get(v)==='u32[]')fail(`Invalid assignment: ${v}`);vars.set(v,'u32');};
    function check(body,inLoop=false) {for(const n of body) {
      if(n.kind==='var'){if(vars.has(n.name))fail('Duplicate variable');read(n.value);write(n.name);}
      else if(n.kind==='for') {
        if(f.name!=='main')fail('Loops only allowed in main');read(n.end);if(vars.has(n.index)||!NAME.test(n.index))fail('Invalid induction variable');
        const before=new Map(vars);vars.set(n.index,'u32');immutable.add(n.index);check(n.body,true);immutable.delete(n.index);vars.clear();for(const [k,v]of before)vars.set(k,v);
      } else {
        const a=n.args;let keys;
        if(n.operation.startsWith('CALL ')){const target=n.operation.slice(5),callee=table.get(target);if(!callee||target==='main')fail('Unknown or invalid helper');calls.push(target);keys=[...callee.params.map(x=>x.name),'result'];for(const p of callee.params)read(a[p.name]);}
        else {keys=({ADD:['a','b','result'],MUL:['a','b','result'],LOAD:['array','index','result'],POPCOUNT:['value','result'],NONZERO:['value','result']})[n.operation];for(const k of keys.filter(k=>k!=='result'))read(a[k],k==='array'?'u32[]':'u32');}
        if(Object.keys(a).sort().join()!==keys.sort().join())fail('Wrong operation arguments');write(a.result);
      }
    }}
    check(f.body);read(f.result);edges.set(f.name,calls);
  }
  const visiting=new Set(),visited=new Set(); function visit(name){if(visiting.has(name))fail('Recursive calls forbidden');if(visited.has(name))return;visiting.add(name);for(const c of edges.get(name))visit(c);visiting.delete(name);visited.add(name);}for(const name of table.keys())visit(name);
  return {schema:'riverflow.core.v0',name:lines[0].slice(6,-1),arithmetic:lines[2].split(' ')[1].toLowerCase(),effects:['read_input'],functions};
}
export function prepare(source) {
  const program=compile(source);
  return function(data=[],count=data.length) {
  if(!Array.isArray(data)||data.length>65536||data.some(x=>!Number.isInteger(x)||x<0||x>Number(MAX)))fail('Expected at most 65536 u32 inputs');
  if(!Number.isInteger(count)||count<0||count>data.length)fail('Count outside input capacity');
  let steps=0;const table=new Map(program.functions.map(x=>[x.name,x]));
  const tick=()=>{if(++steps>1048576)fail('Execution work limit exceeded');};
  const checked=n=>{if(program.arithmetic==='checked'&&n>MAX)fail('Checked arithmetic overflow');return n&MAX;};
  function call(name,values){tick();const f=table.get(name),env=new Map(f.params.map((p,i)=>[p.name,values[i]]));
    const get=v=>literal(v)?constant(v):env.get(v);
    function run(body){for(const n of body){tick();if(n.kind==='var')env.set(n.name,get(n.value));else if(n.kind==='for'){
      const end=Number(get(n.end));if(end>n.limit)fail('Loop limit exceeded');const saved=new Set(env.keys());for(let i=0;i<end;i++){tick();env.set(n.index,BigInt(i));run(n.body);}for(const k of env.keys())if(!saved.has(k))env.delete(k);
    }else{const a=n.args;let value;
      switch(n.operation){case 'ADD':value=checked(get(a.a)+get(a.b));break;case 'MUL':value=checked(get(a.a)*get(a.b));break;
      case 'LOAD':{const arr=get(a.array),i=Number(get(a.index));if(i>=arr.length)fail('LOAD outside input capacity');value=arr[i];break;}
      case 'NONZERO':value=get(a.value)===0n?0n:1n;break;case 'POPCOUNT':{let x=get(a.value);value=0n;while(x){x&=x-1n;value++;}break;}
      default:{const callee=table.get(n.operation.slice(5));value=call(callee.name,callee.params.map(p=>get(a[p.name])));}
      }env.set(a.result,value);
    }}}
    run(f.body);return get(f.result);
  }
  return {value:Number(call('main',[data.map(BigInt),BigInt(count)])),steps,profile:PROFILE,effects:program.effects};
  };
}
export function execute(source,data=[],count=data.length) { return prepare(source)(data,count); }
