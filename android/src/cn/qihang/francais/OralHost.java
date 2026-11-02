package cn.qihang.francais;
import android.app.Activity;
import android.app.ActivityManager;
import android.content.*;
import android.security.keystore.*;
import java.io.*;
import java.security.KeyStore;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;
import cn.qihang.oral.*;
/** Android Keystore material is neither exported nor placed in WebView storage. */
final class OralHost implements Host {
 static final int IMPORT_MODEL=45;private final Activity activity;private final Runnable picker;private ModelStore importTarget;
 OralHost(Activity activity,Runnable picker){this.activity=activity;this.picker=picker;}
 private javax.crypto.SecretKey key()throws Exception{KeyStore store=KeyStore.getInstance("AndroidKeyStore");store.load(null);String alias="qihang-oral-binding-v1";if(!store.containsAlias(alias)){KeyGenerator g=KeyGenerator.getInstance("AES","AndroidKeyStore");g.init(new KeyGenParameterSpec.Builder(alias,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());g.generateKey();}return (javax.crypto.SecretKey)store.getKey(alias,null);}
 public byte[] protect(byte[] plain)throws Exception{Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,key());byte[] encrypted=c.doFinal(plain),iv=c.getIV(),out=new byte[1+iv.length+encrypted.length];out[0]=(byte)iv.length;System.arraycopy(iv,0,out,1,iv.length);System.arraycopy(encrypted,0,out,1+iv.length,encrypted.length);return out;}
 public byte[] unprotect(byte[] sealed)throws Exception{int size=sealed[0]&255;if(size!=12||sealed.length<30)throw new IOException();Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,sealed,1,size));return c.doFinal(sealed,1+size,sealed.length-1-size);}
 public long availableMemory(){ActivityManager.MemoryInfo info=new ActivityManager.MemoryInfo();((ActivityManager)activity.getSystemService(Context.ACTIVITY_SERVICE)).getMemoryInfo(info);return info.availMem;}
 public synchronized void importModel(ModelStore model)throws IOException{if(importTarget!=null)throw new IOException("请先完成当前导入 / Terminez l’importation.");importTarget=model;activity.runOnUiThread(picker);}
 public synchronized ModelStore takeImportTarget(){ModelStore value=importTarget;importTarget=null;return value;}
}
