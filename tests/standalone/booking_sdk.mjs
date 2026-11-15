// Development-only independent MCP SDK interoperability check. Native server has no Node dependency.
import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from '@modelcontextprotocol/sdk/client/stdio.js';
import assert from 'node:assert/strict';
const [exe,journal,write] = process.argv.slice(2);
const transport = new StdioClientTransport({command:exe,args:[journal,...(write==='yes'?['--write']:[])],env:{PATH:'/nonexistent'},stderr:'pipe'});
const client=new Client({name:'rf2-booking-independent-sdk-test',version:'1'},{capabilities:{}});
let stderr='';transport.stderr?.on('data',c=>stderr+=c);
let checks=0;const check=(v)=>{assert(v);checks++;};
try {
 await client.connect(transport);
 const tools=await client.listTools();check(tools.tools.length===(write==='yes'?3:1));
 const read=await client.callTool({name:'booking_list',arguments:{}});check(!read.isError&&read.structuredContent.outcome==='read');
 check(/^[0-9a-f]{64}$/.test(read.structuredContent.snapshot_sha256));
 if(write==='yes') {
  const args={expected_revision:read.structuredContent.revision,id:'18446744073709551615',room:16,day:739938,start:0,finish:1440};
  const saved=await client.callTool({name:'booking_reserve',arguments:args});check(!saved.isError&&saved.structuredContent.outcome==='confirmed');
  check(saved.structuredContent.bookings.some(r=>r.id===args.id));
  const stale=await client.callTool({name:'booking_reserve',arguments:args});check(stale.isError&&stale.structuredContent.errorCode===409);
  const cancelled=await client.callTool({name:'booking_cancel',arguments:{expected_revision:saved.structuredContent.revision,id:args.id}});check(!cancelled.isError&&cancelled.structuredContent.bookings.length===0);
 } else {
  await assert.rejects(()=>client.callTool({name:'booking_reserve',arguments:{}}));checks++;
 }
 await client.ping();checks++;
} finally {await client.close();}
check(stderr==='');
console.log(JSON.stringify({checks,sdk:'@modelcontextprotocol/sdk@1.32.2',write:write==='yes'}));
