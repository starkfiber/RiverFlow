import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
// Publishing dependency only, never required to execute RF2 programs.
const require = createRequire(import.meta.url);
let marked;
try { ({ marked } = require('marked')); }
catch { if (!process.env.RF2_MARKED_MODULE) throw Error('Install marked for book publishing, or select it with RF2_MARKED_MODULE'); ({ marked } = await import(process.env.RF2_MARKED_MODULE)); }
const root=path.resolve(process.argv[2] || '.');
const dir=path.join(root,'book/learning-edition-1');
const source=await readFile(path.join(dir,'README.md'),'utf8');
let body=marked.parse(source,{gfm:true});
const toc=[]; let heading=0;
body=body.replace(/<h2>(.*?)<\/h2>/g,(_,title)=>{const id='lesson-'+(++heading);toc.push(`<a href="#${id}">${title}</a>`);return `<h2 id="${id}">${title}</h2>`;});
const html=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RF2 From Zero | First Learning Edition</title><style>
:root{color-scheme:light dark;--paper:#fbfaf5;--ink:#202f36;--line:#d8dfdc;--code:#edf2ef;--link:#175c56}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:18px/1.7 system-ui,sans-serif}main{max-width:860px;margin:auto;padding:48px 28px 100px}h1{font-size:clamp(38px,6vw,62px);line-height:1.1;letter-spacing:-.04em}h2{margin-top:70px;font-size:30px;line-height:1.25;border-top:1px solid var(--line);padding-top:28px;scroll-margin-top:20px}a{color:var(--link);text-underline-offset:3px}pre{background:var(--code);padding:20px;overflow-x:auto;border-radius:10px;font:15px/1.65 ui-monospace,monospace}code{font-family:ui-monospace,monospace;font-size:.9em}table{display:block;overflow-x:auto;border-collapse:collapse;font-size:16px}td,th{padding:12px;text-align:left;border:1px solid var(--line)}nav{padding:20px;background:var(--code);border-radius:10px}nav a{display:block;font-size:15px;margin:5px 0}summary{cursor:pointer;font-weight:700}p{margin:20px 0}a:focus-visible,summary:focus-visible{outline:3px solid #bc6f16;outline-offset:4px}@media(prefers-color-scheme:dark){:root{--paper:#172327;--ink:#e4ede8;--line:#435454;--code:#223338;--link:#9ee2d1}}@media print{body{font:11pt/1.5 Georgia,serif;background:white;color:black}main{max-width:none;padding:0}h2{break-before:page}nav{display:none}pre{white-space:pre-wrap;overflow:visible}a{color:black}table{display:table;width:100%}tr,pre{break-inside:avoid}}
</style><main><nav aria-label="Chapter navigation"><details><summary>Contents · First Learning Edition</summary>${toc.join('\n')}</details></nav>${body}<footer><p>Original RF2 learning material · SFE · Version-bound examples and honest limits.</p></footer></main></html>`;
await writeFile(path.join(dir,'RF2-From-Zero.html'),html);
const publicHtml=html.replaceAll('href="../../','href="https://github.com/starkfiber/RiverFlow/blob/main/').replaceAll('href="examples/','href="https://github.com/starkfiber/RiverFlow/blob/main/book/learning-edition-1/examples/').replaceAll('href="VERIFICATION.json"','href="https://github.com/starkfiber/RiverFlow/blob/main/book/learning-edition-1/VERIFICATION.json"').replaceAll('href="RF2-From-Zero.html"','href="./"');
for (const target of ['site/learn','docs/learn']) { await mkdir(path.join(root,target),{recursive:true}); await writeFile(path.join(root,target,'index.html'),publicHtml); }
console.log(JSON.stringify({chapters:(source.match(/^## \d+\./gm)||[]).length,navigationEntries:toc.length,bytes:Buffer.byteLength(html)}));
