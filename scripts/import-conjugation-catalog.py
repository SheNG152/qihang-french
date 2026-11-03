from pathlib import Path
import json,re,hashlib
root=Path(__file__).resolve().parents[1]
p=root/'.lexicon-work/en-fr.jsonl'
result={};ipa={}
people={('first-person','singular'):'je',('second-person','singular'):'tu',('third-person','singular'):'il',('first-person','plural'):'nous',('second-person','plural'):'vous',('third-person','plural'):'ils'}
if p.exists():
 for line in p.open(encoding='utf-8'):
  d=json.loads(line)
  if d.get('pos')!='verb' or not d.get('forms'):continue
  verb=d['word'];tenses={};part=None;aux=None
  for f in d['forms']:
   tags=set(f.get('tags',[]));text=f.get('form','')
   if tags=={'participle','past'} and re.fullmatch(r"[a-zA-ZÀ-ÿŒœÆæ'’ -]+",text):part=part or text
   if {'indicative','perfect','present','multiword-construction'}<=tags:
    if text=='present indicative of avoir + past participle':aux='avoir'
    elif text=='present indicative of être + past participle':aux='être'
   if 'indicative' not in tags or 'multiword-construction' in tags:continue
   tense='现在时' if 'present' in tags else '未完成过去时' if 'imperfect' in tags else None
   person=next((v for k,v in people.items() if set(k)<=tags),None)
   if not tense or not person or not re.fullmatch(r"[a-zA-ZÀ-ÿŒœÆæ'’ -]+",text):continue
   tenses.setdefault(tense,{}).setdefault(person,text)
   if f.get('ipa'):ipa.setdefault(text,f['ipa'].strip('/[]'))
  if part and aux:
   auxforms={'avoir':['ai','as','a','avons','avez','ont'],'être':['suis','es','est','sommes','êtes','sont']}[aux]
   tenses['复合过去时']={person:a+' '+part+('s' if aux=='être' and person in ['nous','vous','ils'] and not part.endswith('s') else '') for person,a in zip(['je','tu','il','nous','vous','ils'],auxforms) if person in tenses.get('现在时',{})}
  if tenses:result.setdefault(verb,tenses)
original=json.loads((root/'src/conjugation/source-catalog.json').read_text(encoding='utf-8'))
# Source tables take precedence over generic extracted constructions.
for verb,tenses in original.items():result.setdefault(verb,{}).update(tenses)
(root/'src/conjugation/catalog.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
base=json.loads((root/'src/conjugation/phonetics.json').read_text(encoding='utf-8'));ipa.update(base)
(root/'src/conjugation/phonetics.json').write_text(json.dumps(ipa,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
metadata={'source':'法语变位器3.0','sourceDirectory':'法语变位器3.0','sourceLicense':'MIT','supplement':'https://github.com/tatuylonen/wiktextract','data':'https://kaikki.org/dictionary/French/','extractionCommit':'19f9a3006a405fb7bfb40193dca41c7117a009a5','dataLicense':'CC-BY-SA-4.0','verbs':len(result),'dataSHA256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest() if p.exists() else None}
(root/'src/conjugation/sources.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
print('Conjugation catalog:',len(result),'verbs;',len(ipa),'pronunciations.')
