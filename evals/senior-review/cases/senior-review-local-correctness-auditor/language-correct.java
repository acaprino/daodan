// store input always contains at least one element.
// Java source; same independent contracts, with complete accepted input handling.
import java.util.*;
class Subject {
  // Base-typed calls on Special return 10 for any Number.
  static class Base { int fee(Number n){return 0;} }
  static class Special extends Base { @Override int fee(Number n){return 10;} }
  // Equal ids are interchangeable in a HashSet.
  static class Key { final int id; Key(int i){id=i;} public boolean equals(Object o){return o instanceof Key && ((Key)o).id==id;} public int hashCode(){return Integer.hashCode(id);} }
  // Copy all bytes fitting destination, including shorter destinations.
  static void copy(byte[] src,byte[] dst){System.arraycopy(src,0,dst,0,Math.min(src.length,dst.length));}
  // Nonnegative ranges inside limit, including maximum int boundaries.
  static boolean fits(int offset,int length,int limit){return offset>=0 && length>=0 && offset<=limit && length<=limit-offset;}
  // Accepted String/Integer become trimmed textual representation.
  static String normalize(Object value){return String.valueOf(value).trim();}
  // Only strings are inserted.
  static List<String> names(){List<String> x=new ArrayList<>();x.add("42");return x;}
  // Return may be copy, so use actual Object[] storage for any object.
  static Object[] store(Object[] input,Object value){Object[] out=Arrays.copyOf(input,input.length,Object[].class);out[0]=value;return out;}
}

