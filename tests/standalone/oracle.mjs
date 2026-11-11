// Development-only reference. Never loaded by the native executable.
import readline from 'node:readline';
import {compile,execute} from '../../src/riverflow.mjs';
for await (const line of readline.createInterface({input:process.stdin})) {
 try {const {source,data=[],count,mode}=JSON.parse(line);console.log(JSON.stringify(mode==='check'?(compile(source),{ok:true}):{ok:true,...execute(source,data,count??data.length)}));}
 catch(e){console.log(JSON.stringify({ok:false,error:e.message}));}
}
