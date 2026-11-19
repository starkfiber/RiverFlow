/** Beginner shortcuts use the existing RF2 form. They do not calculate app state. */
const root=document.getElementById('temperature-controls');
const help=document.getElementById('lesson-help');
const readings=[...document.querySelectorAll('[data-lesson-reading]')];
function form(){return root.querySelector('.rfui-input-form');}
function refresh(){const ready=form()?.querySelector('button')?.disabled===false;for(const button of readings)if(button.disabled===ready)button.disabled=!ready;}
for(const button of readings)button.addEventListener('click',()=>{const current=form();if(!current||current.querySelector('button').disabled)return;const input=current.querySelector('input');input.value=button.dataset.lessonReading;help.textContent=`Sent ${input.value} °C to the RF2 program. Read its response and history below.`;current.requestSubmit();});
document.getElementById('lesson-show-rules').addEventListener('click',()=>{const panel=root.querySelector('.rfui-panel');if(!panel){help.textContent='RF2 is still starting. Try again when the controls appear.';return;}panel.open=true;panel.scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});panel.querySelector('textarea').focus({preventScroll:true});help.textContent='The first rule panel is open. Change 18 to 21, then apply the rules and restart.';});
const observer=new MutationObserver(refresh);observer.observe(root,{childList:true,subtree:true,attributes:true,attributeFilter:['disabled']});refresh();
const heater=document.getElementById('heater-label'),state=document.getElementById('lesson-state');
const reflect=()=>{if(state.textContent!==heater.textContent)state.textContent=heater.textContent;};
const displayObserver=new MutationObserver(reflect);displayObserver.observe(heater,{childList:true,subtree:true,characterData:true});reflect();
window.addEventListener('pagehide',()=>{observer.disconnect();displayObserver.disconnect();},{once:true});
