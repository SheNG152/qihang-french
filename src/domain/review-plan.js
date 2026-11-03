// Day one is the learning day. Normal reviews never move with actual answers.
export const REVIEW_DAYS=[2,4,7,15,30];
const offsets=REVIEW_DAYS.map(n=>n-1);
const datePattern=/^\d{4}-\d{2}-\d{2}$/;
export function shiftDate(value,n){const d=new Date(value+'T12:00:00');d.setDate(d.getDate()+n);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;}
function elapsed(a,b){return Math.round((Date.parse(b+'T00:00:00Z')-Date.parse(a+'T00:00:00Z'))/86400000);}
export function newReviewRecord(today){return {learnedAt:today,reviewAnchor:today,scheduleVersion:2,reviewIndex:0,due:shiftDate(today,1),known:false};}
export function nextReviewDate(form,settings={}){if(!form||form.known)return null;const dates=[form.due,settings.reviewErrorRetry!==false?form.retryDue:null].filter(v=>datePattern.test(v||''));return dates.sort()[0]||null;}
export function nextNormalReview(anchor,today){
 const index=offsets.findIndex(n=>shiftDate(anchor,n)>today);
 if(index>=0)return {reviewIndex:index,due:shiftDate(anchor,offsets[index]),longReview:false};
 const cycle=Math.max(1,Math.floor((elapsed(anchor,today)-29)/30)+1);
 return {reviewIndex:offsets.length,due:shiftDate(anchor,29+cycle*30),longReview:true};
}
export function completeReviewRecord(form,settings,today,failed){
 const anchor=form.reviewAnchor||form.learnedAt;
 if(form.lastNormalReviewedAt!==today&&form.due&&form.due<=today){Object.assign(form,nextNormalReview(anchor,today));form.lastNormalReviewedAt=today;}
 if(form.retryDue&&form.retryDue<=today)delete form.retryDue;
 if(failed&&settings.reviewErrorRetry!==false)form.retryDue=shiftDate(today,1);
 form.lastReviewedAt=today;form.known=false;form.scheduleVersion=2;
}
export function migrateReviewPlans(data){
 for(const r of Object.values(data.progress||{}))for(const f of Object.values(r.forms||{})){
  if(!datePattern.test(f.learnedAt||''))continue;
  if(f.scheduleVersion===2)continue;
  const anchor=datePattern.test(r.learnedAt||'')?r.learnedAt:f.learnedAt;
  f.reviewAnchor=anchor;f.scheduleVersion=2;
  if(f.known){f.due=null;delete f.retryDue;continue;}
  const index=Math.max(0,Math.min(offsets.length,Number.isInteger(f.reviewIndex)?f.reviewIndex:0));f.reviewIndex=index;
  f.due=index<offsets.length?shiftDate(anchor,offsets[index]):shiftDate(anchor,59);
  if(index===offsets.length&&datePattern.test(r.lastPracticed||'')&&r.lastPracticed>=shiftDate(anchor,29))f.due=nextNormalReview(anchor,r.lastPracticed).due;
  f.longReview=index===offsets.length;
 }
}
