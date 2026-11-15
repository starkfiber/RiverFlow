// Development oracle only. The native app has no JavaScript runtime dependency.
import fs from 'node:fs';
import assert from 'node:assert/strict';
const input=JSON.parse(fs.readFileSync(0,'utf8'));
assert.equal(input.schema,'rf2.document-audit.v2');
assert.ok(input.items.some(row=>row.matches===0));
assert.ok(input.items.some(row=>row.matches>0));
for(const row of input.items){
  if(row.matches===0) assert.equal(row.first_byte,null);
  else {
    assert.ok(Number.isSafeInteger(row.first_byte));
    assert.ok(row.first_byte>=0&&row.first_byte<65536);
  }
}
const roundtrip=JSON.parse(JSON.stringify(input));
assert.deepEqual(roundtrip,input);
// Negative control: the documented former u64 sentinel is not a safe JS integer.
const old=JSON.parse('{"first_byte":18446744073709551615}');
assert.equal(Number.isSafeInteger(old.first_byte),false);
assert.notEqual(old.first_byte,null);
process.stdout.write(JSON.stringify({schema:'rf2.document-audit.js-wire-test.v1',node:process.version,passed:true,absent:null,present:'safe integers',roundtrip:true,formerSentinelUnsafe:true})+'\n');
