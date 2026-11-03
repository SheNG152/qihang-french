package cn.qihang.oral;
public final class NativeSpeech {
 public static final String CPU_LIBRARY=NativeLibraries.load(System.getProperty("java.runtime.name","").contains("Android")||System.getProperty("java.vm.name","").contains("Dalvik"),new NativeLibraries.Loader(){
  public void load(String name){System.loadLibrary(name);}
  public int features(){return cpuFeatures();}
 });
 private static native int cpuFeatures();
 public static native String transcribe(String model,float[] samples,int threads);
 /** Load model before recording; true means a GPU warm-up is needed. */
 public static native boolean preload(String model);
 public static native void prepare();
 public static native int[] progress();
 /** load, inference, encoder, decoder ms, samples, threads, GPU used (1/0). */
 public static native long[] timings();
 public static native void cancel();
 public static native void release();
 public static native byte[] decode(byte[] opus,int rate,boolean reset);
 public static native byte[] protect(byte[] data,boolean decrypt);
}
