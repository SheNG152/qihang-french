package cn.qihang.oral;
import org.json.*;
import java.io.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.nio.channels.*;
import java.time.*;
import java.util.concurrent.*;
final class ReviewReminders {
 private final File home,state,lock;private String registration="";
 ReviewReminders(File home,File data){this.home=home;state=new File(data,"review-reminder.json");lock=new File(data,"review-reminder.lock");}
 private static String day(){return LocalDate.now().toString();}
 synchronized boolean sync(JSONObject incoming)throws Exception{
  JSONArray dates=incoming.getJSONArray("dates");String time=incoming.optString("time","08:00");if(dates.length()>100000||!time.matches("(?:[01]\\d|2[0-3]):[0-5]\\d"))throw new IOException("提醒时间无效 / Heure invalide.");
  for(int i=0;i<dates.length();i++)LocalDate.parse(dates.getString(i));
  lock.getParentFile().mkdirs();try(RandomAccessFile f=new RandomAccessFile(lock,"rw");FileLock held=f.getChannel().lock()){JSONObject old=J.json(state);incoming.put("lastSent",old.optString("lastSent",""));J.atomic(state,J.bytes(incoming.toString()));}
  String config=incoming.optBoolean("enabled")+":"+time+":"+home.getCanonicalPath();boolean registered=true;
  if(!config.equals(registration)){
   String task="QihangFrenchReview";
   ProcessBuilder p;
   if(incoming.optBoolean("enabled")){
    String java=new File(home,"口语运行/runtime/bin/javaw.exe").getCanonicalPath(),cp=new File(home,"口语运行/qihang-oral.jar").getCanonicalPath()+";"+new File(home,"口语运行/json.jar").getCanonicalPath();
    File script=new File(state.getParentFile(),"review-reminder.ps1");
    String invoke="& '"+java.replace("'","''")+"' '-Dqihang.reminderOnly=true' '-cp' '"+cp.replace("'","''")+"' 'cn.qihang.oral.WindowsApp' '"+home.getCanonicalPath().replace("'","''")+"'\r\n";
    J.atomic(script,J.bytes("\uFEFF"+invoke));
    String command="powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File \""+script.getCanonicalPath()+"\"";
    p=new ProcessBuilder("schtasks.exe","/Create","/TN",task,"/TR",command,"/SC","DAILY","/ST",time,"/F","/RL","LIMITED","/IT");
   }else p=new ProcessBuilder("schtasks.exe","/Delete","/TN",task,"/F");
   Process process=p.redirectOutput(ProcessBuilder.Redirect.DISCARD).redirectError(ProcessBuilder.Redirect.DISCARD).start();registered=process.waitFor(12,TimeUnit.SECONDS)&&process.exitValue()==0;if(!registered)process.destroy();if(registered||!incoming.optBoolean("enabled"))registration=config;
  }
  check(false);return registered;
 }
 synchronized void check(boolean oneShot){
  try{lock.getParentFile().mkdirs();try(RandomAccessFile f=new RandomAccessFile(lock,"rw");FileLock held=f.getChannel().tryLock()){
   if(held==null)return;JSONObject v=J.json(state);String today=day();if(!v.optBoolean("enabled")||today.equals(v.optString("lastSent"))||LocalTime.now().isBefore(LocalTime.parse(v.optString("time","08:00"))))return;
   JSONArray dates=v.optJSONArray("dates");int n=0;for(int i=0;dates!=null&&i<dates.length();i++)if(dates.getString(i).compareTo(today)<=0)n++;if(n==0||!SystemTray.isSupported()||GraphicsEnvironment.isHeadless())return;
   BufferedImage image=new BufferedImage(32,32,BufferedImage.TYPE_INT_ARGB);Graphics2D g=image.createGraphics();g.scale(32.0/108,32.0/108);g.setColor(new Color(105,117,173));g.fillRoundRect(0,0,108,108,24,24);g.setColor(Color.WHITE);g.fillPolygon(new int[]{31,52,52,31},new int[]{39,45,78,71},4);g.fillPolygon(new int[]{56,77,77,56},new int[]{45,39,71,78},4);g.fillPolygon(new int[]{62,68,55,51},new int[]{23,29,38,34},4);g.dispose();
   TrayIcon icon=new TrayIcon(image,"启航法语");icon.setImageAutoSize(true);icon.addActionListener(e->{try{Desktop.getDesktop().open(new File(home,"启动启航法语.bat"));}catch(Exception ignored){}});SystemTray.getSystemTray().add(icon);icon.displayMessage("该复习法语啦 · À réviser !",n+" 个单词待复习 / "+n+" mots à réviser",TrayIcon.MessageType.INFO);
   v.put("lastSent",today);J.atomic(state,J.bytes(v.toString()));
   if(oneShot){Thread.sleep(15000);SystemTray.getSystemTray().remove(icon);}else{Thread cleanup=new Thread(()->{try{Thread.sleep(15000);}catch(InterruptedException ignored){}SystemTray.getSystemTray().remove(icon);},"review-toast");cleanup.setDaemon(true);cleanup.start();}
  }}catch(Exception ignored){}
 }
}
