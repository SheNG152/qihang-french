"""Build a pinned local French lookup from Wiktextract, wordfreq and Tatoeba snapshots."""
import sys,json,re,bz2,gzip,hashlib,collections,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'.lexicon-work';sys.path.insert(0,str(WORK/'python'))
from wordfreq import zipf_frequency
from opencc import OpenCC
cc=OpenCC('t2s');entries={};posmap={'noun':'n.','verb':'v.','adj':'adj.','adv':'adv.','prep':'prép.','pron':'pron.','article':'art.','det':'art.','conj':'conj.','intj':'interj.','num':'num.','phrase':'loc.','prep_phrase':'loc.','unknown':'loc.'}
def senses(x):return [s for s in x.get('senses',[]) if not s.get('form_of') and not set(s.get('tags',[]))&{'obsolete','archaic','rare','dated','misspelling','nonstandard','alternative','form-of'}]
def add(x):
 word=x.get('word','').strip();ss=senses(x)
 if x.get('lang_code')!='fr' or not ss or x.get('pos') not in posmap or not re.fullmatch(r"[a-zàâäæçéèêëîïôöœùûüÿ][a-zàâäæçéèêëîïôöœùûüÿ’' -]{0,59}",word):return
 frequency=zipf_frequency(word,'fr')
 if frequency<2.6:return
 gloss=[cc.convert(g).strip() for s in ss for g in s.get('glosses',[]) if re.search('[\u4e00-\u9fff]',g) and len(g)<200]
 if not gloss:return
 row=entries.setdefault(word,{'word':word,'meanings':[],'pos':posmap[x['pos']],'ipa':'','gender':None,'example':None,'frequency':frequency,'source':'Wiktionary'})
 if row['pos']=='loc.' and x['pos']!='unknown':row['pos']=posmap[x['pos']]
 for g in gloss:
  if g not in row['meanings'] and len(row['meanings'])<4:row['meanings'].append(g)
 enrich(row,x)
def enrich(row,x):
 for sound in x.get('sounds',[]):
  if not row['ipa'] and sound.get('ipa'):row['ipa']=sound['ipa'].replace(chr(92),'/')
 tags=set(x.get('tags',[]))|{t for s in x.get('senses',[]) for t in s.get('tags',[])}
 if 'plural-only' in tags:row['plural']=True
 if not row['gender']:row['gender']='m' if 'masculine' in tags else 'f' if 'feminine' in tags else None
 for sense in senses(x):
  for e in sense.get('examples',[]):
   text=e.get('text','');zh=e.get('translation','')
   if not row['example'] and 15<len(text)<190 and row['word'].casefold() in text.casefold():row['example']={'fr':text,'zh':cc.convert(zh) if re.search('[\u4e00-\u9fff]',zh) else '', 'source':'Wiktionary · '+e.get('ref','')[:180]}
for name in ['zh-simp.jsonl','zh-trad.jsonl']:
 for l in (WORK/name).open(encoding='utf-8'):add(json.loads(l))
print('Chinese modern headwords',len(entries),flush=True)
attested=set()
for l in (WORK/'en-fr.jsonl').open(encoding='utf-8'):
 x=json.loads(l);row=entries.get(x.get('word'))
 if row:
  attested.add(row['word'])
  if row['pos']=='loc.' and x.get('pos') in posmap:row['pos']=posmap[x['pos']]
  enrich(row,x)
entries={k:v for k,v in entries.items() if k in attested}
if (WORK/'fr-fr.jsonl.gz').exists():
 print('Enriching French edition',flush=True)
 with gzip.open(WORK/'fr-fr.jsonl.gz','rt',encoding='utf-8') as data:
  for line in data:
   x=json.loads(line);row=entries.get(x.get('word'))
   if row:enrich(row,x)
ipa={}
for line in (WORK/'fr_FR-ipa.txt').read_text(encoding='utf-8').splitlines():
 fields=line.split('\t')
 if len(fields)>1:ipa[fields[0]]=fields[1]
for word,row in entries.items():
 if not row['ipa']:row['ipa']=ipa.get(word,'')

phrases=collections.defaultdict(list)
for word in entries:
 if ' ' in word or '-' in word or "'" in word or '’' in word:phrases[re.split(r"[ '’-]",word)[0]].append(word)
cmn={}
with bz2.open(WORK/'cmn_sentences.tsv.bz2','rt',encoding='utf-8') as f:
 for l in f:
  a=l.rstrip().split('\t');cmn[a[0]]=a[2]
links={}
with bz2.open(WORK/'fra-cmn_links.tsv.bz2','rt',encoding='utf-8') as f:
 for l in f:
  a=l.split();links.setdefault(a[0],a[1])
best={}
with bz2.open(WORK/'fra_sentences_detailed.tsv.bz2','rt',encoding='utf-8') as f:
 for l in f:
  a=l.rstrip().split('\t')
  if len(a)<4:continue
  sid,_,text,author=a[:4]
  if not author or author==r'\N' or not 22<=len(text)<=145:continue
  tokens=set(re.findall(r"[a-zàâäæçéèêëîïôöœùûüÿ]+(?:['’\-][a-zàâäæçéèêëîïôöœùûüÿ]+)*",text.casefold()))
  tokens|={piece for token in list(tokens) for piece in re.split("['’]",token)}
  candidates=set(tokens)
  for token in tokens:
   for phrase in phrases.get(token,[]):
    if re.search(r'(?<![a-zà-ÿœæ])'+re.escape(phrase.replace('’',"'"))+r'(?![a-zà-ÿœæ])',text.casefold().replace('’',"'")):candidates.add(phrase)
  for token in candidates:
   row=entries.get(token)
   if not row:continue
   score=(0 if sid in links else 100)+abs(len(text)-60)
   if token not in best or score<best[token][0]:best[token]=(score,{'fr':text,'zh':cc.convert(cmn.get(links.get(sid),'')),'source':'Tatoeba #'+sid+' · '+author+' · CC BY 2.0','url':'https://tatoeba.org/en/sentences/show/'+sid})
for word,(_,example) in best.items():
 row=entries[word]
 if not row['example'] or example['zh']:row['example']=example
authored=json.loads((ROOT/'src/lexicon/authored-examples.json').read_text(encoding='utf-8'))
supplemental_ipa=json.loads((ROOT/'src/lexicon/supplemental-ipa.json').read_text(encoding='utf-8'))
excluded=json.loads((ROOT/'src/lexicon/excluded-words.json').read_text(encoding='utf-8'))
corrections={
 'pouvoir toujours courir':['想也别想；别指望（口语）'],
 'garni':['配有……的；装饰过的；带家具的'],'puant':['发臭的；臭的'],
 'gouvernant':['统治者；执政者'],'débarqué':['已上岸的；已抵达的'],
 'vingt-et-un':['二十一'],
 'arrêter son char':['别胡说；停止夸大其词（口语）'],
 'bouillon-blanc':['毛蕊花'], 'cristal de roche':['水晶；无色透明石英'],
 'gymnastique artistique':['竞技体操'], 'surf des neiges':['单板滑雪'],
 'liquide de gaz naturel':['天然气凝液'], 'boîte postale':['邮政信箱'],
 'échéancier':['付款时间表；到期日明细表'], 'stylisé':['风格化的；经过艺术加工的'],
 'codifié':['规范化的；编纂成典的'], 'contentant':['令人满意的'],
 'actus':['新闻；时事（口语）'], 'assimilée':['被同化者（女性）'],
 'vous-autres':['你们（口语）'], 'nous-autres':['我们（口语）'],
 "s'il te plait":['请（非正式）'], "s'il vous plait":['请（礼貌用语）'],
 'svp':['请（s’il vous plaît 的缩写）'], 'clef de fa':['低音谱号'], 'clé de fa':['低音谱号'],
 "clé d'ut":['中音谱号'], 'écoeurant':['令人恶心的；令人反感的'],
 'pêcher en eaux troubles':['浑水摸鱼'], 'casse-noisettes':['榛子夹；胡桃夹'],
 'néonazi':['新纳粹主义的；新纳粹分子'], 'couteux':['昂贵的；花费大的'],
 'icone':['图标；圣像'], 'porto-ricain':['波多黎各的'],
 'appartenances':['附属建筑物'], 'priorité':['优先；优先权']
}
for word,row in entries.items():
 if word in authored:row['example']=authored[word]
 if not row['ipa'] and word in supplemental_ipa:row['ipa']=supplemental_ipa[word];row['ipaSource']='启航法语 · 音标补充'
 if word in corrections:row['meanings']=corrections[word]
 if word=='actus':row['plural']=True
 if word in ['garni','puant','débarqué']:row['pos']='adj.';row['gender']=None
 if word=='gouvernant':row['pos']='n.';row['gender']='m'
 # Here "la" names a musical note, rather than a feminine article.
 if word=='la majeur':row['pos']='loc.';row['gender']=None;row['literal']=True
entries={k:v for k,v in entries.items() if k not in excluded and not all('非标准' in m or '错误拼写' in m for m in v['meanings'])}
missing=[r['word'] for r in entries.values() if not r['ipa'] or not r['example']]
if missing:raise RuntimeError('Incomplete entries: '+repr(missing))
out=ROOT/'src/static/lexicon';out.mkdir(parents=True,exist_ok=True)
rows=sorted(entries.values(),key=lambda x:(-x['frequency'],x['word']))
# One compact dictionary loaded only when the import page is opened.
for i,row in enumerate(rows):row['id']='lex'+hashlib.sha256(row['word'].encode()).hexdigest()[:20];row['sourceUrl']='https://zh.wiktionary.org/wiki/'+urllib.parse.quote(row['word'])
raw=json.dumps({'schema':1,'entries':rows},ensure_ascii=False,separators=(',',':')).encode()
(out/'french.json').write_bytes(raw)
counts={'words':len(rows),'ipa':sum(bool(x['ipa']) for x in rows),'examples':sum(bool(x['example']) for x in rows),'translatedExamples':sum(bool(x['example'] and x['example']['zh']) for x in rows),'authoredExamples':sum(bool(x['example'] and x['example'].get('authored')) for x in rows)}
manifest={'schema':1,'sources':{'extractor':'https://github.com/tatuylonen/wiktextract','extractorCommit':'19f9a3006a405fb7bfb40193dca41c7117a009a5','wiktionaryDump':'2026-11-01','wordfreq':'3.1.1','frequencyCutoff':2.6,'ipaDictionaryCommit':(WORK/'ipa-commit.txt').read_text(encoding='utf-8'),'frenchEditionDump':'2026-10-01','tatoebaExport':'2026-10-31'},'stats':counts,'sha256':hashlib.sha256(raw).hexdigest(),'inputs':{n:hashlib.file_digest((WORK/n).open('rb'),'sha256').hexdigest() for n in ['zh-simp.jsonl','zh-trad.jsonl','en-fr.jsonl','fra_sentences_detailed.tsv.bz2','fra-cmn_links.tsv.bz2','cmn_sentences.tsv.bz2','fr_FR-ipa.txt']}}
if (WORK/'fr-fr.jsonl.gz').exists():manifest['inputs']['fr-fr.jsonl.gz']=hashlib.file_digest((WORK/'fr-fr.jsonl.gz').open('rb'),'sha256').hexdigest()
manifest['curation']={n:hashlib.file_digest((ROOT/'src/lexicon'/n).open('rb'),'sha256').hexdigest() for n in ['authored-examples.json','supplemental-ipa.json','excluded-words.json']}
manifest['sources']['editionDumps']={'zh':'2026-11-01','en':'2026-10-01','fr':'2026-10-01'}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(counts),flush=True)
