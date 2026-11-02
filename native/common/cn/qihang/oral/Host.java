package cn.qihang.oral;
import java.io.*;
public interface Host {
 byte[] protect(byte[] plain)throws Exception;
 byte[] unprotect(byte[] sealed)throws Exception;
 void importModel(ModelStore store)throws Exception;
 long availableMemory();
}
