import assert from 'node:assert/strict';
import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from '@modelcontextprotocol/sdk/client/stdio.js';
const client = new Client({name:'native-independent-sdk', version:'1'});
try {
 await client.connect(new StdioClientTransport({command:process.env.RF2_TEST_BINARY??new URL('../../output/bin/rf2',import.meta.url).pathname,args:process.env.RF2_TEST_COMPACT==='1'?['mcp','--compact']:['mcp']}));
 const list=await client.listTools();assert.deepEqual(list.tools.map(t=>t.name),['0.8.0','0.9.0','0.10.0','0.11.0','0.12.0','0.13.0','0.14.0'].includes(process.env.RF2_TEST_VERSION)?['rf2_status','rf2_check','rf2_run','rf2_lower','attendance_export','invoice_total','invoice_prepare','invoice_apply','invoice_release']:process.env.RF2_TEST_VERSION==='0.7.0'?['rf2_status','rf2_check','rf2_run','rf2_lower','attendance_export','invoice_total']:process.env.RF2_TEST_VERSION==='0.6.0'?['rf2_status','rf2_check','rf2_run','rf2_lower','attendance_export']:['rf2_status','rf2_check','rf2_run']);
 const good=await client.callTool({name:'rf2_run',arguments:{source:'rf2 v1 checked\nsum input',data:[5,7,9]}});
 assert.equal(good.structuredContent.value,21);
 const bad=await client.callTool({name:'rf2_run',arguments:{source:'rf2 v1 checked\nsum input',data:[4294967295,1]}});assert.equal(bad.isError,true);
 const next=await client.callTool({name:'rf2_run',arguments:{source:'rf2 v1 wrap\nsquares input',data:[4294967295]}});assert.equal(next.structuredContent.value,1);
 if(['0.6.0','0.7.0','0.8.0','0.9.0','0.10.0','0.11.0','0.12.0','0.13.0','0.14.0'].includes(process.env.RF2_TEST_VERSION)){
  const {readFileSync}=await import('node:fs');const core=readFileSync(new URL('../../examples/sum.flow',import.meta.url),'utf8');
  const result=await client.callTool({name:'rf2_run',arguments:{source:core,data:[4,5,6]}});assert.equal(result.structuredContent.value,15);
  const lowered=await client.callTool({name:'rf2_lower',arguments:{source:core}});assert.ok(lowered.content[0].text.includes('fn cgn_entry'));
  const records=[{student_id:'TEST-SDK',date:'2026-11-12',status:'present'}];const exported=await client.callTool({name:'attendance_export',arguments:{records}});assert.equal(exported.structuredContent.present,1);
  const duplicate=await client.callTool({name:'attendance_export',arguments:{records:[...records,...records]}});assert.equal(duplicate.isError,true);
 }
 if(['0.7.0','0.8.0','0.9.0','0.10.0','0.11.0','0.12.0','0.13.0','0.14.0'].includes(process.env.RF2_TEST_VERSION)){
  const plan='rf2 app v1 invoice total currency MYR tax 600 bps';
  const invoice=await client.callTool({name:'invoice_total',arguments:{plan,lines:[{quantity:2,unit_cents:1250}]}});assert.equal(invoice.structuredContent.totalCents,2650);
  const refused=await client.callTool({name:'invoice_total',arguments:{plan:plan+' allow network',lines:[]}});assert.equal(refused.isError,true);
 }
 if(['0.8.0','0.9.0','0.10.0','0.11.0','0.12.0','0.13.0','0.14.0'].includes(process.env.RF2_TEST_VERSION)){
  const prepared=await client.callTool({name:'invoice_prepare',arguments:{plan:'rf2 app v1 invoice total currency MYR tax 600 bps'}});
  const applied=await client.callTool({name:'invoice_apply',arguments:{plan_id:prepared.structuredContent.plan_id,lines:[{quantity:1,unit_cents:100}]}});assert.equal(applied.structuredContent.totalCents,106);
  const released=await client.callTool({name:'invoice_release',arguments:{plan_id:prepared.structuredContent.plan_id}});assert.equal(released.structuredContent.released,true);
 }
 console.log('Independent MCP SDK: native discovery, result, refusal and recovery passed');
} finally { await client.close(); }
