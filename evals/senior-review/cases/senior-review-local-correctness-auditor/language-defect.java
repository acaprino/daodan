// store input always contains at least one element.
// Java source fixtures. Each method's contract is independent; no execution claimed.
import java.util.*;
class Subject {
  // Base-typed calls on Special must return fee 10 for any Number.
  static class Base { int fee(Number n){return 0;} }
  static class Special extends Base { int fee(Integer n){return 10;} }
  // Keys with equal id must be interchangeable in a HashSet.
  static class Key { final int id; Key(int i){id=i;} public boolean equals(Object o){return o instanceof Key && ((Key)o).id==id;} }
  // Copy all bytes that fit destination; shorter destinations are valid.
  static void copy(byte[] src, byte[] dst){System.arraycopy(src,0,dst,0,src.length);}
  // Accept only nonnegative ranges wholly inside limit; Integer.MAX_VALUE is supported.
  static boolean fits(int offset,int length,int limit){return offset>=0 && length>=0 && offset+length<=limit;}
  // Accept String or Integer, return textual trimmed representation.
  static String normalize(Object value){return ((String)value).trim();}
  // Result must contain only Strings; callers read it as List<String>.
  static List<String> names(){List<String> x=new ArrayList<>(); List raw=x;raw.add(42);return x;}
  // Return an array containing supplied object at index zero; input may be String[].
  // Return may be a copy; callers use the returned array.
  static Object[] store(Object[] input,Object value){input[0]=value;return input;}
}

