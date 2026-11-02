/* The same local command interface is backed by Android JNI or the bundled Windows host. */
export async function oralCall(method,args={}){
 const payload=JSON.stringify({method,args});let result;
 if(window.QihangNative?.oralCall)result=JSON.parse(window.QihangNative.oralCall(payload));
 else{const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);try{const response=await fetch('/oral-api',{method:'POST',credentials:'same-origin',signal:controller.signal,headers:{'Content-Type':'application/json'},body:payload});if(!response.ok)throw Error('口语连接已失效，请关闭旧窗口并重新启动 / Fermez l’ancienne fenêtre et relancez l’application.');result=await response.json();}catch(error){if(error.name==='AbortError')throw Error('口语连接等待超时，已有内容保留 / Connexion expirée, séance conservée.');if(error instanceof TypeError)throw Error('口语服务已断开，请重新双击启动文件 / Relancez l’application avec son lanceur.');throw error;}finally{clearTimeout(timer);}}
 if(!result.ok)throw Error(result.error||'操作未完成 / Opération incomplète.');return result.value;
}
