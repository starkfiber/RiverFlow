import assert from 'node:assert/strict';
import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from '@modelcontextprotocol/sdk/client/stdio.js';
const client = new Client({name:'native-independent-sdk', version:'1'});
try {
 await client.connect(new StdioClientTransport({command:process.env.RF2_TEST_BINARY??new URL('../../output/bin/rf2',import.meta.url).pathname,args:['mcp']}));
 const list=await client.listTools();assert.deepEqual(list.tools.map(t=>t.name),process.env.RF2_TEST_VERSION==='0.7.0'?['rf2_status','rf2_check','rf2_run','rf2_lower','attendance_export','invoice_total']:process.env.RF2_TEST_VERSION==='0.6.0'?['rf2_status','rf2_check','rf2_run','rf2_lower','attendance_export']:['rf2_status','rf2_check','rf2_run']);
 const good=await client.callTool({name:'rf2_run',arguments:{source:'rf2 v1 checked\nsum input',data:[5,7,9]}});
 assert.equal(good.structuredContent.value,21);
 const bad=await client.callTool({name:'rf2_run',arguments:{source:'rf2 v1 checked\nsum input',data:[4294967295,1]}});assert.equal(bad.isError,true);
 const next=await client.callTool({name:'rf2_run',arguments:{source:'rf2 v1 wrap\nsquares input',data:[4294967295]}});assert.equal(next.structuredContent.value,1);
 if(['0.6.0','0.7.0'].includes(process.env.RF2_TEST_VERSION)){
  const {readFileSync}=await import('node:fs');const core=readFileSync(new URL('../../examples/sum.flow',import.meta.url),'utf8');
  const result=await client.callTool({name:'rf2_run',arguments:{source:core,data:[4,5,6]}});assert.equal(result.structuredContent.value,15);
  const lowered=await client.callTool({name:'rf2_lower',arguments:{source:core}});assert.ok(lowered.content[0].text.includes('fn cgn_entry'));
  const records=[{student_id:'TEST-SDK',date:'2026-11-12',status:'present'}];const exported=await client.callTool({name:'attendance_export',arguments:{records}});assert.equal(exported.structuredContent.present,1);
  const duplicate=await client.callTool({name:'attendance_export',arguments:{records:[...records,...records]}});assert.equal(duplicate.isError,true);
 }
 if(process.env.RF2_TEST_VERSION==='0.7.0'){
  const plan='rf2 app v1 invoice total currency MYR tax 600 bps';
  const invoice=await client.callTool({name:'invoice_total',arguments:{plan,lines:[{quantity:2,unit_cents:1250}]}});assert.equal(invoice.structuredContent.totalCents,2650);
  const refused=await client.callTool({name:'invoice_total',arguments:{plan:plan+' allow network',lines:[]}});assert.equal(refused.isError,true);
 }
 console.log('Independent MCP SDK: native discovery, result, refusal and recovery passed');
} finally { await client.close(); }
