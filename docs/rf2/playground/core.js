/* RF2 Simple V3 browser reference: parser -> immutable bytecode -> bounded VM.
 * No eval, Function, JS generation, file access or network access. Native RF2 is separate.
 */
const MAX = (1n << 64n) - 1n;
const ENCODER = new TextEncoder();
const issuedPlans = new WeakSet();
const RESERVED = new Set('say show let set ask number if else end repeat times while fn return'.split(' '));
const IDENT = /^[A-Za-z_][A-Za-z0-9_]{0,30}(?![\s\S])/;
const PREC = new Map([['==',1],['!=',1],['<',1],['<=',1],['>',1],['>=',1],['+',2],['-',2],['*',3],['/',3],['//',3],['%',3],['**',4]]);
const bytes = text => ENCODER.encode(text).length;
const trim = text => text.replace(/^[ \t]+|[ \t]+$/g,'');
function wellFormed(text) {
  for (let i=0;i<text.length;i++) { const c=text.charCodeAt(i); if(c>=0xd800&&c<=0xdbff){const next=text.charCodeAt(++i);if(!(next>=0xdc00&&next<=0xdfff))return false;}else if(c>=0xdc00&&c<=0xdfff)return false; }
  return true;
}
export class RF2Error extends Error {
  constructor(message,{code='SYNTAX',line=1,column=1,hint=''}={}) { super(message); this.name='RF2Error'; Object.assign(this,{code,line,column,hint}); }
  toJSON(){return {code:this.code,message:this.message,line:this.line,column:this.column,hint:this.hint};}
}
const issue = (message,loc={},code='SYNTAX',hint='') => { throw new RF2Error(message,{...loc,code,hint}); };
function freeze(value){ if(value&&typeof value==='object'){for(const item of Object.values(value))freeze(item);Object.freeze(value);}return value; }
function location(line,text,index=0){return {line,column:bytes(text.slice(0,index))+1};}
function literal(raw,loc){
  if(raw.length<2||raw[0]!=='"'||raw.at(-1)!=='"'||bytes(raw.slice(1,-1))>1024)issue('Use a quoted message of at most 1,024 bytes.',loc,'TEXT');
  for(let i=1;i<raw.length-1;i++){const c=raw[i];if(c==='"'||c.charCodeAt(0)<32)issue('Escape quotes and keep the message on one line.',loc,'TEXT');if(c==='\\'){i++;if(i>=raw.length-1||!['n','r','t','"','\\'].includes(raw[i]))issue('Use only \\n, \\r, \\t, \\" or \\\\ escapes.',loc,'TEXT');}}
  return JSON.parse(raw);
}
function expression(text,loc){
  if(bytes(text)>1024)issue('Keep this calculation within 1,024 bytes.',loc,'EXPRESSION_LIMIT');
  const tokens=[];let pos=0;
  while(pos<text.length){const c=text[pos];if(/[ \t\r\n]/.test(c)){pos++;continue;}const at=pos;
    if(/[0-9]/.test(c)){while(pos<text.length&&/[0-9]/.test(text[pos]))pos++;const value=BigInt(text.slice(at,pos));if(value>MAX)issue('That number is too large.',{...loc,column:loc.column+bytes(text.slice(0,at))},'OVERFLOW');tokens.push({type:'number',value:value.toString(),at});continue;}
    if(/[A-Za-z_]/.test(c)){while(pos<text.length&&/[A-Za-z0-9_]/.test(text[pos]))pos++;const value=text.slice(at,pos);if(value.length>31)issue('Use names of at most 31 characters.',loc,'NAME');tokens.push({type:'name',value,at});continue;}
    const two=text.slice(pos,pos+2);if(['**','//','==','!=','<=','>='].includes(two)){tokens.push({type:'op',value:two,at});pos+=2;continue;}
    if('+-*/%<>() ,'.includes(c)&&c!==' '){tokens.push({type:'op',value:c,at});pos++;continue;}
    issue(c==='^'?'Use ** for powers; ^ is not supported.':'Check the calculation and its operators.',{...loc,column:loc.column+bytes(text.slice(0,at))},'SYNTAX');
  }
  let cursor=0;
  const fail=(token=tokens[cursor])=>issue('Check the calculation, commas and parentheses.',{...loc,column:loc.column+bytes(text.slice(0,token?.at??text.length))},'SYNTAX');
  function parse(min=1,depth=0){
    if(depth>64)issue('Use at most 64 nested parentheses or calls.',loc,'EXPRESSION_DEPTH');
    const token=tokens[cursor++];if(!token)fail();let node;
    if(token.type==='number')node={type:'number',value:token.value,at:token.at};
    else if(token.type==='name'){
      if(tokens[cursor]?.value==='('){cursor++;const args=[];if(tokens[cursor]?.value!==')'){while(true){if(args.length===4)issue('A function has at most four arguments.',loc,'ARITY');args.push(parse(1,depth+1));if(tokens[cursor]?.value!==',')break;cursor++;if(tokens[cursor]?.value===')')fail();}}if(tokens[cursor]?.value!==')')fail();cursor++;node={type:'call',name:token.value,args,at:token.at};}
      else node={type:'name',name:token.value,at:token.at};
    }else if(token.value==='('){const value=parse(1,depth+1);if(tokens[cursor]?.value!==')')fail();cursor++;node={type:'group',value,at:token.at};}
    else fail(token);
    let compared=false;
    while(cursor<tokens.length){const op=tokens[cursor];const precedence=PREC.get(op.value);if(!precedence||precedence<min)break;if(precedence===1){if(compared)issue('Compare two values at a time; use parentheses for another comparison.',loc,'COMPARISON_CHAIN');compared=true;}cursor++;node={type:'binary',operator:op.value,left:node,right:parse(op.value==='**'?precedence:precedence+1,depth+1),at:op.at};}
    return node;
  }
  const result=parse();if(cursor!==tokens.length)fail();return result;
}
function validateExpr(node,scope,functions,loc,edges){
  if(node.type==='number')return;
  if(node.type==='name'){const at={...loc,column:loc.column+node.at};if(!scope.has(node.name))issue('Introduce '+node.name+' before using it.',at,'UNKNOWN_NAME');if(scope.get(node.name)!=='number')issue(node.name+' holds text; calculations need a number.',at,'TYPE');return;}
  if(node.type==='group')return validateExpr(node.value,scope,functions,loc,edges);
  if(node.type==='binary'){validateExpr(node.left,scope,functions,loc,edges);validateExpr(node.right,scope,functions,loc,edges);return;}
  const fn=functions.get(node.name);if(!fn)issue('That function has not been defined: '+node.name,{...loc,column:loc.column+node.at},'UNKNOWN_FUNCTION');if(fn.params.length!==node.args.length)issue(node.name+' needs '+fn.params.length+' arguments.',{...loc,column:loc.column+node.at},'ARITY');for(const arg of node.args)validateExpr(arg,scope,functions,loc,edges);edges?.add(node.name);
}
export function compile(source){
  if(typeof source!=='string')issue('Source must be text.',{},'SOURCE');if(source.length>65536||!wellFormed(source)||bytes(source)>65536)issue('Use valid UTF-8 source within 64 KiB.',{},'SOURCE_LIMIT');
  const rows=source.split('\n').map((raw,index)=>({raw,text:raw.replace(/^[ \t]+|[ \t\r]+$/g,''),line:index+1}));
  for(const row of rows)for(let i=0;i<row.raw.length;i++){const c=row.raw.charCodeAt(i);if(c<32&&![9,13].includes(c))issue('Remove the hidden control character.',location(row.line,row.raw,i),'SOURCE');}
  const commands=rows.filter(row=>row.text&&!row.text.startsWith('#')).map(row=>({...row,loc:location(row.line,row.raw,row.raw.search(/[^ \t]/))}));
  if(!commands.length)issue('Write something to run. Try: say "Hello, world!"',{},'EMPTY');if(commands.length>64)issue('Use at most 64 instructions.',commands[64].loc,'INSTRUCTION_LIMIT');
  const functions=new Map(),functionParts=new Set();
  for(let i=0;i<commands.length;i++){
    const row=commands[i];if(!/^fn(?:[ \t]|$)/.test(row.text))continue;
    const m=/^fn[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*\(([\s\S]*)\)(?![\s\S])/.exec(row.text);if(!m||!IDENT.test(m[1])||RESERVED.has(m[1])||m[1]==='main')issue('Use a function heading such as fn twice(n).',row.loc,'FUNCTION');if(functions.has(m[1]))issue('That function name already exists.',row.loc,'FUNCTION');if(functions.size===8)issue('Use at most eight functions.',row.loc,'FUNCTION_LIMIT');
    const params=trim(m[2])?m[2].split(',').map(trim):[];if(params.length>4||params.some(p=>!IDENT.test(p)||RESERVED.has(p))||new Set(params).size!==params.length)issue('Use up to four different numeric input names.',row.loc,'PARAMETERS');
    const body=commands[i+1],end=commands[i+2];if(!body||!/^return(?:[ \t]|$)/.test(body.text)||!end||end.text!=='end')issue('A small function has one return expression followed by end.',row.loc,'FUNCTION');
    const raw=body.text.replace(/^return[ \t]*/,''),exprLoc={...body.loc,column:body.loc.column+bytes(body.text.slice(0,body.text.length-raw.length))},expr=expression(raw,exprLoc);functions.set(m[1],{name:m[1],params,expr,loc:exprLoc,edges:new Set()});for(let j=i;j<=i+2;j++)functionParts.add(j);i+=2;
  }
  for(const fn of functions.values())validateExpr(fn.expr,new Map(fn.params.map(p=>[p,'number'])),functions,fn.loc,fn.edges);
  const colors=new Map();function visit(name){if(colors.get(name)===1)issue('These functions call each other in a circle.',functions.get(name).loc,'RECURSION');if(colors.get(name)===2)return;colors.set(name,1);for(const child of functions.get(name).edges)visit(child);colors.set(name,2);}for(const name of functions.keys())visit(name);
  const variables=new Map(),instructions=[],stack=[],inputs=[];
  function expr(text,loc){const ast=expression(text,loc);validateExpr(ast,variables,functions,loc);return ast;}
  for(let index=0;index<commands.length;index++){
    const row=commands[index],text=row.text,loc=row.loc;const match=/^([^ \t]+)(?:[ \t]+([\s\S]*))?(?![\s\S])/.exec(text);const word=match[1],arg=trim(match[2]??'');const argLoc={...loc,column:loc.column+bytes(text.slice(0,text.length-arg.length))};const pc=instructions.length;
    if(functionParts.has(index)){if(word==='fn'&&stack.length)issue('Define functions outside if and loop blocks.',loc,'FUNCTION_SCOPE');instructions.push({op:'NOP',loc});continue;}
    if(['if','while','repeat'].includes(word)){
      if(stack.length===8)issue('Use at most eight nested blocks.',loc,'BLOCK_LIMIT');let body=arg;if(word==='repeat'){const m=/^([\s\S]*?)[ \t]+times(?![\s\S])/.exec(arg);if(!m)issue('Use repeat followed by a number and times.',loc,'REPEAT');body=trim(m[1]);}
      instructions.push({op:word.toUpperCase(),expr:expr(body,argLoc),target:null,loc});stack.push({kind:word,head:pc,else:null});continue;
    }
    if(word==='else'){if(arg)issue('Put else on its own line.',loc);const block=stack.at(-1);if(!block||block.kind!=='if'||block.else!==null)issue('Use one else inside an if block.',loc,'BLOCK');instructions[block.head].target=pc+1;block.else=pc;instructions.push({op:'ELSE',target:null,loc});continue;}
    if(word==='end'){if(arg)issue('Put end on its own line.',loc);const block=stack.pop();if(!block)issue('There is no open block for this end.',loc,'BLOCK');if(block.kind==='if'){instructions[block.else??block.head].target=pc+1;instructions.push({op:'ENDIF',loc});}else{instructions[block.head].target=pc+1;instructions.push({op:'LOOP_END',head:block.head,loc});}continue;}
    if(word==='say'){if(arg.startsWith('"'))instructions.push({op:'SAY_TEXT',text:literal(arg,argLoc),loc});else{if(!IDENT.test(arg)||!variables.has(arg))issue('Use say "a message" or an existing name.',loc,'UNKNOWN_NAME');instructions.push({op:'SAY_NAME',name:arg,loc});}continue;}
    if(word==='show'){instructions.push({op:'SHOW',expr:expr(arg,argLoc),loc});continue;}
    if(['let','set','ask'].includes(word)){
      let name,kind,value,prompt;
      if(word==='ask'){const m=/^(?:(number)[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)(?:[ \t]+)([\s\S]*)(?![\s\S])/.exec(arg);if(!m)issue('Use ask name "Question?" or ask number age "Age?".',loc,'INPUT');name=m[2];kind=m[1]?'number':'text';prompt=literal(m[3],loc);}
      else{const m=/^([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*([\s\S]*)(?![\s\S])/.exec(arg);if(!m)issue('Put = between a name and its value.',loc,'ASSIGNMENT');name=m[1];kind=m[2].startsWith('"')?'text':'number';const valueLoc={...argLoc,column:argLoc.column+bytes(arg.slice(0,arg.length-m[2].length))};value=kind==='text'?literal(m[2],valueLoc):expr(m[2],valueLoc);}
      if(!IDENT.test(name)||RESERVED.has(name))issue('Choose a short name that is not a command word.',loc,'NAME');const existing=variables.get(name);const creating=word==='let'||(word==='ask'&&!existing);
      if(creating){if(existing)issue('That name already exists. Use set to change it.',loc,'NAME');if(stack.length)issue('Introduce names before the block; use set or ask inside it.',loc,'DECLARATION_SCOPE');if(functions.has(name))issue('That name belongs to a function.',loc,'NAME');if(variables.size===32)issue('Use at most 32 names.',loc,'VARIABLE_LIMIT');variables.set(name,kind);}else{if(!existing)issue('Introduce this name with let or ask first.',loc,'UNKNOWN_NAME');if(existing!==kind)issue('Text stays text and numbers stay numbers.',loc,'TYPE');}
      if(word==='ask'){instructions.push({op:'ASK',name,kind,prompt,loc});inputs.push({name,kind,prompt});}else instructions.push({op:word==='let'?'LET':'SET',name,kind,value,loc});continue;
    }
    issue(word==='return'?'Use return only inside a small function.':'Try say, show, let, set, ask, if, repeat, while or fn.',loc,'STATEMENT');
  }
  if(stack.length)issue('Finish every if and loop with end.',instructions[stack.at(-1).head].loc,'BLOCK');
  const plan={profile:'RF2_SIMPLE_V3_BROWSER_REFERENCE',source,instructions,functions:[...functions.values()].map(({edges,...fn})=>fn),variables:[...variables].map(([name,kind])=>({name,kind})),inputs,effects:{stdin:inputs.length>0,stdout:true,fileWrites:false,network:false},limits:{work:4096,repeat:1000,trace:200,outputBytes:262144}};freeze(plan);issuedPlans.add(plan);return plan;
}
export function createExecution(givenPlan,{stdin='',stdinClosed=false}={}){
  const plan=issuedPlans.has(givenPlan)?givenPlan:compile(givenPlan?.source);const fns=new Map(plan.functions.map(fn=>[fn.name,fn])),values=new Map(),loops=new Map();let pc=0,state='running',stdout='',staged='',work=0,error=null,waiting=null,inputBuffer=String(stdin),trace=[],traceDropped=0;
  const loc=()=>plan.instructions[pc]?.loc??plan.instructions.at(-1)?.loc??{line:1,column:1};
  function tick(where){if(work>=4096)issue('This program reached its work limit. Check the loop stopping rule.',where,'WORK_LIMIT');work++;}
  function output(text){if(bytes(stdout)+bytes(staged)+bytes(text)>262144)issue('This browser run reached its 256 KiB output limit.',loc(),'OUTPUT_LIMIT');staged+=text;}
  function flush(){stdout+=staged;staged='';}
  function calculate(node,scope,active=[],where=loc()){
    tick(where);
    if(node.type==='number')return BigInt(node.value);
    if(node.type==='name'){const value=scope.get(node.name);if(typeof value!=='bigint')issue('This calculation needs a number.',where,'TYPE');return value;}
    if(node.type==='group')return calculate(node.value,scope,active,where);
    if(node.type==='call'){if(active.includes(node.name))issue('Recursive function calls are not supported.',where,'RECURSION');if(active.length>=16)issue('Function calls are nested too deeply.',where,'FUNCTION_DEPTH');const fn=fns.get(node.name),args=node.args.map(arg=>calculate(arg,scope,active,where));return calculate(fn.expr,new Map(fn.params.map((name,i)=>[name,args[i]])),[...active,node.name],where);}
    const a=calculate(node.left,scope,active,where),b=calculate(node.right,scope,active,where),op=node.operator;let value;
    if(op==='==')return BigInt(a===b);if(op==='!=')return BigInt(a!==b);if(op==='<')return BigInt(a<b);if(op==='<=')return BigInt(a<=b);if(op==='>')return BigInt(a>b);if(op==='>=')return BigInt(a>=b);
    if(op==='+')value=a+b;
    if(op==='-'){if(a<b)issue('This would be below zero.',where,'UNDERFLOW');value=a-b;}
    if(op==='*'){if(b!==0n&&a>MAX/b)issue('That result is too large.',where,'OVERFLOW');value=a*b;}
    if(['/', '//','%'].includes(op)){if(b===0n)issue('Cannot divide by zero.',where,'DIVIDE_ZERO');if(op==='/'&&a%b!==0n)issue('That division has a fraction. Use // for a whole-number quotient.',where,'INEXACT_DIVISION');value=op==='%'?a%b:a/b;}
    if(op==='**'){let base=a,power=b;value=1n;while(power!==0n){tick(where);if(power&1n){if(base!==0n&&value>MAX/base)issue('That power is too large.',where,'OVERFLOW');value*=base;}power>>=1n;if(power!==0n){if(base!==0n&&base>MAX/base)issue('That power is too large.',where,'OVERFLOW');base*=base;}}}
    if(value>MAX)issue('That result is too large.',where,'OVERFLOW');return value;
  }
  function rememberInput(answer){
    if(!waiting)issue('Run the program until it asks a question first.',loc(),'INPUT_STATE');if(typeof answer!=='string')issue('Use valid text for the answer.',waiting.loc,'INPUT');if(answer.length>1026)issue('Use an answer of at most 1,024 bytes.',waiting.loc,'INPUT_LIMIT');if(!wellFormed(answer))issue('Use valid text for the answer.',waiting.loc,'INPUT');let text=answer;if(text.endsWith('\n'))text=text.slice(0,-1).replace(/\r$/,'');if(text.includes('\n')||text.includes('\r')||[...text].some(c=>c.charCodeAt(0)<32&&c!=='\t'))issue('Provide one answer without hidden control characters.',waiting.loc,'INPUT');if(bytes(text)>1024)issue('Use an answer of at most 1,024 bytes.',waiting.loc,'INPUT_LIMIT');let value=text;if(waiting.kind==='number'){if(!/^(0|[1-9][0-9]*)(?![\s\S])/.test(text)||text.length>20)issue('Enter a whole number, such as 12, without extra leading zeros.',waiting.loc,'INPUT_NUMBER');value=BigInt(text);if(value>MAX)issue('That number is too large.',waiting.loc,'INPUT_NUMBER');}values.set(waiting.name,value);waiting=null;pc++;state='running';
  }
  function queuedAnswer(){if(!inputBuffer.length){if(stdinClosed)issue('No answer arrived. Type an answer and press Enter.',waiting?.loc??loc(),'INPUT_EOF');return false;}const end=inputBuffer.indexOf('\n');let answer;if(end<0){answer=inputBuffer;inputBuffer='';}else{answer=inputBuffer.slice(0,end+1);inputBuffer=inputBuffer.slice(end+1);}rememberInput(answer);return true;}
  function fail(e){error=e instanceof RF2Error?e.toJSON():{code:'INTERNAL',message:'The browser reference could not complete this run.',...loc(),hint:''};state='error';staged='';}
  function snapshot(){return {state,line:loc().line,stdout,variables:[...values].map(([name,value])=>({name,kind:typeof value==='bigint'?'number':'text',value:String(value)})),trace:trace.map(item=>({...item})),traceDropped,error,steps:work,pc,...(waiting?{question:{name:waiting.name,kind:waiting.kind,prompt:waiting.prompt}}:{})};}
  function step(){
    if(state==='error'||state==='done')return snapshot();if(state==='waiting'){try{queuedAnswer();}catch(e){fail(e);}return snapshot();}
    if(pc>=plan.instructions.length){flush();state='done';return snapshot();}
    const instruction=plan.instructions[pc],before=pc;
    try{
      tick(instruction.loc);let next=pc+1;
      if(instruction.op==='LET'||instruction.op==='SET')values.set(instruction.name,instruction.kind==='text'?instruction.value:calculate(instruction.value,values));
      if(instruction.op==='SAY_TEXT')output(instruction.text+'\n');
      if(instruction.op==='SAY_NAME')output(String(values.get(instruction.name))+'\n');
      if(instruction.op==='SHOW')output(calculate(instruction.expr,values).toString()+'\n');
      if(['IF','WHILE','REPEAT'].includes(instruction.op)){const value=calculate(instruction.expr,values);if(instruction.op==='REPEAT'){if(value>1000n)issue('Repeat at most 1,000 times.',instruction.loc,'REPEAT_LIMIT');loops.set(pc,value);}if(value===0n)next=instruction.target;}
      if(instruction.op==='ELSE')next=instruction.target;
      if(instruction.op==='LOOP_END'){const head=plan.instructions[instruction.head];if(head.op==='REPEAT'){const remaining=loops.get(instruction.head);if(remaining>1n){loops.set(instruction.head,remaining-1n);next=instruction.head+1;}}else next=instruction.head;}
      if(instruction.op==='ASK'){output(instruction.prompt+'\n');flush();waiting=instruction;state='waiting';if(queuedAnswer())next=pc;else next=before;}
      pc=next;if(trace.length<200)trace.push({step:work,pc:before,line:instruction.loc.line,op:instruction.op,state});else traceDropped++;
      if(pc>=plan.instructions.length&&state==='running'){flush();state='done';}
    }catch(e){fail(e);if(trace.length<200)trace.push({step:work,pc:before,line:instruction.loc.line,op:instruction.op,state:'error',code:error.code});else traceDropped++;}return snapshot();
  }
  function run(){while(state==='running')step();return snapshot();}
  function provideInput(text){if(state!=='waiting')issue('The program is not waiting for an answer.',loc(),'INPUT_STATE');try{rememberInput(text);}catch(e){fail(e);}return snapshot();}
  return Object.freeze({step,run,provideInput,snapshot});
}
