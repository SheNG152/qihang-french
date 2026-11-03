import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {primaryMeaning,primaryMeaningOptions} from '../src/domain/meanings.js';

const file=new URL('../src/static/lexicon/french.json',import.meta.url);
const data=JSON.parse(await fs.readFile(file,'utf8'));
const defaults={roman:'小说',combien:'多久'};
const generic=new Set(['一种','一个','某人','某物','某事','表示','用来','用于']);
let matched=0;
for(const row of data.entries){
 const zh=row.example?.zh||'',choices=primaryMeaningOptions(row);
 const ranked=choices.map((meaning,index)=>{
  const tokens=meaning.match(/[\u3400-\u9fff]{2,}/g)||[];
  const hits=tokens.filter(token=>token.length<=12&&!generic.has(token)&&zh.includes(token));
  return {meaning,index,score:hits.reduce((n,token)=>Math.max(n,token.length),0)};
 }).filter(item=>item.score>0).sort((a,b)=>b.score-a.score||a.index-b.index);
 if(!defaults[row.word]&&ranked[0]&&(!ranked[1]||ranked[0].score>ranked[1].score)){
  defaults[row.word]=ranked[0].meaning;matched++;
 }
 row.primaryMeaning=defaults[row.word]||primaryMeaning(row);
}
await fs.writeFile(file,JSON.stringify(data));
await fs.writeFile(new URL('../src/lexicon/contextual-primary-meanings.json',import.meta.url),JSON.stringify(defaults,null,2)+'\n');
const manifestFile=new URL('../src/static/lexicon/manifest.json',import.meta.url);
const manifest=JSON.parse(await fs.readFile(manifestFile,'utf8'));
manifest.sha256=createHash('sha256').update(await fs.readFile(file)).digest('hex');
manifest.supplement.reviewedPrimarySenses=51;
manifest.contextualPrimaryMeanings={matched,method:'Existing Chinese example matches a distinct dictionary sense; user overrides take priority.'};
await fs.writeFile(manifestFile,JSON.stringify(manifest,null,2)+'\n');
console.log(`Aligned ${matched} defaults to explicit Chinese example matches; roman and combien curated.`);
