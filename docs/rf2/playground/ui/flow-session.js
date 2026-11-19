/** Reusable browser view binding. All computation remains in the bounded RF2 worker. */
export class FlowSession {
 constructor({workerURL=new URL('../worker.js',import.meta.url),timeoutMs=3000}={}){this.url=workerURL;this.timeoutMs=timeoutMs;this.worker=null;this.generation=0;this.nextId=0;this.pending=new Map();this.inflight=false;}
 stop(reason='Session stopped.'){this.generation++;this.inflight=false;this.worker?.terminate();this.worker=null;for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(new Error(reason));}this.pending.clear();}
 request(action,fields={}){
  if(!this.worker){const generation=this.generation;this.worker=new Worker(this.url,{type:'module'});this.worker.onmessage=event=>{if(generation!==this.generation)return;const p=this.pending.get(event.data.id);if(!p)return;clearTimeout(p.timer);this.pending.delete(event.data.id);p.resolve(event.data);};this.worker.onerror=()=>this.stop('The RF2 worker could not start. Check the local page and try restarting.');}
  return new Promise((resolve,reject)=>{const id=++this.nextId;const timer=setTimeout(()=>this.stop('The RF2 worker exceeded its page deadline. Restart to try again.'),this.timeoutMs);this.pending.set(id,{resolve,reject,timer});this.worker.postMessage({id,action,...fields});});
 }
 async start(source,{stdin=''}={}){this.stop('New program started.');const generation=this.generation;this.inflight=true;try{return await this.request('run',{source,stdin});}finally{if(generation===this.generation)this.inflight=false;}}
 async answer(value){if(this.inflight)throw new Error('An RF2 action is already running.');const generation=this.generation;this.inflight=true;try{const accepted=await this.request('input',{value:String(value)});if(generation!==this.generation)throw new Error('This RF2 action belongs to an earlier session.');if(!accepted.ok)return accepted;return await this.request('run');}finally{if(generation===this.generation)this.inflight=false;}}
}
export function numberField(snapshot,name,max){const field=snapshot?.variables?.find(x=>x.name===name);if(!field||!['number','u64'].includes(field.kind)||!/^\d+$/.test(field.value))throw new Error(`This view needs a numeric ${name} value from RF2.`);const n=BigInt(field.value);if(n>BigInt(max))throw new Error(`RF2 returned ${name} outside this view's 0–${max} contract.`);return Number(n);}
