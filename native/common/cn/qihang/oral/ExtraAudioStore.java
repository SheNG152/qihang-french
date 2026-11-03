package cn.qihang.oral;
import org.json.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.zip.*;
/** Optional public recordings, isolated from recognition models and learning data. */
public final class ExtraAudioStore {
 private final JSONObject manifest;private final ModelStore archive;private final File directory;private final Map<String,JSONObject> files=new LinkedHashMap<>();private final ExecutorService worker=Executors.newSingleThreadExecutor();
 private final ScheduledExecutorService watcher=Executors.newSingleThreadScheduledExecutor();
 private volatile boolean ready,checking=true,installing,closed;private volatile String error="";
 public ExtraAudioStore(File root,JSONObject manifest)throws Exception{
  this.manifest=manifest;File base=new File(root,"extra-audio");directory=new File(base,"pack-v1");directory.mkdirs();archive=new ModelStore(base,manifest,false);
  JSONArray list=manifest.getJSONArray("files");for(int i=0;i<list.length();i++){JSONObject f=list.getJSONObject(i);String name=f.getString("name");if(!name.matches("[a-f0-9]{64}\\.mp3")||!name.equals(f.getString("sha256")+".mp3")||files.put(name,f)!=null)throw new IOException("语音包目录无效 / Index audio invalide.");}
  worker.submit(()->{try{verifyInstalled();ready=true;}catch(Exception ignored){}finally{checking=false;}});watcher.scheduleAtFixedRate(this::installIfReady,1,1,TimeUnit.SECONDS);
 }
 private void verifyInstalled()throws Exception{for(Map.Entry<String,JSONObject> e:files.entrySet()){if(closed)throw new IOException();File f=new File(directory,e.getKey());if(f.length()!=e.getValue().getLong("size")||!J.sha(f).equals(e.getValue().getString("sha256")))throw new IOException("语音包不完整 / Pack incomplet.");}}
 private synchronized void installIfReady(){if(closed||ready||checking||installing||!archive.status().optBoolean("ready"))return;installing=true;error="";worker.submit(()->{try{
  if(directory.getUsableSpace()<manifest.getLong("expandedSize")+64L*1024*1024)throw new IOException("存储空间不足 / Espace insuffisant.");
  try(ZipFile zip=new ZipFile(archive.model)){for(Map.Entry<String,JSONObject> e:files.entrySet()){if(closed)throw new IOException();ZipEntry entry=zip.getEntry("audio/"+e.getKey());long expected=e.getValue().getLong("size");if(entry==null||entry.getSize()!=expected)throw new IOException("语音包校验失败 / Pack audio invalide.");File temp=new File(directory,e.getKey()+".part");try(InputStream in=zip.getInputStream(entry);FileOutputStream out=new FileOutputStream(temp)){byte[] b=new byte[65536];long count=0;int n;while((n=in.read(b))!=-1){count+=n;if(count>expected)throw new IOException();out.write(b,0,n);}out.getFD().sync();}if(temp.length()!=expected||!J.sha(temp).equals(e.getValue().getString("sha256")))throw new IOException("语音包校验失败 / Pack audio invalide.");Files.move(temp.toPath(),new File(directory,e.getKey()).toPath(),StandardCopyOption.REPLACE_EXISTING);}}
  ready=true;archive.delete();
 }catch(Exception e){ready=false;error=J.safe(e);}finally{installing=false;}});}
 public JSONObject status(){installIfReady();try{JSONObject value=archive.status();String state=checking?"checking":installing?"installing":ready?"ready":!error.isEmpty()?"failed":value.optString("state");value.put("state",state).put("ready",ready).put("running",installing||value.optBoolean("running")).put("error",error.isEmpty()?value.optString("error").replace("模型","语音包").replace("Modèle","Pack audio"):error).put("expandedSize",manifest.optLong("expandedSize")).put("name","非课内语音包");if(ready)value.put("downloaded",manifest.optLong("size"));return value;}catch(Exception e){return J.o("state","failed","ready",false,"error",J.safe(e));}}

 public synchronized void start()throws Exception{if(checking||installing||ready)return;if(directory.getUsableSpace()<Math.max(0,manifest.getLong("size")-archive.status().optLong("downloaded"))+manifest.getLong("expandedSize")+64L*1024*1024)throw new IOException("存储空间不足 / Espace insuffisant.");error="";if(archive.status().optBoolean("ready"))installIfReady();else archive.start();}
 public void pause(){archive.pause();}
 public synchronized void importFrom(InputStream in)throws Exception{if(checking||installing||ready){in.close();throw new IOException("请等待当前操作结束 / Attendez la fin de l’opération.");}error="";archive.importFrom(in);}
 public synchronized void delete()throws Exception{if(checking||installing||archive.status().optBoolean("running"))throw new IOException("请先暂停下载 / Mettez le téléchargement en pause.");ready=false;archive.delete();for(String name:files.keySet()){Files.deleteIfExists(new File(directory,name).toPath());Files.deleteIfExists(new File(directory,name+".part").toPath());}error="";}
 public File file(String name){return ready&&files.containsKey(name)?new File(directory,name):null;}
 public String call(String payload){try{JSONObject request=new JSONObject(payload);String action=request.getString("action");if(action.equals("start"))start();else if(action.equals("pause"))pause();else if(action.equals("delete")){if(!request.optBoolean("confirmed"))throw new IOException("请确认删除 / Confirmez la suppression.");delete();}else if(!action.equals("status"))throw new IOException();return J.o("ok",true,"value",status()).toString();}catch(Exception e){return J.o("ok",false,"error",J.safe(e)).toString();}}
 public synchronized void close(){closed=true;watcher.shutdownNow();archive.close();worker.shutdown();}
}
