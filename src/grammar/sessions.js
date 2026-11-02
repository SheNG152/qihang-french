export function roundComplete(round){return !!round?.questions?.length&&round.results?.length===round.questions.length;}
function freezeQuestion(q){return {id:q.id,pointId:q.pointId,lessonId:q.lessonId,type:q.type,prompt:q.prompt,answer:q.answer,answerText:q.answerText,explain:q.explain||'',point:{id:q.pointId,title:q.point.title,raw:q.point.raw||'',hook:q.point.hook||'',unitId:q.point.unitId||''},options:q.options.map(o=>({id:o.id,text:o.text,correct:o.correct}))};}
function frozenQuestion(row){
 const q=row.material,text=(s,max,empty=false)=>typeof s==='string'&&s.length<=max&&(empty||s.trim().length>0);
 if(!q||q.id!==row.id||!text(q.id,256)||!text(q.pointId,256)||!text(q.lessonId,64)||!['translate','judge'].includes(q.type)||!text(q.prompt,4000)||!text(q.answerText,4000)||!text(q.explain,8000,true)||q.point?.id!==q.pointId||!text(q.point.title,500)||!text(q.point.hook,4000,true)||!text(q.point.raw,1000,true)||!text(q.point.unitId,64,true))throw Error();
 if(!Array.isArray(q.options)||q.options.length<2||q.options.length>4||q.options.filter(o=>o.correct===true).length!==1||new Set(q.options.map(o=>o.id)).size!==q.options.length||q.options.some(o=>!text(o.id,256)||!text(o.text,4000)||typeof o.correct!=='boolean'))throw Error();
 return freezeQuestion(q);
}
export function encodeRound(round){
 if(!round?.questions?.length)return null;
 return {kind:round.kind||'lesson',lessonKey:round.lessonKey||'',scopeLabel:round.scopeLabel||'',questions:round.questions.map(q=>({id:q.id,options:q.options.map(o=>o.id),material:freezeQuestion(q)})),index:round.index,pickedId:round.pickedId||'',answered:!!round.answered,results:round.results.map(r=>({id:r.question.id,pickedId:r.pickedId}))};
}
export function decodeRound(saved,byId){
 if(!saved||!Array.isArray(saved.questions)||!saved.questions.length||saved.questions.length>20||!Array.isArray(saved.results))return null;
 try{
  const questions=saved.questions.map(row=>{
   const q=row.material?frozenQuestion(row):byId.get(row.id);if(!q||!Array.isArray(row.options)||row.options.length!==q.options.length||new Set(row.options).size!==q.options.length)throw Error();
   const options=row.options.map(id=>{const option=q.options.find(o=>o.id===id);if(!option)throw Error();return option;});return {...q,options};
  });
  if(new Set(questions.map(q=>q.id)).size!==questions.length||!Number.isInteger(saved.index)||saved.index<0||saved.index>=questions.length)return null;
  const results=saved.results.map((row,i)=>{const q=questions[i],option=q?.options.find(o=>o.id===row.pickedId);if(!q||q.id!==row.id||!option)throw Error();return {question:q,pickedId:option.id,correct:option.correct};});
  if(results.length!==saved.index+(saved.answered?1:0))return null;
  if(saved.pickedId&&!questions[saved.index].options.some(o=>o.id===saved.pickedId))return null;
  if(saved.answered&&results.at(-1)?.pickedId!==saved.pickedId)return null;
  return {kind:['lesson','mixed','retry'].includes(saved.kind)?saved.kind:'lesson',lessonKey:typeof saved.lessonKey==='string'?saved.lessonKey:'',scopeLabel:typeof saved.scopeLabel==='string'?saved.scopeLabel:'',questions,index:saved.index,pickedId:saved.pickedId||'',answered:!!saved.answered,results};
 }catch{return null;}
}
const samePaper=(a,b)=>JSON.stringify(a.questions)===JSON.stringify(b.questions);
export const mixedUnit=round=>/ · (U[0-9]+)$/.exec(round?.scopeLabel||'')?.[1]||'all';
export function mixedForUnit(cache,unit){const r=cache.mixedByUnit?.[unit]||(mixedUnit(cache.mixed)===unit?cache.mixed:null);return r||null;}
export function rememberRound(cache,round){
 if(!round)return cache;
 if(round.kind==='mixed'){
  // An unfinished mixed paper cannot be overwritten by another paper.
  const unit=mixedUnit(round),previous=mixedForUnit(cache,unit);
  if(previous&&!roundComplete(previous)&&!samePaper(previous,round))return cache;
  return {...cache,mixed:round,mixedByUnit:{...cache.mixedByUnit,[unit]:round}};
 }
 if(round.kind==='lesson'&&round.lessonKey)return {...cache,lessons:{...cache.lessons,[round.lessonKey]:round}};
 return cache;
}
