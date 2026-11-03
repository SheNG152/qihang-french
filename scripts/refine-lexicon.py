import csv,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'.lexicon-work';path=ROOT/'src/static/lexicon/french.json';data=json.loads(path.read_text(encoding='utf-8'));english={}
for row in csv.DictReader((WORK/'ecdict.csv').open(encoding='utf-8-sig')):
 if row['word'].islower():english[row['word']]=re.sub(r'\\+n','\n',row['translation'])
patterns={'v.':r'v[ti]?\.', 'n.':r'n\.', 'adj.':r'(?:a|adj)\.', 'adv.':r'(?:ad|adv)\.'}
for row in data['entries']:
 if not row.get('translationPivot'):continue
 pattern=patterns.get(row['pos']);gloss=re.sub(r'\([^)]*\)','',row.get('glossEn','')).strip()
 for phrase in re.split('[,;]',gloss):
  phrase=re.sub(r'^(?:to|an?|the)\s+','',phrase.strip()).rstrip('.').lower();translation=english.get(phrase,'');meaning=None
  for line in translation.splitlines():
   match=re.match(pattern+r'\s*(.+)',line,re.I) if pattern else None
   if match:meaning=re.split('[,，;；]',match[1])[0].strip();break
  if not meaning and ' ' in phrase and re.fullmatch(r'[\u4e00-\u9fff，,；; 、]+',translation.strip()):meaning=re.split('[,，;；]',translation)[0]
  if meaning:row['meanings']=[meaning];row['translationPivot']=phrase;break
corrections=json.loads((ROOT/'src/lexicon/primary-sense-corrections.json').read_text(encoding='utf-8'))
for row in data['entries']:
 if row['word'] in corrections:
  row.update(corrections[row['word']]);row['reviewedPrimarySense']=True
  if row['pos']!='n.':row['gender']=None
path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
manifest=ROOT/'src/static/lexicon/manifest.json';m=json.loads(manifest.read_text(encoding='utf-8'));m['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();m['supplement']['reviewedPrimarySenses']=len(corrections);manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Reviewed primary senses:',len(corrections))
