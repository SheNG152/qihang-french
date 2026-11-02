package cn.qihang.oral;
import javax.net.ssl.*;
import java.io.*;
import java.net.*;
import java.security.*;
import java.util.*;
/** Minimal RFC6455 client, TLS endpoint identification, bounded frames and masked writes. */
public final class SecureSocket implements Closeable {
 public interface Listener{void text(String text)throws Exception;void binary(byte[] data)throws Exception;void closed();}
 private final SSLSocket socket;private final InputStream in;private final OutputStream out;private final Listener listener;
 private final SecureRandom random=new SecureRandom();private volatile boolean closed;
 public SecureSocket(String address,Map<String,String> headers,Listener listener)throws Exception{
  URI uri=new URI(address);if(!"wss".equals(uri.getScheme())||uri.getUserInfo()!=null||uri.getHost()==null)throw new IOException("连接地址无效 / Adresse invalide.");
  socket=(SSLSocket)SSLSocketFactory.getDefault().createSocket();socket.connect(new InetSocketAddress(uri.getHost(),uri.getPort()<0?443:uri.getPort()),15000);socket.setSoTimeout(45000);SSLParameters p=socket.getSSLParameters();p.setEndpointIdentificationAlgorithm("HTTPS");socket.setSSLParameters(p);socket.startHandshake();in=socket.getInputStream();out=socket.getOutputStream();this.listener=listener;
  byte[] nonce=new byte[16];random.nextBytes(nonce);String key=Base64.getEncoder().encodeToString(nonce),path=uri.getRawPath();if(path==null||path.isEmpty())path="/";if(uri.getRawQuery()!=null)path+="?"+uri.getRawQuery();
  StringBuilder request=new StringBuilder("GET "+path+" HTTP/1.1\r\nHost: "+uri.getHost()+(uri.getPort()>0?":"+uri.getPort():"")+"\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Key: "+key+"\r\n");
  for(Map.Entry<String,String> h:headers.entrySet()){if(h.getValue().matches(".*[\\r\\n].*"))throw new IOException();request.append(h.getKey()).append(": ").append(h.getValue()).append("\r\n");}request.append("\r\n");out.write(J.bytes(request.toString()));out.flush();
  ByteArrayOutputStream raw=new ByteArrayOutputStream();int tail=0,b;while((b=in.read())!=-1){raw.write(b);tail=(tail<<8)|b;if(tail==0x0d0a0d0a)break;if(raw.size()>16384)throw new IOException();}
  String response=new String(raw.toByteArray(),java.nio.charset.StandardCharsets.US_ASCII),accept=Base64.getEncoder().encodeToString(MessageDigest.getInstance("SHA-1").digest(J.bytes(key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")));Map<String,String> parsed=new HashMap<>();for(String line:response.split("\r\n")){int colon=line.indexOf(':');if(colon>0)parsed.put(line.substring(0,colon).toLowerCase(Locale.ROOT),line.substring(colon+1).trim());}
  if(!response.startsWith("HTTP/1.1 101 ")||!accept.equals(parsed.get("sec-websocket-accept"))||!"websocket".equalsIgnoreCase(parsed.get("upgrade"))||!String.valueOf(parsed.get("connection")).toLowerCase(Locale.ROOT).contains("upgrade")){close();throw new IOException("小智连接未成功 / Connexion refusée.");}
 }
 public void start(){Thread t=new Thread(()->{try{ByteArrayOutputStream fragments=null;int type=0;while(!closed){int a=read(),b=read(),opcode=a&15;if((a&0x70)!=0||(b&128)!=0)throw new IOException();long len=b&127;if(len==126)len=(read()<<8)|read();else if(len==127){len=0;for(int i=0;i<8;i++)len=(len<<8)|read();}if(len<0||len>4*1024*1024||opcode>=8&&(len>125||(a&128)==0))throw new IOException();byte[] data=new byte[(int)len];int at=0,n;while(at<data.length){n=in.read(data,at,data.length-at);if(n<0)throw new EOFException();at+=n;}if(opcode==8)break;if(opcode==9){frame(10,data);continue;}if(opcode==10)continue;if(opcode!=0){if(fragments!=null||opcode!=1&&opcode!=2)throw new IOException();type=opcode;fragments=new ByteArrayOutputStream();}if(fragments==null||fragments.size()+data.length>4*1024*1024)throw new IOException();fragments.write(data);if((a&128)!=0){byte[] full=fragments.toByteArray();fragments=null;if(type==1)listener.text(new String(full,java.nio.charset.StandardCharsets.UTF_8));else listener.binary(full);}}}catch(Exception ignored){}finally{close();listener.closed();}},"qihang-examiner");t.setDaemon(true);t.start();}
 private int read()throws IOException{int b=in.read();if(b<0)throw new EOFException();return b;}
 public synchronized void frame(int opcode,byte[] data)throws IOException{if(closed)throw new IOException("连接已断开 / Déconnecté.");out.write(128|opcode);int len=data.length;if(len<126)out.write(128|len);else if(len<65536){out.write(128|126);out.write(len>>8);out.write(len);}else{out.write(128|127);for(int i=7;i>=0;i--)out.write((int)((long)len>>(8*i)));}byte[] mask=new byte[4];random.nextBytes(mask);out.write(mask);byte[] payload=data.clone();for(int i=0;i<payload.length;i++)payload[i]^=mask[i%4];out.write(payload);out.flush();}
 public void send(String text)throws IOException{frame(1,J.bytes(text));}
 public void ping(){try{frame(9,new byte[0]);}catch(Exception e){close();}}
 public void close(){closed=true;try{socket.close();}catch(Exception ignored){}}
}
