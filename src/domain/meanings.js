import contextualMeanings from '../lexicon/contextual-primary-meanings.json' with {type:'json'};
function shortSense(value){
 return String(value||'').replace(/^:Template:[^ ]+\s*/,'').replace(/^(?:[a-z]+\.)+\s*/i,'').replace(/［[^］]*］|【[^】]*】|\[[^\]]*\]|〈[^〉]*〉|（[^）]*）|\([^)]*\)/g,'').split(/(?:adv|adj|n|v|loc|prép|art)\./i)[0].split(/[；;\n]/)[0].trim();
}
export function primaryMeaning(word){return shortSense(word?.primaryMeaning||word?.meanings?.[0]||'');}
export function primaryMeaningOptions(word){
 return [...new Set([word?.primaryMeaning,...(word?.meanings||[])].filter(Boolean).flatMap(value=>shortSense(value).split(/[，,]/)).map(value=>value.trim()).filter(Boolean))];
}
export function applyMeaningCorrections(data){
 for(const p of data.library)for(const w of p.words){
  if(w.conjugation)continue;
  const key=w.lexiconWord||w.forms?.[0]?.text?.replace(/^(?:un|le)\s+/i,'');
  if(key==='roman'&&!(w.meaningRevision>=1)){
   w.meanings=['小说',...w.meanings.filter(m=>m!=='小说')];w.pos='n.';w.sourcePos='n.';w.meaningRevision=1;
   for(const f of w.forms){f.gender='m';if(!f.audioKey||f.audioKey.startsWith('tts:'))f.audioKey='tts:'+encodeURIComponent('un roman');}
  }
  if(key==='combien'&&!w.meanings.includes('多久'))w.meanings=['多久','多少','多么',...w.meanings];
  if(!w.primaryMeaningChosen&&contextualMeanings[key]&&(w.lexiconWord||key==='roman'||key==='combien'))w.primaryMeaning=contextualMeanings[key];
 }
}
