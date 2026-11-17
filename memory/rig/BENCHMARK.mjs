// Semantic port of the pinned Campfire benchmark; uses Node's built-in CDP
// transport instead of installing Puppeteer. This is not a 60x reproduction.
import fs from 'node:fs';
const endpoint=process.argv[2];
if(typeof WebSocket!=='function')throw new Error('Node built-in WebSocket unavailable');
const ws=new WebSocket(endpoint), pending=new Map(), events=[];let seq=0;
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
ws.onmessage=e=>{
  const m=JSON.parse(e.data);
  if(m.id){const p=pending.get(m.id);if(p){clearTimeout(p.timer);pending.delete(m.id);m.error?p.reject(new Error(JSON.stringify(m.error))):p.resolve(m.result);}}
  else events.push(m);
};
function cdp(method,params={},sessionId){
  return new Promise((resolve,reject)=>{const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(new Error('CDP deadline: '+method));},15000);
    pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));});
}
async function evaluate(expression,session){
  const r=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);
  if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
async function waitValue(expression,session,timeout=100){
  const end=performance.now()+timeout;
  while(performance.now()<end){if(await evaluate(expression,session))return;await new Promise(r=>setTimeout(r,1));}
  throw new Error('Official workload readiness deadline exceeded: '+expression);
}
const timings=[],began=performance.now();let activeContext;
try{
  for(let run=0;run<100;run++){
    const start=performance.now();
    activeContext=(await cdp('Target.createBrowserContext')).browserContextId;
    const {targetId}=await cdp('Target.createTarget',{url:'about:blank',browserContextId:activeContext});
    const {sessionId}=await cdp('Target.attachToTarget',{targetId,flatten:true});
    await cdp('Page.enable',{},sessionId);
    await cdp('Emulation.setDeviceMetricsOverride',{width:800,height:600,deviceScaleFactor:1,mobile:false},sessionId);
    const before=events.length;
    await cdp('Page.navigate',{url:'http://127.0.0.1:1234/campfire-commerce/'},sessionId);
    const deadline=performance.now()+15000;
    while(!events.slice(before).some(e=>e.sessionId===sessionId&&e.method==='Page.loadEventFired')){
      if(performance.now()>deadline)throw new Error('Load event deadline exceeded');
      await new Promise(r=>setTimeout(r,1));
    }
    await waitValue("document.querySelector('#product-price').textContent.length > 0",sessionId);
    await waitValue("document.querySelectorAll('#product-reviews > div').length > 0",sessionId);
    const result={};
    result.name=await evaluate("document.querySelector('#product-name').textContent",sessionId);
    result.price=parseFloat((await evaluate("document.querySelector('#product-price').textContent",sessionId)).substring(1));
    result.description=await evaluate("document.querySelector('#product-description').textContent",sessionId);
    result.image=await evaluate("document.querySelector('#product-image').getAttribute('src')",sessionId);
    result.related=await evaluate("Array.from(document.querySelectorAll('#product-related > div')).map(r=>({name:r.querySelector('h4').textContent,price:parseFloat(r.querySelector('p').textContent.substring(1)),image:r.querySelector('img').getAttribute('src')}))",sessionId);
    result.reviews=await evaluate("Array.from(document.querySelectorAll('#product-reviews > div')).map(r=>({name:r.querySelector('h4').textContent,text:r.querySelector('p').textContent}))",sessionId);
    if(result.price!==244.99||result.image!=='images/nomad_000.jpg'||result.related.length!==3||result.reviews.length!==3)throw new Error('Extraction mismatch');
    await cdp('Target.closeTarget',{targetId});await cdp('Target.disposeBrowserContext',{browserContextId:activeContext});activeContext=null;
    const duration=performance.now()-start;timings.push(duration);
    fs.appendFileSync('/out/BENCHMARK.jsonl',JSON.stringify({run,milliseconds:duration,result})+'\n');
  }
  fs.writeFileSync('/out/BENCHMARK_SUMMARY.json',JSON.stringify({state:'complete',runs:timings.length,total_ms:performance.now()-began,
    per_run_ms:timings,viewport:[800,600,1],source_commit:'a87412aebbeec8b6422337fca178fbb7e3ffc883',
    label:'Campfire workload port; current pins/test host/built-in CDP client; not original machine, versions or Puppeteer timings; not 60x reproduction'},null,2));
}finally{
  if(activeContext)await cdp('Target.disposeBrowserContext',{browserContextId:activeContext}).catch(()=>{});
  ws.close();
}
