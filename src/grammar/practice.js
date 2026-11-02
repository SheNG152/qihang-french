// Question material is taken from the merged Inspire 1 grammar bank.
export function shuffle(list){const result=[...list];for(let i=result.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[result[i],result[j]]=[result[j],result[i]];}return result;}
export function buildQuestions(points){
 const pool=[];
 for(const point of points){
  const base={pointId:point.id,lessonId:point.lessonId,point};
  // An annotated comparison belongs in the source notes, not in a single-answer question.
  const exerciseText=text=>typeof text==='string'&&text.trim()&&!/[\p{Script=Han}×√/]/u.test(text);
  const mistakes=(point.mistakes||[]).filter(m=>m&&exerciseText(m.wrong)&&exerciseText(m.right));
  const wrongs=[...new Set(mistakes.map(m=>m.wrong).filter(Boolean))];
  const explain=point.rules?.[0]||point.hook||'';
  for(const [i,example] of (point.examples||[]).entries()){
   const [fr,zh]=example;if(!exerciseText(fr)||!zh)continue;
   const candidates=wrongs.filter(w=>w!==fr);
   if(!candidates.length)continue;
   const distractors=[...candidates.slice(i%candidates.length),...candidates.slice(0,i%candidates.length)].slice(0,2);
   if(!distractors.length)continue;
   const id=`${point.id}:translate:${i}`;
   pool.push({...base,id,type:'translate',prompt:zh,answer:fr,answerText:fr,explain,options:[fr,...distractors].map((text,n)=>({id:`${id}:${n}`,text,correct:n===0}))});
  }
  const seen=new Set(),truths=new Map();
  for(const m of mistakes)for(const [text,truth] of [[m.wrong,false],[m.right,true]]){if(!text)continue;const values=truths.get(text)||new Set();values.add(truth);truths.set(text,values);}
  for(const [i,m] of mistakes.entries())for(const [prompt,truth] of [[m.wrong,false],[m.right,true]]){
   if(!prompt||seen.has(prompt)||truths.get(prompt)?.size!==1)continue;seen.add(prompt);
   const id=`${point.id}:judge:${i}:${truth?1:0}`;
   pool.push({...base,id,type:'judge',prompt,answer:truth,answerText:m.right||prompt,explain:m.why||explain,options:[
    {id:`${id}:yes`,text:'正确 · Correct',correct:truth},
    {id:`${id}:no`,text:'需改正 · À corriger',correct:!truth},
   ]});
  }
 }
 return pool;
}
export function normalizeProgress(value,ids){
 const result={};if(!value||typeof value!=='object'||Array.isArray(value))return result;
 for(const id of ids){const item=value[id];if(!item||typeof item!=='object')continue;const count=n=>Number.isSafeInteger(n)&&n>=0?n:0;result[id]={r:count(item.r),w:count(item.w),at:Number.isFinite(item.at)?item.at:0};}
 return result;
}
export function isMastered(stat={}){const total=(stat.r||0)+(stat.w||0);return total>=2&&(stat.r||0)/total>=.6;}
