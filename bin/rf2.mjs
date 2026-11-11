#!/usr/bin/env node
import {readFileSync,writeFileSync} from 'node:fs';
import {compile,execute} from '../src/riverflow.mjs';
import {emitC} from '../src/native-c.mjs';
const [command,path,input='[]',output]=process.argv.slice(2);
try {
 if(!['check','run','compile','emit-c'].includes(command)||!path)throw new Error('Usage: rf2 check file.flow | run file.flow "[1,2,3]" | compile file.flow output.json | emit-c file.flow output.c');
 const source=readFileSync(path,'utf8');
 if(command==='run') console.log(JSON.stringify(execute(source,JSON.parse(input)),null,2));
 else if(command==='check'){compile(source);console.log('Valid RF² Core program');}
 else {if(process.argv.length<5)throw new Error('compile and emit-c require an explicit output path');writeFileSync(input,command==='emit-c'?emitC(source):JSON.stringify(compile(source),null,2)+'\n');console.log(`Wrote generated output to ${input}`);}
} catch(e){console.error(e.message);process.exitCode=1;}
