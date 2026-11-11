#!/usr/bin/env node
import {readFileSync,writeFileSync} from 'node:fs';
import {compile,execute} from '../src/riverflow.mjs';
const [command,path,input='[]',output]=process.argv.slice(2);
try {
 if(!['check','run','compile'].includes(command)||!path)throw new Error('Usage: rf2 check file.flow | run file.flow "[1,2,3]" | compile file.flow output.json');
 const source=readFileSync(path,'utf8');
 if(command==='run') console.log(JSON.stringify(execute(source,JSON.parse(input)),null,2));
 else if(command==='check'){compile(source);console.log('Valid RF² Core program');}
 else {if(process.argv.length<5)throw new Error('compile requires an explicit output path');writeFileSync(input,JSON.stringify(compile(source),null,2)+'\n');console.log(`Wrote checked IR to ${input}`);}
} catch(e){console.error(e.message);process.exitCode=1;}
