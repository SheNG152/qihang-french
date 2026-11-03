import {nativeHost} from './native.js';
export async function extraAudioCall(action='status',confirmed=false){
 const host=nativeHost();if(action==='import'&&host?.importExtraAudio){host.importExtraAudio();return;}
 let result;if(host?.extraAudioCall)result=JSON.parse(host.extraAudioCall(JSON.stringify({action,confirmed})));
 else{const r=await fetch('/extra-audio-api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,confirmed})});if(!r.ok)throw Error('请使用完整安装包打开 / Ouvrez l’application installée.');result=await r.json();}
 if(!result.ok)throw Error(result.error||'语音包操作失败 / Opération impossible.');return result.value;
}
export function extraAudioURL(file){return new URL('extra-audio/'+file,document.baseURI);}
