import assert from'node:assert/strict';
import {Client} from'@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from'@modelcontextprotocol/sdk/client/stdio.js';
import fs from'node:fs';
const dir=process.env.RF2_TRUST_DIR,key=process.env.RF2_TEST_KEY_FILE;
assert.ok(dir&&key,'Supply explicit native test binary directory and test key path');
const c=new Client({name:'rf2-trust-independent-sdk',version:'1'});
try{
 await c.connect(new StdioClientTransport({command:dir+'/rf2-trust',args:['mcp',key],env:{PATH:'/nonexistent'}}));
 assert.deepEqual((await c.listTools()).tools.map(x=>x.name),['contract_status','contract_run','contract_verify']);
 const plan='RF2E1 allow 7 budget 6 input 3 1 2 3 steps 1 xor 2\n';
 const run=await c.callTool({name:'contract_run',arguments:{plan}});assert.deepEqual(run.structuredContent.output,[3,0,1]);assert.equal(run.structuredContent.authenticated,true);
 const verified=await c.callTool({name:'contract_verify',arguments:{capsule:run.structuredContent.capsule}});assert.equal(verified.structuredContent.verified,true);
 const bad=await c.callTool({name:'contract_verify',arguments:{capsule:run.structuredContent.capsule.replace('tag ','tag f')}});assert.equal(bad.isError,true);
 const escaped=await c.callTool({name:'contract_run',arguments:{plan:'profile RF2_SYSTEM_A64_V1\nfn main()\n return 0\nend\n'}});assert.equal(escaped.isError,true);
 assert.equal((await c.callTool({name:'contract_status',arguments:{}})).structuredContent.callerFilesystem,false);
 console.log('Independent SDK: three native bounded tools, auth/semantics, refusal/recovery passed; server PATH=/nonexistent');
}finally{await c.close();}
