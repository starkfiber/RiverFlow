import {FlowSession,numberField} from '../ui/flow-session.js';
const el=id=>document.getElementById('maker-'+id),session=new FlowSession();
let revision=0,busy=false,dirty=false,custom=false,lastGood='',attempted='',reply=null,successful=null,viewError=null;
const defaults={price:5,tickets:2,wallet:12};
function program(v){return `let price = ${v.price}
let tickets = ${v.tickets}
let wallet = ${v.wallet}
let total = price * tickets
let approved = wallet >= total
let printed = 0
let change = 0
let shortfall = 0
if approved
 set change = wallet - total
 repeat tickets times
  set printed = printed + 1
 end
 say "Tickets ready. Enjoy the film!"
else
 set shortfall = total - wallet
 say "Not enough money. Keep your money."
end
show total
show printed
`;}
function inputs(){const v={};for(const [name,min,max] of [['price',1,20],['tickets',1,6],['wallet',0,200]]){const value=el(name).value;if(!/^(0|[1-9][0-9]*)$/.test(value)||BigInt(value)<BigInt(min)||BigInt(value)>BigInt(max)){el(name).setAttribute('aria-invalid','true');el(name).focus();throw new Error(`${name==='tickets'?'Friends':name==='wallet'?'Money to spend':'Ticket price'}: enter a whole number from ${min} to ${max}.`);}v[name]=Number(value);el(name).removeAttribute('aria-invalid');}return v;}
function controls(){el('run').disabled=busy;el('apply').disabled=busy;el('last-good').disabled=busy||!lastGood;el('record').disabled=busy||!reply;el('save').disabled=busy;for(const n of ['price','tickets','wallet'])el(n).disabled=custom;el('code-state').textContent=custom?(dirty?'Your code draft · not run yet':'Your checked code'):(dirty?'Visual rules changed · run to see them':'Rules generated from your controls');el('code-help').textContent=custom?'Visual controls are locked while you edit, so they cannot overwrite your code. Restore the example to use them again.':'These are the actual RF2 rules behind this counter. You can read them now or edit them when you are ready.';}
function message(text,error=false){el('notice').textContent=text;el('notice').dataset.kind=error?'error':'info';}
function pending(){revision++;session.stop('Your changes are waiting.');busy=false;dirty=true;el('scene').dataset.pending='1';message('Your changes are ready. Run the counter to see the new result.');el('prediction-feedback').textContent='';delete el('prediction-feedback').dataset.correct;el('predict').removeAttribute('aria-invalid');controls();}
for(const n of ['price','tickets','wallet'])el(n).addEventListener('input',()=>{if(custom)return;pending();try{el('source').value=program(inputs());}catch(error){message(error.message,true);}});
el('source').addEventListener('input',()=>{custom=true;pending();});
const value=(snapshot,name,max)=>numberField(snapshot,name,max);
function render(result,source){const s=result.snapshot;if(!result.ok||!s||s.state!=='done')throw new Error(result.error?.message||'This counter needs a finished program with no unanswered questions.');
 const v={price:value(s,'price',20),tickets:value(s,'tickets',6),wallet:value(s,'wallet',200),total:value(s,'total',10000),approved:value(s,'approved',1),printed:value(s,'printed',6),change:value(s,'change',200),shortfall:value(s,'shortfall',10000)};
 if(v.price<1||v.tickets<1)throw new Error('This picture needs price 1–20 and tickets 1–6. Restore the example, or adjust those values in your code.');
 const knownRules=source===program({price:v.price,tickets:v.tickets,wallet:v.wallet});
 // The worker owns every business value. This view formats and draws those returned values only.
 for(const key of ['price','tickets','wallet','total','printed','change','shortfall']){const node=el('actual-'+key);if(node)node.textContent=String(v[key]);}
 el('party').replaceChildren(...Array.from({length:v.tickets},(_,i)=>{const person=document.createElement('span');person.className='cinema-person';person.style.setProperty('--person',i);person.textContent=String(i+1);return person;}));
 el('ticket-stack').replaceChildren(...Array.from({length:v.printed},(_,i)=>{const ticket=document.createElement('div');ticket.className='printed-ticket';ticket.style.setProperty('--ticket',i);const mark=document.createElement('span');mark.textContent='✦';const title=document.createElement('strong');title.textContent='THE LITTLE CINEMA';const no=document.createElement('small');no.textContent=`TICKET ${i+1} · ADMIT ONE`;ticket.append(mark,title,no);return ticket;}));
 el('scene').dataset.approved=String(v.approved);el('scene').dataset.pending='0';el('scene').classList.remove('just-ran');void el('scene').offsetWidth;el('scene').classList.add('just-ran');
 el('outcome').textContent=!knownRules?'Your edited program finished.':v.approved?'Your friends can go in.':'Keep the money. No tickets printed.';el('outcome-detail').textContent=!knownRules?`RF2 returned total ${v.total}, approved ${v.approved} and printed ${v.printed}. Your edited rules control these values.`:v.approved?`RF2 printed ${v.printed} ticket${v.printed===1?'':'s'} and returned RM ${v.change}.`:`The bill is RM ${v.total}. RF2 says you need RM ${v.shortfall} more.`;
 el('scene-total').textContent=String(v.total);el('scene-state').textContent=knownRules?(v.approved?`${v.printed} tickets ready · everyone can go in`:`Keep your money · need RM ${v.shortfall} more`):`Your code returned approved = ${v.approved}`;
 el('equation').textContent=knownRules?`${v.price} × ${v.tickets} = ${v.total}`:`total = ${v.total}`;el('why-title').textContent=knownRules?'One price. Every friend.':'Your rule. Your result.';
 el('reason').textContent=!knownRules?'You changed the source. Read the checked code below to see how it produced this result; the picture does not assume the original purchase rule still applies.':v.approved?`RM ${v.wallet} covers RM ${v.total}. The “if” path ran, then the loop printed ${v.printed} ticket${v.printed===1?'':'s'}.`:`RM ${v.wallet} does not cover RM ${v.total}. The “else” path ran. Your wallet stays with you.`;
 el('source-summary').textContent=knownRules?`price remembers ${v.price}; tickets remembers ${v.tickets}. Multiplication produced ${v.total}. A comparison produced approved = ${v.approved}.`:`Your code returned price ${v.price}, tickets ${v.tickets}, total ${v.total} and approved ${v.approved}. Inspect the actual source and execution record below.`;
 el('applied').textContent=source;el('trace').textContent=(s.trace||[]).map(x=>`${x.line}: ${x.kind||x.operation||x.op||''} ${x.detail||x.text||''}`).join('\n')||JSON.stringify(s.trace||[],null,2);el('output').textContent=s.stdout||'(No text output.)';
 successful={v,source,snapshot:s,knownRules};el('challenge-result').textContent=!knownRules?'You are exploring your own rules. Restore the example to return to the guided challenge.':v.total===12&&v.printed===3?'Challenge solved: three tickets, RM 12, all printed.':'Next little challenge: make three tickets cost RM 12 and get everyone inside.';
 const p=el('predict').value;if(p!=='')checkPrediction();
}
function checkPrediction(){delete el('prediction-feedback').dataset.correct;el('predict').removeAttribute('aria-invalid');if(dirty||!successful){el('prediction-feedback').textContent='Run your current rules first, then compare your prediction.';return;}const guess=el('predict').value;if(!/^(0|[1-9][0-9]*)$/.test(guess)||BigInt(guess)>10000n){el('predict').setAttribute('aria-invalid','true');el('prediction-feedback').textContent='Enter your predicted bill as a whole number from 0 to 10000.';return;}const {v,knownRules}=successful;const right=BigInt(guess)===BigInt(v.total);el('prediction-feedback').dataset.correct=String(right);el('prediction-feedback').textContent=!knownRules?(right?`Your prediction matches: the edited code returned total ${v.total}.`:`You guessed RM ${guess}; your edited code returned total ${v.total}. Inspect your calculation below.`):right?`Yes. RM ${v.price} for each of ${v.tickets} friends makes RM ${v.total}. Change a value and try a new prediction.`:`You guessed RM ${guess}. The actual RF2 result is ${v.price} × ${v.tickets} = RM ${v.total}. The price is for one ticket, so it is counted once for each friend. Try again.`;}

async function run(source,{preserveDraft=false}={}){const r=++revision;session.stop('Counter restarted.');busy=true;reply=null;viewError=null;attempted=source;controls();message('Checking your rules and running the counter…');try{if(new TextEncoder().encode(source).length>65536)throw new Error('Keep this lesson under 64 KiB of source.');const result=await session.start(source);if(r!==revision)return;reply=result;render(result,source);lastGood=source;if(!preserveDraft){dirty=false;el('source').value=source;}else dirty=el('source').value!==source;message(preserveDraft&&dirty?'Showing your last working counter. Your newer draft is still kept in the editor.':'That result came from your RF2 program. Change one thing and try again.');if(el('predict').value!==''&&!dirty)checkPrediction();}catch(error){if(r!==revision)return;viewError=error.message;message(`${error.message} Your last successful result is still shown; no new tickets were accepted.`,true);el('scene').dataset.pending='1';el('error').hidden=false;el('error').textContent=error.message;}finally{if(r===revision){busy=false;controls();}}}
el('run').addEventListener('click',()=>{el('error').hidden=true;try{const source=custom?el('source').value:program(inputs());run(source);}catch(error){message(error.message,true);}});
el('apply').addEventListener('click',()=>{custom=true;el('error').hidden=true;run(el('source').value);});el('last-good').addEventListener('click',()=>{el('error').hidden=true;run(lastGood,{preserveDraft:true});});
el('prediction-form').addEventListener('submit',event=>{event.preventDefault();checkPrediction();});
function restore(){revision++;session.stop('Example restored.');custom=false;dirty=true;for(const n of Object.keys(defaults))el(n).value=defaults[n];el('predict').value='';el('prediction-feedback').textContent='';el('error').hidden=true;el('source').value=program(defaults);run(el('source').value);}
el('restore').addEventListener('click',restore);
el('challenge').addEventListener('click',()=>{if(custom){message('Your code draft is kept. Restore the example before using the visual challenge.',true);return;}for(const [n,v]of Object.entries({price:4,tickets:3,wallet:12}))el(n).value=v;el('source').value=program(inputs());pending();message('Three friends, RM 4 each, RM 12 in the wallet. Predict the bill, then run it.');});
el('refusal').addEventListener('click',()=>{if(custom){message('Your code draft is kept. Restore the example before using the visual challenge.',true);return;}for(const [n,v]of Object.entries({price:5,tickets:3,wallet:12}))el(n).value=v;el('source').value=program(inputs());pending();message('Three friends want RM 5 tickets, but have RM 12. What should your app do? Run it.');});
function save(content,type,name){const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
el('save').addEventListener('click',()=>save(el('source').value,'text/plain;charset=utf-8','my-cinema.flow'));
el('record').addEventListener('click',async()=>{if(!reply)return;const source=attempted,record={schema:'rf2.maker.execution.v1',backend:'bounded-browser-reference',source,snapshot:reply.snapshot||null,error:reply.error||null,viewError,metrics:reply.metrics,recordedAt:new Date().toISOString(),unsigned:true};record.sourceSha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(source))),x=>x.toString(16).padStart(2,'0')).join('');save(JSON.stringify(record,null,2),'application/json','my-cinema-execution.json');});
window.addEventListener('pagehide',()=>{revision++;session.stop('Page closed.');});
const foundation=document.getElementById('foundations');if(location.hash==='#lesson'||location.hash==='#foundations')foundation.open=true;window.addEventListener('hashchange',()=>{if(location.hash==='#lesson'||location.hash==='#foundations')foundation.open=true;});
restore();
