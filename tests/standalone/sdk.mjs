import assert from 'node:assert/strict';
import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from '@modelcontextprotocol/sdk/client/stdio.js';
const client = new Client({name:'native-independent-sdk', version:'1'});
try {
 await client.connect(new StdioClientTransport({command:process.env.RF2_TEST_BINARY??new URL('../../output/bin/rf2',import.meta.url).pathname,args:['mcp']}));
 const list=await client.listTools();assert.deepEqual(list.tools.map(t=>t.name),['rf2_status','rf2_check','rf2_run']);
 const good=await client.callTool({name:'rf2_run',arguments:{source:'rf2 v1 checked\nsum input',data:[5,7,9]}});
 assert.equal(good.structuredContent.value,21);
 const bad=await client.callTool({name:'rf2_run',arguments:{source:'rf2 v1 checked\nsum input',data:[4294967295,1]}});assert.equal(bad.isError,true);
 const next=await client.callTool({name:'rf2_run',arguments:{source:'rf2 v1 wrap\nsquares input',data:[4294967295]}});assert.equal(next.structuredContent.value,1);
 console.log('Independent MCP SDK: native discovery, result, refusal and recovery passed');
} finally { await client.close(); }
