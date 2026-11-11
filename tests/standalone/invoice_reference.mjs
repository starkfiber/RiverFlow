// Development comparator only. End users do not require Node.
import fs from 'node:fs';
import readline from 'node:readline';
const explicitSchema=JSON.parse(fs.readFileSync(new URL('./invoice-explicit-schema.json',import.meta.url),'utf8'));
export function invoice(plan,lines){
 if(typeof plan!=='string'||Buffer.byteLength(plan)>256)throw Error('plan');
 const words=plan.trim().split(/[ \t\r\n]+/);
 if(words.length!==10||words.slice(0,6).join(' ')!=='rf2 app v1 invoice total currency'||!/^[A-Z]{3}$/.test(words[6])||words[7]!=='tax'||!/^(0|[1-9][0-9]{0,4})$/.test(words[8])||Number(words[8])>10000||words[9]!=='bps')throw Error('plan');
 if(!Array.isArray(lines)||lines.length>1000)throw Error('lines');
 let subtotal=0n;
 for(const line of lines){
  if(line===null||Array.isArray(line)||typeof line!=='object'||Object.keys(line).sort().join(',')!=='quantity,unit_cents')throw Error('schema');
  if(!Number.isInteger(line.quantity)||line.quantity<1||line.quantity>4294967295||!Number.isInteger(line.unit_cents)||line.unit_cents<0||line.unit_cents>4294967295)throw Error('integer');
  const amount=BigInt(line.quantity)*BigInt(line.unit_cents);if(amount>4294967295n)throw Error('overflow');subtotal+=amount;if(subtotal>4294967295n)throw Error('overflow');
 }
 const rate=Number(words[8]),tax=(subtotal*BigInt(rate)+5000n)/10000n,total=subtotal+tax;
 if(total>4294967295n)throw Error('overflow');
 return {capability:'invoice.total@1',currency:words[6],lineCount:lines.length,subtotalCents:Number(subtotal),taxBps:rate,taxCents:Number(tax),totalCents:Number(total)};
}
if(process.argv[2]==='app'){
 try{console.log(JSON.stringify(invoice(fs.readFileSync(process.argv[3],'utf8'),JSON.parse(fs.readFileSync(process.argv[4],'utf8')))));}catch{process.exitCode=1;}
}else{
 const rl=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
 for await(const line of rl){let q;try{q=JSON.parse(line);if(q.method==='tools/list'){console.log(JSON.stringify({jsonrpc:'2.0',id:q.id,result:{tools:[explicitSchema]}}));continue;}const a=q.params.arguments;if(q.method!=='tools/call')throw Error('tool');let plan=a.plan;if(q.params.name==='invoice_total_explicit'){if(Object.keys(a).sort().join(',')!=='currency,lines,tax_bps'||typeof a.currency!=='string'||!Number.isInteger(a.tax_bps)||a.tax_bps<0||a.tax_bps>10000)throw Error('tool');plan=`rf2 app v1 invoice total currency ${a.currency} tax ${a.tax_bps} bps`;}else if(q.params.name!=='invoice_total'||Object.keys(a).sort().join(',')!=='lines,plan')throw Error('tool');const v=invoice(plan,a.lines);console.log(JSON.stringify({jsonrpc:'2.0',id:q.id,result:{content:[{type:'text',text:'Checked invoice total'}],structuredContent:v}}));}catch{console.log(JSON.stringify({jsonrpc:'2.0',id:q?.id??null,result:{content:[{type:'text',text:'Invalid invoice'}],isError:true}}));}}
}
