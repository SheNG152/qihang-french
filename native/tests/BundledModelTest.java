package cn.qihang.oral;
import java.io.*;
import java.nio.file.*;
import org.json.*;
public final class BundledModelTest {
 static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
 static JSONObject waitFor(ModelStore store)throws Exception{for(int n=0;n<300;n++){JSONObject s=store.status();if(!s.optString("state").equals("checking")&&!s.optString("state").equals("installing")&&!s.optBoolean("running"))return s;Thread.sleep(10);}throw new AssertionError("model operation stuck");}
 public static void main(String[] args)throws Exception{
  Path root=Files.createTempDirectory("bundled_model_test_");File bundled=root.resolve("package/models/ggml-model-q5_0.bin").toFile();bundled.getParentFile().mkdirs();Files.write(bundled.toPath(),new byte[]{1,2,3,4,5,6});
  JSONObject manifest=J.o("id","fixture","filename",bundled.getName(),"size",6,"sha256",J.sha(bundled),"revision","fixture","sources",new JSONArray().put(J.o("id","origin","url","https://example.invalid/model")));
  File data=root.resolve("data").toFile();ModelStore model=new ModelStore(data,manifest,false,bundled);
  require(waitFor(model).optBoolean("ready"),"fresh install did not find packaged model");
  require(model.model.equals(bundled),"bundle should be used directly, not copied into the user profile");
  require(model.status().getString("bundledPath").equals(bundled.getAbsolutePath())&&model.status().getString("path").equals(model.model.getAbsolutePath()),"paths not exposed");
  model.importFrom(new ByteArrayInputStream(new byte[]{9,9,9,9,9,9,9}));require(waitFor(model).optBoolean("ready"),"bad import lost old verified model");require(Files.mismatch(model.model.toPath(),bundled.toPath())==-1,"import modified packaged model");
  File session=new File(data,"sessions/keep.json");J.atomic(session,J.bytes("{\"score\":7}"));byte[] original=Files.readAllBytes(session.toPath());model.close();
  model=new ModelStore(data,manifest,false,bundled);require(waitFor(model).optBoolean("ready"),"reopening installation failed");require(java.util.Arrays.equals(original,Files.readAllBytes(session.toPath())),"history changed");
  boolean refused=false;try{model.delete();}catch(IOException expected){refused=true;}require(refused&&bundled.isFile()&&J.sha(bundled).equals(manifest.getString("sha256")),"bundled model deletion must be refused");model.close();
  File corrupt=root.resolve("corrupt.bin").toFile();Files.write(corrupt.toPath(),new byte[]{6,5,4,3,2,1});model=new ModelStore(root.resolve("invalid-data").toFile(),manifest,false,corrupt);require(waitFor(model).optString("state").equals("invalid")&&!model.status().optBoolean("ready"),"invalid bundle was accepted");model.close();
  model=new ModelStore(root.resolve("missing-data").toFile(),manifest,false,new File(root.toFile(),"absent.bin"));require(waitFor(model).optString("state").equals("missing"),"missing bundle not reported");model.close();
  System.out.println("Bundled model: 6 groups passed; isolated fixture, no model or personal data.");
 }
}
