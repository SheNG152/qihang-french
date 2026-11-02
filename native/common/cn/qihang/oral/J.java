package cn.qihang.oral;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
public final class J {
 public static JSONObject o(Object... pairs){JSONObject o=new JSONObject();try{for(int i=0;i<pairs.length;i+=2)o.put(String.valueOf(pairs[i]),pairs[i+1]);return o;}catch(Exception e){throw new IllegalArgumentException(e);}}
 public static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
 public static byte[] read(InputStream in,int max)throws IOException{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){if(out.size()+n>max)throw new IOException("内容过大 / Contenu trop volumineux.");out.write(b,0,n);}return out.toByteArray();}
 public static JSONObject json(File f)throws Exception{if(!f.isFile())return o();return new JSONObject(new String(Files.readAllBytes(f.toPath()),StandardCharsets.UTF_8));}
 public static void atomic(File f,byte[] b)throws Exception{f.getParentFile().mkdirs();File tmp=new File(f.getPath()+".tmp");try(FileOutputStream out=new FileOutputStream(tmp)){out.write(b);out.getFD().sync();}try{Files.move(tmp.toPath(),f.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}catch(AtomicMoveNotSupportedException e){Files.move(tmp.toPath(),f.toPath(),StandardCopyOption.REPLACE_EXISTING);}}
 public static String hex(byte[] bytes){StringBuilder s=new StringBuilder();for(byte b:bytes)s.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return s.toString();}
 public static String sha(File f)throws Exception{MessageDigest hash=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[1024*1024];int n;while((n=in.read(b))!=-1)hash.update(b,0,n);}return hex(hash.digest());}
 public static String safe(Throwable e){String s=e.getMessage();return s!=null&&s.contains(" / ")?s:"操作未完成，请重试 / Réessayez.";}
}
