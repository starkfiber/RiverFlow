// Explicit development test using the same TextMate/Oniguruma engines used by VS Code.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,mkdtempSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
const root=resolve(new URL('../..',import.meta.url).pathname),deps=process.env.RF2_EDITOR_TEST_DEPS;
assert(deps,'Select explicit development dependencies via RF2_EDITOR_TEST_DEPS');
const req=createRequire(join(resolve(deps),'package.json'));
const tm=req('vscode-textmate'),onig=req('vscode-oniguruma');
const wasm=readFileSync(req.resolve('vscode-oniguruma/release/onig.wasm'));await onig.loadWASM(wasm.buffer.slice(wasm.byteOffset,wasm.byteOffset+wasm.byteLength));
const grammarPath=join(root,'editors/vscode/syntaxes/riverflow.tmLanguage.json');
const registry=new tm.Registry({onigLib:Promise.resolve({createOnigScanner:p=>new onig.OnigScanner(p),createOnigString:s=>new onig.OnigString(s)}),loadGrammar:async scope=>scope==='source.riverflow'?tm.parseRawGrammar(readFileSync(grammarPath,'utf8'),grammarPath):null});
const grammar=await registry.loadGrammar('source.riverflow');assert(grammar);
const results=[];function check(name,v,detail){results.push({name,passed:!!v,detail});assert(v,name);}
function scopes(line,part,which=0){const pos=line.indexOf(part,which),r=grammar.tokenizeLine(line,tm.INITIAL);assert(pos>=0);return r.tokens.find(t=>t.startIndex<=pos&&t.endIndex>pos).scopes;}
for(const [line,part,scope]of [
 ['fn main(argc,argv)','main','entity.name.function'],['FUNCTION main(data:u32[]) RETURNS u32','main','entity.name.function'],['record Booking(id:u64)','Booking','entity.name.type'],['module booking_store','booking_store','entity.name.namespace'],['own rows=Bookings()','own','keyword.control.ownership'],['ok own rows:Bookings','own','keyword.control.ownership'],['let x=move(rows)','move','keyword.control.ownership'],['profile RF2_SYSTEM_A64_V1','RF2_SYSTEM_A64_V1','constant.language.profile'],['let x=true','true','constant.language.boolean'],['STEP read = LOAD WITH { array: data }','LOAD','support.function.core'],['let half=8//2','//','keyword.operator'],['let value=18446744073709551615','18446744073709551615','constant.numeric.integer'],['rf2 v1 checked','checked','keyword.control.compact'],['# தமிழ் comment if own 123','if','comment.line.number-sign'],['let name="தமிழ் # own 123"','#','string.quoted.double'],['let name="a\\" if # text"','if','string.quoted.double']])check('scope '+part+' in '+line,scopes(line,part).some(s=>s.startsWith(scope)),scopes(line,part));
for(const [line,part]of [['let iffy=1','iffy'],['let trueish=2','trueish'],['let recording=3','recording']])check('no keyword prefix leak '+part,!scopes(line,part).some(s=>s.startsWith('keyword.')||s.startsWith('constant.language')||s.startsWith('entity.name.type')));
check('integer division is never a comment',!scopes('let half=8//2','//').some(s=>s.startsWith('comment')));
const manifest=JSON.parse(readFileSync(join(root,'editors/vscode/package.json'))),lang=manifest.contributes.languages[0];check('canonical extensions only',JSON.stringify(lang.extensions)===JSON.stringify(['.flow','.rf2']));check('no executable extension or auto activation',!manifest.main&&!manifest.browser&&!manifest.activationEvents);check('grammar scope agrees',manifest.contributes.grammars[0].scopeName==='source.riverflow');
const files=execFileSync('git',['ls-files','-z'],{cwd:root,encoding:'utf8'}).split('\0').filter(p=>/\.(flow|rf2)$/.test(p));let lines=0;
for(const file of files){let state=tm.INITIAL;for(const line of readFileSync(join(root,file),'utf8').split('\n')){const r=grammar.tokenizeLine(line,state,1000);assert(!r.stoppedEarly,file);state=r.ruleStack;lines++;}}
check('tracked RF2 corpus tokenizes without engine timeout',files.length>100,{files:files.length,lines});
const snippets=JSON.parse(readFileSync(join(root,'editors/vscode/snippets/riverflow.json')));check('four explicit snippets',Object.keys(snippets).length===4);
if(process.env.RF2_EDITOR_COMPILER){const dir=mkdtempSync(join(root,'artifacts/editor-snippet-')),source=snippets['Native Systems entry'].body.join('\n').replace(/\$\{\d+:([^}]*)\}/g,'$1')+'\n';writeFileSync(join(dir,'main.flow'),source);execFileSync(resolve(process.env.RF2_EDITOR_COMPILER),[join(dir,'main.flow'),join(dir,'program'),'--opt']);execFileSync('/usr/bin/codesign',['-s','-',join(dir,'program')]);execFileSync(join(dir,'program'),[],{env:{PATH:'/nonexistent'}});check('expanded Systems entry compiles and executes natively',true);}
const report={checks:results.length,textmate:req('vscode-textmate/package.json').version,oniguruma:req('vscode-oniguruma/package.json').version,results};if(process.env.RF2_EDITOR_REPORT)writeFileSync(resolve(process.env.RF2_EDITOR_REPORT),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));registry.dispose();
