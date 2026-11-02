package cn.qihang.oral;
public final class NativeSpeech {
 static {System.loadLibrary("qihang_speech");}
 public static native String transcribe(String model,float[] samples,int threads);
 public static native void prepare();
 public static native int[] progress();
 public static native void cancel();
 public static native void release();
 public static native byte[] decode(byte[] opus,int rate,boolean reset);
 public static native byte[] protect(byte[] data,boolean decrypt);
}
