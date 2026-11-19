/* Browser-only teaching walkthrough, not an RF2 interpreter/compiler. No network calls. */
(() => {
 const $ = s => document.querySelector(s);
 const themeButton = $('#theme-toggle');
 let theme = 'light';
 try { theme = localStorage.getItem('rf2.theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); } catch (_) {}
 function setTheme(value) {
  document.documentElement.dataset.theme = value;
  themeButton?.setAttribute('aria-label', `Switch to ${value === 'light' ? 'dark' : 'light'} theme`);
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', value === 'light' ? '#f2f0e8' : '#101b20');
 }
 setTheme(theme);
 themeButton?.addEventListener('click', () => { theme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light'; setTheme(theme); try { localStorage.setItem('rf2.theme', theme); } catch (_) {} });
 const examples = {
  hello: {filename:'hello.flow', source:'say "Hello, world!"\n', explanation:'say displays a message. The quotes tell RF2 that these words are text.', steps:['Hello, world!\n']},
  points: {filename:'points.flow',source:'let points = 2\nset points = points + 3\nshow points\n',explanation:'let gives a value a name. set changes that value. show calculates and displays the answer.',steps:['No output yet. points remembers 2.','No output yet. points now remembers 5.','5\n']},
  age: {filename:'age.flow',source:'ask number age "How old are you?"\nshow age + 1\n',explanation:'ask number requests a whole number. The next line calculates one more than the answer.',steps:['How old are you?\n','answer']}
 };
 let selected='hello', step=0;
 function reset() {step=0;$('#step-count').textContent='READY';$('#trace-output').textContent='Your output will appear here.';$('#next-step').textContent='Show the example →';$('#next-step').disabled=false;}
 function select(name,focus=false) {
  if(!examples[name]) return;
  selected=name;const ex=examples[name];
  document.querySelectorAll('[data-example]').forEach(tab=>{const on=tab.dataset.example===name;tab.setAttribute('aria-selected',String(on));tab.tabIndex=on?0:-1;if(on&&focus)tab.focus();});
  $('#lesson-panel').setAttribute('aria-labelledby',`tab-${name}`);$('#lesson-filename').textContent=ex.filename;$('#lesson-source code').textContent=ex.source.trimEnd();$('#trace-explanation').textContent=ex.explanation;$('#example-input').hidden=name!=='age';$('#run-command').textContent=`./rf2 ${ex.filename}`;$('#download-source').href=`examples/${ex.filename}`;$('#download-source').download=ex.filename;reset();
 }
 document.querySelectorAll('[data-example]').forEach((tab,i,tabs)=>{
  tab.addEventListener('click',()=>select(tab.dataset.example));
  tab.addEventListener('keydown',e=>{let next;if(e.key==='ArrowRight')next=(i+1)%tabs.length;if(e.key==='ArrowLeft')next=(i+tabs.length-1)%tabs.length;if(e.key==='Home')next=0;if(e.key==='End')next=tabs.length-1;if(next!==undefined){e.preventDefault();select(tabs[next].dataset.example,true);}});
 });
 $('#reset-trace')?.addEventListener('click',reset);
 $('#age-input')?.addEventListener('input',()=>{reset();$('#age-input').removeAttribute('aria-invalid');});
 $('#next-step')?.addEventListener('click',()=>{
  const ex=examples[selected];let output=ex.steps[step];
  if(selected==='age'&&step===1){
   const raw=$('#age-input').value;
   if(!/^(0|[1-9][0-9]{0,19})$/.test(raw)||BigInt(raw)>18446744073709551615n){$('#trace-output').textContent='Use a whole number from 0 to 18446744073709551615, without leading zeros.';$('#age-input').setAttribute('aria-invalid','true');$('#age-input').focus();return;}
   const value=BigInt(raw);output=value===18446744073709551615n?'The answer is too large for this whole-number example.':`How old are you?\n${value+1n}\n`;
  }
  $('#trace-output').textContent=output;step++;$('#step-count').textContent=`STEP ${step} / ${ex.steps.length}`;
  $('#next-step').textContent=step>=ex.steps.length?'Example complete':'Next step →';$('#next-step').disabled=step>=ex.steps.length;
 });
 const copyFeedback = new WeakMap();
 async function copy(text,button) {
  let state = copyFeedback.get(button);
  if (!state) { state = {label:button.textContent,timer:0,ticket:0}; copyFeedback.set(button,state); }
  const ticket = ++state.ticket;
  clearTimeout(state.timer);
  try {
   if(!navigator.clipboard)throw Error('unavailable');
   await navigator.clipboard.writeText(text);
   if(state.ticket!==ticket)return;
   button.textContent='Copied ✓';$('#action-status').textContent='Copied to clipboard.';
  } catch(_) {
   if(state.ticket!==ticket)return;
   button.textContent='Select and copy the text';$('#action-status').textContent='Clipboard unavailable. Select the visible source or command and copy it.';
  }
  state.timer=window.setTimeout(()=>{if(state.ticket===ticket)button.textContent=state.label;},2200);
 }
 $('#copy-source')?.addEventListener('click',e=>copy(examples[selected].source,e.currentTarget));
 $('#copy-command')?.addEventListener('click',e=>copy(`./rf2 ${examples[selected].filename}`,e.currentTarget));
 if($('#lesson-panel'))select('hello');
})();
