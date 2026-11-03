"""Supplement French headwords using Lexique 3.83 and attested bilingual glosses."""
import csv,gzip,bz2,hashlib,io,json,re,sys,zipfile,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'.lexicon-work';sys.path.insert(0,str(WORK/'python'))
from wordfreq import zipf_frequency
path=ROOT/'src/static/lexicon/french.json';original=json.loads(path.read_text(encoding='utf-8'));original['entries']=[r for r in original['entries'] if 'Lexique' not in r.get('source','')];known={r['word'] for r in original['entries']}
with zipfile.ZipFile(WORK/'Lexique383.zip') as z:
 lex={}
 for r in csv.DictReader(io.StringIO(z.read('Lexique383.tsv').decode('utf-8-sig')),delimiter='\t'):
  if r.get('lemme') and r['lemme'] not in lex:lex[r['lemme']]=r
english={}
for r in csv.DictReader((WORK/'ecdict.csv').open(encoding='utf-8-sig',newline='')):
 if r['word'].islower() and r['translation']:english[r['word']]=re.sub(r'\\+n','\n',r['translation'])
posmap={'verb':('v.',r'v[ti]?\.'),'noun':('n.',r'n\.'),'adj':('adj.',r'(?:a|adj)\.'),'adv':('adv.',r'(?:ad|adv)\.')}
extra={}
def chinese(gloss,pattern):
 clean=re.sub(r'\([^)]*\)','',gloss).strip();clean=re.sub(r'^(?:to|an?|the)\s+','',clean);clean=re.split(r'[,;:.(]',clean)[0].strip().lower()
 if clean not in english:return None
 for line in english[clean].splitlines():
  match=re.match(pattern+r'\s*(.+)',line,re.I)
  if match and re.search('[\u4e00-\u9fff]',match[1]):return re.sub(r'\[[^]]*\]','',match[1]).strip(),clean
 return None
for line in (WORK/'en-fr.jsonl').open(encoding='utf-8'):
 x=json.loads(line);word=x.get('word','');pos=x.get('pos')
 if word in known or word in extra or word not in lex or pos not in posmap or x.get('lang_code')!='fr' or zipf_frequency(word,'fr')<2.6 or not re.fullmatch(r"[a-zàâäæçéèêëîïôöœùûüÿ][a-zàâäæçéèêëîïôöœùûüÿ'’ -]{1,49}",word):continue
 senses=[s for s in x.get('senses',[]) if not s.get('form_of') and not set(s.get('tags',[]))&{'obsolete','archaic','rare','misspelling','form-of','nonstandard'}]
 match=None;gloss=''
 for sense in senses:
  for g in sense.get('glosses',[]):
   match=chinese(g,posmap[pos][1])
   if match:gloss=g;break
  if match:break
 if not match:continue
 ipa=next((s['ipa'] for s in x.get('sounds',[]) if s.get('ipa')),'')
 if not ipa:continue
 gender=lex[word].get('genre') or None
 row={'id':'lex'+hashlib.sha256(word.encode()).hexdigest()[:20],'word':word,'pos':posmap[pos][0],'gender':gender if gender in ['m','f'] else None,'meanings':[match[0]],'ipa':ipa,'frequency':zipf_frequency(word,'fr'),'source':'Wiktionary · Lexique · ECDICT','sourceUrl':'https://en.wiktionary.org/wiki/'+urllib.parse.quote(word),'glossEn':gloss,'translationPivot':match[1],'example':None}
 extra[word]=row
for line in bz2.open(WORK/'fra_sentences_detailed.tsv.bz2','rt',encoding='utf-8'):
 parts=line.rstrip('\n').split('\t')
 if len(parts)<4:continue
 text=parts[2]
 if not 12<len(text)<180:continue
 for token in set(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿœ]+",text.lower())):
  row=extra.get(token)
  if row and not row['example']:row['example']={'fr':text,'zh':'','source':f'Tatoeba #{parts[0]} · {parts[3]} · CC BY 2.0','url':'https://tatoeba.org/en/sentences/show/'+parts[0]}
# Reviewed common senses and original context sentences.
curated={
 'rester':{'pos':'v.','gender':None,'meanings':['留下；停留','保持某种状态；剩余'],'ipa':'/ʁɛs.te/','example':{'fr':'Je préfère rester à la maison ce soir.','zh':'今晚我更愿意待在家里。','authored':True,'source':'启航法语 · 例句'}},
 'radical':{'pos':'adj.','gender':None,'meanings':['根本的；彻底的','激进的','n.m. 词根；词干'],'ipa':'/ʁa.di.kal/','example':{'fr':'Ce projet exige un changement radical.','zh':'这个项目需要一次彻底的改变。','authored':True,'source':'启航法语 · 例句'}}
}
for word,fields in curated.items():
 row=extra.setdefault(word,{'id':'lex'+hashlib.sha256(word.encode()).hexdigest()[:20],'word':word,'frequency':zipf_frequency(word,'fr'),'source':'Wiktionary · Lexique','sourceUrl':'https://fr.wiktionary.org/wiki/'+word})
 row.update(fields)
accepted=[r for r in extra.values() if r.get('example') and (r['pos']!='n.' or r.get('gender'))]
original['entries']+=accepted;original['entries'].sort(key=lambda r:(-r.get('frequency',0),r['word']))
path.write_text(json.dumps(original,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
manifest=ROOT/'src/static/lexicon/manifest.json';m=json.loads(manifest.read_text(encoding='utf-8'));m['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();m['supplement']={'lexiqueRepository':'https://github.com/chrplr/openlexicon','lexiqueCommit':'9009f488f664536940965453c127f43cf18b84a4','ecdictRepository':'https://github.com/skywind3000/ECDICT','ecdictCommit':'39cfb9672c0906b63569e0453c2e6abfb9ab182a','added':len(accepted),'lexiqueSHA256':hashlib.sha256((WORK/'Lexique383.zip').read_bytes()).hexdigest(),'ecdictSHA256':hashlib.sha256((WORK/'ecdict.csv').read_bytes()).hexdigest()};m['stats']['words']=len(original['entries']);m['stats']['ipa']=len(original['entries']);m['stats']['examples']=len(original['entries']);m['stats']['translatedExamples']=sum(bool(r['example'].get('zh')) for r in original['entries']);m['stats']['authoredExamples']=sum(bool(r['example'].get('authored')) for r in original['entries']);manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'src/lexicon/reviewed-supplement.json').write_text(json.dumps(curated,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'added':len(accepted),'total':len(original['entries']),'requiredWords':{w:any(r['word']==w for r in original['entries']) for w in curated}},ensure_ascii=False),flush=True)
