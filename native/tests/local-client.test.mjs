import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';
import {webcrypto} from 'node:crypto';
import {performance} from 'node:perf_hooks';

const source=await fs.readFile(new URL('../../src/oral/local-client.js',import.meta.url),'utf8');
const bank=JSON.parse(await fs.readFile(new URL('../../src/oral/bank-full.json',import.meta.url),'utf8'));
async function fixture(jobs,options={}){
 const sessions=new Map(),nativeEvents=[],sent=[],polls=[],messages=[];
 let cursor=0,recording=0,recognizedAt=0,failedSaves=options.failedSaves||0;
 const call=async(method,args={})=>{
  if(method==='status')return{model:{ready:true},recognizer:{ready:options.prepared!==false},provider:{status:'connected',hasTask:false}};
  if(method==='events')return{cursor,events:nativeEvents.filter(e=>e.seq>args.after)};
  if(method==='session.save'){if(failedSaves-->0)throw Error('isolated storage failure');sessions.set(args.session.id,structuredClone(args.session));return{};}
  if(method==='session.get')return structuredClone(sessions.get(args.id));
  if(method==='record.begin')return{audio:'test-recording-'+(++recording)};
  if(method==='record.end')return{audio:'test-recording-'+recording,row:'row-'+recording,duration:2};
  if(method==='recognize'){recognizedAt=performance.now();return{job:'isolated-job',timeoutMs:10000};}
  if(method==='job'){polls.push(performance.now()-recognizedAt);return structuredClone(jobs.length>1?jobs.shift():jobs[0]);}
  if(method==='send'){
   sent.push(structuredClone(args));
   for(const event of [{type:'task_read',turn:args.task.turn_id},{type:'sentence',text:'Bonjour !'},{type:'turn_end',hasAudio:false}])nativeEvents.push({...event,seq:++cursor});
   return{submitted:true};
  }
  return{};
 };
 const window={};window.parent={postMessage(){}};
 const context=vm.createContext({window,parent:window.parent,document:{hidden:false,addEventListener(){}},location:{origin:'http://test.local',href:'http://test.local/static/oral/index.html'},fetch:async()=>({json:async()=>bank}),URL,Blob,setTimeout,clearTimeout,performance,crypto:webcrypto,structuredClone,btoa,atob,console});
 const module=new vm.SourceTextModule(source,{context,identifier:'local-client.js'});
 await module.link(()=>new vm.SyntheticModule(['oralCall'],function(){this.setExport('oralCall',call);},{context}));
 await module.evaluate();
 const channel=window.QihangOralClient.createSocket();channel.onmessage=e=>{if(typeof e.data==='string')messages.push(JSON.parse(e.data));};
 async function until(condition){const end=performance.now()+5000;while(!condition()){assert.ok(performance.now()<end,'test condition timed out');await new Promise(r=>setTimeout(r,5));}}
 async function command(action,expected='ack',values={}){const request=webcrypto.randomUUID();channel.send(JSON.stringify({action,request,mode:'practice',part:'intro',...values}));await until(()=>messages.some(m=>m.request===request));const reply=messages.find(m=>m.request===request);assert.equal(reply.type,expected,reply.message);}
 await until(()=>channel.readyState===1);if(!options.skipStart){await command('start','ack',options.startValues||{});await until(()=>!channel.inFlight);}
 return{channel,messages,polls,sent,sessions,until,command,client:window.QihangOralClient};
}

let passed=0;
{
 const t=await fixture([{state:'done',text:'Je suis étudiant.',elapsedMs:4,backend:'gpu',modelLoadMs:0,inferenceMs:3,encoderMs:2,decoderMs:1,threads:16}]);
 try{
  await t.command('record_start');await t.command('record_stop');await t.until(()=>t.sent.length===2);
  assert.equal(t.polls.length,1);assert.ok(t.polls[0]<250,`Ready result unnecessarily delayed ${t.polls[0]}ms`);
  await t.until(()=>!t.channel.inFlight);
  const saved=[...t.sessions.values()][0],row=saved.messages.find(m=>m.role==='user');
  assert.equal(row.confirmed_text,'Je suis étudiant.');assert.equal(row.audio,'test-recording-1');assert.equal(row.reply_delivered,true);
  assert.equal(row.recognition.backend,'gpu');assert.equal(row.recognition.model_load_ms,0);assert.equal(row.recognition.inference_ms,3);
  passed++;
 }finally{t.channel.close();}
}
{
 const t=await fixture([{state:'running',phase:'transcribing',elapsedMs:10},{state:'done',text:'Bonjour.',elapsedMs:100}]);
 try{
  await t.command('record_start');await t.command('record_stop');await t.until(()=>t.sent.length===2);
  assert.ok(t.polls[0]<250);assert.ok(t.polls[1]-t.polls[0]>=100&&t.polls[1]-t.polls[0]<400);
  passed++;
 }finally{t.channel.close();}
}
{
 const t=await fixture([{state:'failed',error:'isolated recognizer failure'}]);
 try{
  await t.command('record_start');await t.command('record_stop');await t.until(()=>t.channel.recognizingRow===null);
  assert.equal(t.sent.length,1,'Failed recognition must not be sent to the examiner');
  const saved=[...t.sessions.values()][0],row=saved.messages.find(m=>m.role==='user');
  assert.equal(row.audio,'test-recording-1');assert.equal(row.recognition_status,'failed');assert.equal(row.confirmation_status,'not_sent');
  passed++;
 }finally{t.channel.close();}
}
{
 const t=await fixture([],{prepared:false,skipStart:true});
 try{await t.command('start','error');assert.equal(t.sessions.size,0,'Preparation must not create a premature exam session');passed++;}
 finally{t.channel.close();}
}
{
 const t=await fixture([],{failedSaves:1,skipStart:true});
 try{
  await t.command('start','error');assert.equal(t.channel.session,null,'Failed save must not leave a phantom active session');
  assert.equal(t.sessions.size,0);assert.equal(t.sent.length,0,'Unsaved practice must not contact the examiner');
  await t.command('start');await t.until(()=>!t.channel.inFlight);
  assert.equal(t.sessions.size,1);assert.equal(t.sent.length,1,'Retry should open exactly one practice');passed++;
 }finally{t.channel.close();}
}
{
 const tails=new Set();
 for(let round=0;round<12;round++){
  const t=await fixture([],{startValues:{mode:round%2?'simulation':'practice',part:round%3?'intro':'full'}});
  try{
   if(t.channel.session.phase==='preparation'){await t.command('next');await t.until(()=>!t.channel.inFlight);}
   const plan=t.channel.session.intro_questions;
   assert.equal(plan.length,6);assert.equal(plan[0].topic,'identity');assert.equal(plan[0].question,'Comment vous appelez-vous ?');assert.equal(plan[1].topic,'age');
   assert.match(plan[1].question,/âge/);assert.ok(plan.slice(2).every(p=>!['identity','age'].includes(p.topic)));assert.equal(new Set(plan.map(p=>p.topic)).size,6);
   assert.equal(t.sent[0].task.intro_plan.topic,'identity');assert.match(t.sent[0].task.instruction,/先姓名、再年龄/);tails.add(JSON.stringify(plan.slice(2)));
  }finally{t.channel.close();}
 }
 assert.ok(tails.size>1,'Later themes should vary between rounds');passed++;
}
{
 const t=await fixture([{state:'done',text:"Je m'appelle Alex."},{state:'done',text:"J'ai vingt ans."}]);
 try{
  for(let n=2;n<=3;n++){await t.command('record_start');await t.command('record_stop');await t.until(()=>t.sent.length===n);await t.until(()=>!t.channel.inFlight);}
  assert.deepEqual(t.sent.slice(0,2).map(s=>s.task.intro_plan.topic),['identity','age']);assert.ok(!['identity','age'].includes(t.sent[2].task.intro_plan.topic));
  if(process.env.QIHANG_TASK_EVIDENCE)await fs.writeFile(process.env.QIHANG_TASK_EVIDENCE,JSON.stringify(t.sent.slice(0,3),null,2));passed++;
 }finally{t.channel.close();}
}
{
 const t=await fixture([{state:'done',text:"Je m'appelle Alex."},{state:'done',text:'Pouvez-vous répéter ?'},{state:'done',text:"J'ai 20 ans."}]);
 try{
  for(let n=2;n<=4;n++){await t.command('record_start');await t.command('record_stop');await t.until(()=>t.sent.length===n);await t.until(()=>!t.channel.inFlight);}
  assert.equal(t.sent[1].task.intro_plan.topic,'age');assert.equal(t.sent[2].task.intro_plan.topic,'age','Repeat request must not skip age');assert.ok(!['identity','age'].includes(t.sent[3].task.intro_plan.topic));passed++;
 }finally{t.channel.close();}
}
{
 for(const [text,skip] of [["Je m'appelle Alex, j'ai 20 ans.",true],["Je m'appelle Alex, j’ai vingt et un ans.",true],["Je m'appelle Alex, j'ai un frère de vingt ans.",false]]){
  const t=await fixture([{state:'done',text}]);
  try{await t.command('record_start');await t.command('record_stop');await t.until(()=>t.sent.length===2);assert.equal(t.sent[1].task.intro_plan.index,skip?2:1,'Only the candidate’s own volunteered age skips its question');}
  finally{t.channel.close();}
 }
 passed++;
}
{
 const t=await fixture([]);
 try{
  const old=structuredClone(t.channel.session);delete old.intro_plan_version;old.intro_questions=bank.intro.filter(r=>!['identity','age'].includes(r[0])).slice(0,6).map(([topic,,q])=>({topic,question:q[0]}));old.bank_version='20261031-a1-bank-1';old.original_score=7;
  const before=JSON.stringify(old.intro_questions);t.sessions.set(old.id,old);await t.command('restore','ack',{id:old.id});
  assert.equal(JSON.stringify(t.channel.session.intro_questions),before);assert.equal(t.channel.session.bank_version,old.bank_version);assert.equal(t.channel.session.original_score,7);
  await t.command('resume');await t.until(()=>!t.channel.inFlight);assert.equal(t.sent.at(-1).task.intro_plan.topic,'home');assert.equal(t.sent.at(-1).task.intro_plan.order_version,1);
  const bootstrap=await(await t.client.fetch('/api/bootstrap')).json();assert.equal(bootstrap.bank.intro_questions,44);passed++;
 }finally{t.channel.close();}
}
console.log(`Local client: ${passed} groups passed; isolated native bridge, no personal data.`);
