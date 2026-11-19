import {compile,createExecution,RF2Error} from './core.js';
let plan=null,execution=null;
const summary=()=>plan?{profile:plan.profile,commands:plan.instructions.length,instructions:plan.instructions.length,instructionCount:plan.instructions.length,functions:plan.functions.length,functionCount:plan.functions.length,variables:plan.variables.length,inputs:plan.inputs,effects:plan.effects,limits:plan.limits}:null;
self.addEventListener('message',event=>{
 const request=event.data??{};const {id,action}=request;const metrics={compileMs:0,executionMs:0,clock:'browser performance.now; not native CPU time'};
 try{
  if(action==='compile'||(action==='run'&&typeof request.source==='string')){plan=null;execution=null;const started=performance.now();plan=compile(request.source);metrics.compileMs=performance.now()-started;execution=createExecution(plan,{stdin:request.stdin??'',stdinClosed:request.stdinClosed===true});}
  if(action==='reset'){if(typeof request.source==='string'){plan=null;execution=null;const started=performance.now();plan=compile(request.source);metrics.compileMs=performance.now()-started;}if(!plan)throw new RF2Error('Compile a program first.',{code:'SESSION'});execution=createExecution(plan,{stdin:request.stdin??'',stdinClosed:request.stdinClosed===true});}
  if(!['compile','run','step','input','reset'].includes(action))throw new RF2Error('Unknown playground action.',{code:'ACTION'});
  if(!execution)throw new RF2Error('Compile a program first.',{code:'SESSION'});
  const started=performance.now();let snapshot;
  if(action==='run')snapshot=execution.run();else if(action==='step')snapshot=execution.step();else if(action==='input')snapshot=execution.provideInput(request.value??'');else snapshot=execution.snapshot();metrics.executionMs=performance.now()-started;
  self.postMessage({id,action,ok:!snapshot.error,plan,planSummary:summary(),snapshot,error:snapshot.error??null,metrics});
 }catch(error){self.postMessage({id,action,ok:false,plan:null,planSummary:null,metrics,error:error instanceof RF2Error?error.toJSON():{code:'INTERNAL',message:'The browser reference could not compile this request.',line:1,column:1,hint:''}});}
});
