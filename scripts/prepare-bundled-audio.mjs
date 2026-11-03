// Build-time asset preparation. Installed applications never download these files.
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Readable} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {unzipSync} from 'fflate';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const directory=path.join(root,'src/static/lexicon/audio');
const metadata=JSON.parse(await fs.readFile(path.join(root,'src/static/lexicon/manifest.json'),'utf8'));
const indexBytes=await fs.readFile(path.join(directory,'index.json'));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
if(hash(indexBytes)!==metadata.audio.indexSHA256)throw Error('Dictionary audio index is invalid.');
const index=JSON.parse(indexBytes),names=[...new Set(Object.values(index.entries).map(clip=>clip.file))];
if(names.length!==metadata.audio.files||names.some(name=>!(/^[a-f0-9]{64}\.mp3$/).test(name)))throw Error('Dictionary audio manifest is invalid.');
async function fileHash(file){const digest=createHash('sha256');for await(const chunk of createReadStream(file))digest.update(chunk);return digest.digest('hex');}
const missing=[];
for(const name of names){try{if(await fileHash(path.join(directory,name))+'.mp3'!==name)missing.push(name);}catch(error){if(error.code!=='ENOENT')throw error;missing.push(name);}}
if(missing.length){
 const cache=path.join(root,'.lexicon-work/public-audio-v1.zip');
 const archiveSize=317546497,archiveHash='86c70b42fdece8808447181dceded0b6ed8e0a53e6d4518b0576488b7520f951';
 const source='https://github.com/zyh307/qihang-french/releases/download/v2.2.0/QihangFrench-ExtraAudio-v1.zip';
 await fs.mkdir(path.dirname(cache),{recursive:true});
 let valid=false;try{valid=(await fs.stat(cache)).size===archiveSize&&await fileHash(cache)===archiveHash;}catch(error){if(error.code!=='ENOENT')throw error;}
 if(!valid){
  const partial=cache+'.part',response=await fetch(source,{signal:AbortSignal.timeout(30*60*1000)});
  if(!response.ok||!response.body)throw Error('Build audio archive could not be downloaded.');
  const expected=response.headers.get('content-length');if(expected&&Number(expected)!==archiveSize)throw Error('Build audio archive has an incorrect size.');
  const handle=await fs.open(partial,'w');try{await pipeline(Readable.fromWeb(response.body),handle.createWriteStream());}finally{await handle.close();}
  if((await fs.stat(partial)).size!==archiveSize||await fileHash(partial)!==archiveHash)throw Error('Build audio archive failed SHA-256 verification.');
  await fs.rename(partial,cache);
 }
 const wanted=new Set(missing.map(name=>'audio/'+name));
 const files=unzipSync(await fs.readFile(cache),{filter:entry=>wanted.has(entry.name)});
 for(const name of missing){const bytes=files['audio/'+name];if(!bytes||hash(bytes)+'.mp3'!==name)throw Error('Missing or damaged build recording: '+name);const target=path.join(directory,name);await fs.writeFile(target+'.part',bytes);await fs.rename(target+'.part',target);}
}
let bytes=0;for(const name of names)bytes+=(await fs.stat(path.join(directory,name))).size;
if(bytes!==metadata.audio.bytes)throw Error('Bundled recording size does not match the manifest.');
console.log(`Verified ${names.length} bundled audio files (${Object.keys(index.entries).length} clips, ${bytes} bytes).`);
