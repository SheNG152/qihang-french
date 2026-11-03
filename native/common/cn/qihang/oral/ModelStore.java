package cn.qihang.oral;
import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.*;
/** Sources serve the same pinned bytes. A partial file is never an inference input. */
public final class ModelStore {
 public final File model;
 private final File partial,manifestFile,preference;
 private final JSONObject manifest;
 private final boolean inferenceModel;
 private final ExecutorService worker=Executors.newSingleThreadExecutor();
 private final AtomicBoolean inUse=new AtomicBoolean();
 private volatile String state="checking",error="",source="",sourceId="",failure="",selectedSource;
 private volatile boolean ready,paused,running;
 private boolean restartRequested,closed;
 private volatile HttpURLConnection connection;
 public ModelStore(File root,JSONObject manifest)throws Exception{
  this(root,manifest,true);
 }
 public ModelStore(File root,JSONObject manifest,boolean inferenceModel)throws Exception{
  this.manifest=manifest;this.inferenceModel=inferenceModel;File dir=new File(root,"models");dir.mkdirs();
  model=new File(dir,manifest.getString("filename"));partial=new File(dir,manifest.getString("filename")+".part");
  manifestFile=new File(dir,"verified.json");preference=new File(dir,"download-source.json");
  JSONArray configured=manifest.getJSONArray("sources");for(int i=0;i<configured.length();i++){JSONObject s=configured.getJSONObject(i);if(s.optString("id").isEmpty())s.put("id",s.optString("url").contains("hf-mirror.com")?"mirror":"origin");}
  selectedSource=hasSource("mirror")?"mirror":configured.getJSONObject(0).getString("id");
  try{String saved=J.json(preference).optString("id");if(hasSource(saved))selectedSource=saved;}catch(Exception ignored){}
  worker.submit(()->{try{if(model.isFile()){verify(model);ready=true;state="ready";}else state=partial.length()>0?"paused":"missing";}catch(Exception e){ready=false;state="invalid";error=J.safe(e);}});
 }
 private boolean hasSource(String id){JSONArray all=manifest.optJSONArray("sources");if(all!=null)for(int i=0;i<all.length();i++)if(id.equals(all.optJSONObject(i).optString("id")))return true;return false;}
 public JSONObject status(){
  JSONArray choices=new JSONArray(),all=manifest.optJSONArray("sources");
  for(int i=0;all!=null&&i<all.length();i++){JSONObject s=all.optJSONObject(i);choices.put(J.o("id",s.optString("id"),"name",s.optString("name")));}
  return J.o("state",state,"ready",ready&&!running&&"ready".equals(state),"running",running,"storedBytes",model.length()+partial.length(),"downloaded",ready&&!running?model.length():partial.length(),"total",manifest.optLong("size"),"error",error,"source",source,"sourceId",sourceId,"selectedSource",selectedSource,"sources",choices,"failure",failure,"domesticVerified",manifest.optBoolean("domesticDeploymentVerified"),"name",manifest.optString("id"));
 }
 private void verify(File f)throws Exception{if(f.length()!=manifest.getLong("size")||!J.sha(f).equals(manifest.getString("sha256")))throw new IOException("模型校验失败，请重新下载或导入 / Modèle invalide.");}
 public synchronized void start(){
  if(closed||running||ready||"checking".equals(state))return;
  running=true;paused=false;error="";failure="";state="connecting";
  worker.submit(()->{try{download();}catch(Throwable e){if(!paused){state="failed";error=J.safe(e);}}finally{boolean restart;synchronized(this){if(paused)state="paused";running=false;connection=null;restart=restartRequested&&!closed;restartRequested=false;}if(restart)start();}});
 }
 public synchronized void pause(){restartRequested=false;stopTransfer();}
 private void stopTransfer(){paused=true;HttpURLConnection c=connection;if(c!=null)c.disconnect();}
 public synchronized void selectSource(String id)throws Exception{
  if(!hasSource(id))throw new IOException("下载源不存在 / Source inconnue.");
  if(closed||inUse.get()||"checking".equals(state)||"verifying".equals(state)||"importing".equals(state))throw new IOException("请等待当前操作结束 / Attendez la fin de l’opération.");
  J.atomic(preference,J.bytes(J.o("id",id).toString()));selectedSource=id;error="";failure="";
  if(running){restartRequested=true;stopTransfer();}
 }
 public synchronized boolean acquire(){return ready&&!running&&"ready".equals(state)&&inUse.compareAndSet(false,true);}
 public void done(){inUse.set(false);}
 public String modelId(){return manifest.optString("id");}
 public long minimumMemory(){return manifest.optLong("minimumMemoryBytes",1800L*1024*1024);}
 public JSONObject description(){return J.o("id",modelId(),"label",manifest.optString("label",modelId()));}
 public synchronized void delete()throws Exception{
  if(running||inUse.get()||"checking".equals(state))throw new IOException("请等待校验、下载或识别结束 / Attendez la fin de l’opération.");
  if(inferenceModel)NativeSpeech.release();Files.deleteIfExists(model.toPath());Files.deleteIfExists(partial.toPath());Files.deleteIfExists(manifestFile.toPath());ready=false;error="";failure="";state="missing";
 }
 public synchronized void importFrom(InputStream in)throws Exception{
  if(in==null)throw new IOException("无法读取模型文件 / Fichier illisible.");
  if(closed||running||inUse.get()||"checking".equals(state)){in.close();throw new IOException("请等待校验、下载或识别结束 / Attendez la fin de l’opération.");}
  running=true;state="importing";error="";
  worker.submit(()->{try(InputStream stream=in){checkSpace(Math.max(0,manifest.optLong("size")-partial.length()));try(FileOutputStream out=new FileOutputStream(partial)){byte[] b=new byte[1024*1024];long count=0;int n;while((n=stream.read(b))!=-1){count+=n;if(count>manifest.optLong("size"))throw new IOException("模型大小不符 / Taille du modèle incorrecte.");out.write(b,0,n);}out.getFD().sync();}promote();}catch(Throwable e){state=ready?"ready":"invalid";error=J.safe(e);}finally{running=false;}});
 }
 private void checkSpace(long need)throws IOException{if(model.getParentFile().getUsableSpace()<Math.max(0,need)+128L*1024*1024)throw new IOException("存储空间不足 / Espace insuffisant.");}
 private void promote()throws Exception{
  state="verifying";verify(partial);if(inferenceModel)NativeSpeech.release();
  try{Files.move(partial.toPath(),model.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}catch(AtomicMoveNotSupportedException e){Files.move(partial.toPath(),model.toPath(),StandardCopyOption.REPLACE_EXISTING);}
  J.atomic(manifestFile,J.bytes(J.o("sha256",manifest.getString("sha256"),"revision",manifest.getString("revision")).toString()));ready=true;state="ready";error="";
 }
 private HttpURLConnection open(String address,long offset)throws Exception{
  URL url=new URL(address);long began=System.nanoTime();
  for(int i=0;i<8;i++){
   if(paused)throw new InterruptedIOException();
   if(System.nanoTime()-began>35000000000L)throw new SocketTimeoutException();
   if(!"https".equals(url.getProtocol()))throw new IOException("下载地址不安全 / Adresse non sécurisée.");
   HttpURLConnection c=(HttpURLConnection)url.openConnection();connection=c;c.setConnectTimeout(12000);c.setReadTimeout(18000);c.setInstanceFollowRedirects(false);c.setRequestProperty("Accept-Encoding","identity");
   if(offset>0)c.setRequestProperty("Range","bytes="+offset+"-");
   int code=c.getResponseCode();
   if(code>=300&&code<400){String next=c.getHeaderField("Location");c.disconnect();if(next==null)throw new IOException("下载源暂不可用 / Source indisponible.");url=new URL(url,next);continue;}
   return c;
  }
  throw new IOException("下载跳转过多 / Redirections excessives.");
 }
 private JSONArray orderedSources(){
  JSONArray all=manifest.optJSONArray("sources"),ordered=new JSONArray();String preferred=selectedSource;
  for(int pass=0;pass<2;pass++)for(int i=0;i<all.length();i++){JSONObject s=all.optJSONObject(i);if(s.optString("id").equals(preferred)==(pass==0))ordered.put(s);}
  return ordered;
 }
 private void download()throws Exception{
  JSONArray sources=orderedSources();Exception last=null;
  for(int i=0;i<sources.length()&&!paused;i++){
   JSONObject s=sources.getJSONObject(i);source=s.optString("name");sourceId=s.optString("id");state="connecting";
   try{
    long offset=partial.length(),total=manifest.getLong("size");
    if(offset>total){Files.delete(partial.toPath());offset=0;}
    if(offset==total){try{promote();return;}catch(Exception e){Files.deleteIfExists(partial.toPath());offset=0;state="connecting";}}
    checkSpace(total-offset);HttpURLConnection c=open(s.getString("url"),offset);int status=c.getResponseCode();boolean append=false;
    if(status==206){
     Matcher range=Pattern.compile("bytes (\\d+)-(\\d+)/(\\d+)").matcher(String.valueOf(c.getHeaderField("Content-Range")));
     if(!range.matches()||Long.parseLong(range.group(1))!=offset||Long.parseLong(range.group(3))!=total||Long.parseLong(range.group(2))>=total)throw new IOException("下载续传验证失败 / Reprise invalide.");
     append=offset>0;
    }else if(status==200){offset=0;long length=c.getContentLengthLong();if(length!=-1&&length!=total)throw new IOException("下载大小不符 / Taille incorrecte.");checkSpace(total);}
    else throw new IOException("下载源暂不可用 / Source indisponible.");
    try(InputStream in=c.getInputStream();FileOutputStream out=new FileOutputStream(partial,append)){
     byte[] b=new byte[131072];long count=offset;int n;
     while(!paused&&(n=in.read(b))!=-1){state="downloading";count+=n;if(count>total)throw new IOException("下载大小不符 / Taille incorrecte.");out.write(b,0,n);}
     out.getFD().sync();
    }finally{c.disconnect();}
    if(paused)return;promote();return;
   }catch(Exception e){
    last=e;failure=e instanceof SocketTimeoutException?"下载连接超时 / Connexion expirée.":e instanceof UnknownHostException?"无法连接下载源 / Source inaccessible.":J.safe(e);
    HttpURLConnection c=connection;if(c!=null)c.disconnect();
    if("verifying".equals(state)){Files.deleteIfExists(partial.toPath());state="connecting";}
   }
  }
  if(!paused)throw new IOException("下载源均未连接成功，可切换来源或稍后重试 / Changez de source ou réessayez.",last);
 }
 public synchronized void close(){closed=true;pause();worker.shutdown();}
}

