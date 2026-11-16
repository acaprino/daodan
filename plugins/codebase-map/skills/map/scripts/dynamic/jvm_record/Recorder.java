package daodan.record;

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Stream;

/**
 * What the instrumented classes call, on the bootstrap class path so every class loader sees it. JDK only.
 *
 * A thread's `pending` is the call site whose instruction is running. A method that starts takes it when the
 * site calls that name and descriptor (or the interface method a lambda or method reference implements; any
 * method for a reflective site) and, the first time for that pair, when the frame under it is the site's method
 * at the site's line: so a method reached through a library frame is not the site's callee. StackWalker hides
 * reflection and lambda frames, so a method called by reflection or through a lambda object is the site's.
 * A site that returns still pending ran outside the instrumented classes. Each new fact is one line, written
 * and flushed at once: a killed JVM loses nothing.
 */
public final class Recorder {
    private static final class State {
        int pending;
        boolean busy;
    }

    private static final ThreadLocal<State> STATE = new ThreadLocal<State>() {
        @Override
        protected State initialValue() {
            return new State();
        }
    };
    private static final StackWalker WALKER = StackWalker.getInstance();
    // Frames from the walk: caller(), enter(), the method that starts, then its caller.
    private static final Function<Stream<StackWalker.StackFrame>, Optional<StackWalker.StackFrame>> CALLER =
        new Function<Stream<StackWalker.StackFrame>, Optional<StackWalker.StackFrame>>() {
            @Override
            public Optional<StackWalker.StackFrame> apply(Stream<StackWalker.StackFrame> frames) {
                return frames.skip(3).findFirst();
            }
        };
    private static final Object LOCK = new Object();
    /** The signature of a reflective call site (`Method.invoke`): any method but a class initializer. */
    public static final int ANY = 0;
    public static final int CLASS_INIT = 1;

    // Indexed by method id, from 1.
    private static volatile int[] methodSig = new int[1024];
    private static volatile int[][] methodAlias = new int[1024][];
    private static volatile String[] methodClass = new String[1024];
    private static volatile String[] methodName = new String[1024];
    private static volatile String[] methodDesc = new String[1024];
    // Indexed by site id, from 1.
    private static volatile int[] siteSig = new int[1024];
    private static volatile int[] siteMethod = new int[1024];
    private static volatile int[] siteLine = new int[1024];
    private static volatile boolean[] outside = new boolean[1024];
    // The pairs (site, method) already written: open addressing, 0 is empty.
    private static volatile long[] pairs = new long[1 << 12];
    private static int pairCount;

    private static String folder;
    private static String header;
    private static OutputStream out;

    private Recorder() {
    }

    public static void open(String outFolder, String headerLine) {
        folder = outFolder;
        header = headerLine;
    }

    public static void method(int id, String className, String name, String desc, int sig) {
        synchronized (LOCK) {
            if (id >= methodSig.length) {
                int size = Math.max(id + 1, methodSig.length * 2);
                methodAlias = Arrays.copyOf(methodAlias, size);
                methodClass = Arrays.copyOf(methodClass, size);
                methodName = Arrays.copyOf(methodName, size);
                methodDesc = Arrays.copyOf(methodDesc, size);
                methodSig = Arrays.copyOf(methodSig, size);
            }
            methodClass[id] = className;
            methodName[id] = name;
            methodDesc[id] = desc;
            methodSig[id] = sig;
            methodSig = methodSig;  // publishes the entries
        }
    }

    /** `sig`, the interface method a lambda or method reference to method `id` implements, also names it. */
    public static void alias(int id, int sig) {
        synchronized (LOCK) {
            int[] old = methodAlias[id];
            int[] grown = old == null ? new int[1] : Arrays.copyOf(old, old.length + 1);
            grown[grown.length - 1] = sig;
            methodAlias[id] = grown;
            methodAlias = methodAlias;
        }
    }

    public static void site(int id, int method, int line, int sig) {
        synchronized (LOCK) {
            if (id >= siteSig.length) {
                int size = Math.max(id + 1, siteSig.length * 2);
                siteMethod = Arrays.copyOf(siteMethod, size);
                siteLine = Arrays.copyOf(siteLine, size);
                outside = Arrays.copyOf(outside, size);
                siteSig = Arrays.copyOf(siteSig, size);
            }
            siteMethod[id] = method;
            siteLine[id] = line;
            siteSig[id] = sig;
            siteSig = siteSig;
        }
    }

    /** Before a call instruction: the site is pending; the caller keeps what was. */
    public static int call(int site) {
        State state = STATE.get();
        int before = state.pending;
        state.pending = site;
        return before;
    }

    /** After a call instruction returned. */
    public static void after(int before, int site) {
        State state = STATE.get();
        if (state.pending == site && !outside[site]) {
            synchronized (LOCK) {
                if (!outside[site]) {
                    outside[site] = true;
                    write("{\"outside\":" + site + "}");
                }
            }
        }
        state.pending = before;
    }

    /** A method starts. */
    public static void enter(int method) {
        State state = STATE.get();
        int site = state.pending;
        if (site == 0 || state.busy) {
            return;
        }
        long pair = ((long) site << 32) | method;
        if (known(pair)) {
            state.pending = 0;
            return;
        }
        int sig = siteSig[site];
        if (sig == ANY ? methodSig[method] == CLASS_INIT : sig != methodSig[method] && !aliased(method, sig)) {
            return;
        }
        state.busy = true;
        try {
            if (!called(site)) {
                return;
            }
            state.pending = 0;
            synchronized (LOCK) {
                if (add(pair)) {
                    write("{\"call\":[" + site + "," + method + "]}");
                }
            }
        } finally {
            state.busy = false;
        }
    }

    private static boolean aliased(int method, int sig) {
        int[] aliases = methodAlias[method];
        if (aliases != null) {
            for (int alias : aliases) {
                if (alias == sig) {
                    return true;
                }
            }
        }
        return false;
    }

    /** Whether the frame under the method that starts is the site's method, at the site's line. */
    private static boolean called(int site) {
        StackWalker.StackFrame frame = WALKER.walk(CALLER).orElse(null);
        int method = siteMethod[site];
        return frame != null && frame.getLineNumber() == siteLine[site]
            && frame.getMethodName().equals(methodName[method])
            && frame.getClassName().equals(methodClass[method])
            && frame.getDescriptor().equals(methodDesc[method]);
    }

    private static boolean known(long pair) {
        long[] table = pairs;
        int mask = table.length - 1;
        for (int at = slot(pair) & mask; table[at] != 0; at = (at + 1) & mask) {
            if (table[at] == pair) {
                return true;
            }
        }
        return false;
    }

    private static int slot(long pair) {
        long mixed = pair * 0x9E3779B97F4A7C15L;
        return (int) (mixed >>> 32);
    }

    // Under LOCK. A reader sees the old table or the new one, each complete.
    private static boolean add(long pair) {
        if (known(pair)) {
            return false;
        }
        long[] table = pairs;
        if (++pairCount * 2 > table.length) {
            long[] grown = new long[table.length * 2];
            for (long old : table) {
                if (old != 0) {
                    put(grown, old);
                }
            }
            table = grown;
        }
        put(table, pair);
        pairs = table;
        return true;
    }

    private static void put(long[] table, long pair) {
        int mask = table.length - 1;
        int at = slot(pair) & mask;
        while (table[at] != 0) {
            at = (at + 1) & mask;
        }
        table[at] = pair;
    }

    /** One line of the JVM's file, opened at the first line with the header. */
    public static void write(String line) {
        synchronized (LOCK) {
            try {
                if (out == null) {
                    if (folder == null) {
                        return;
                    }
                    new File(folder).mkdirs();
                    String name = ProcessHandle.current().pid() + "-" + System.currentTimeMillis() + ".jsonl";
                    out = new BufferedOutputStream(new FileOutputStream(new File(folder, name)), 1 << 16);
                    out.write((header + "\n").getBytes(StandardCharsets.UTF_8));
                }
                out.write((line + "\n").getBytes(StandardCharsets.UTF_8));
                out.flush();
            } catch (IOException error) {
                folder = null;  // nowhere to write: this JVM's file stops here, and the log says so
                System.err.println("DAODAN_RECORD_ERROR " + error);
            }
        }
    }
}
