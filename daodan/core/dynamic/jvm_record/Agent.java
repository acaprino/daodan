package daodan.agent;

import java.io.File;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.net.URL;
import java.net.URLClassLoader;
import java.security.CodeSource;
import java.security.ProtectionDomain;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassVisitor;
import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.Handle;
import org.objectweb.asm.Label;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.Type;

import daodan.record.Recorder;

/**
 * The Java agent of Daodan's dynamic step: `-javaagent:agent.jar=out=<folder>,root=<folder>`.
 *
 * Every class loaded from under `root` (the project's compiled classes) is rewritten as it loads: each method
 * tells the recorder it starts, each call instruction tells it before and after (`daodan.record.Recorder`,
 * which the manifest puts on the bootstrap class path). What the class holds (its source file, its methods,
 * its call sites with their lines and declared callees) and what the recorder sees go to one JSON Lines file
 * per JVM in `out`. An `invokedynamic` creates a lambda or a string and calls no project method: it is not a
 * site; the interface method a lambda or method reference implements is noted, so the body is taken by the
 * site that calls that method. A class that cannot be rewritten runs unchanged and is written as `skipped`.
 * The class files are Java 8's; on JDK 9 and later the transformer is `Modular`, which also handles modules.
 */
public final class Agent {
    private Agent() {
    }

    public static void premain(String options, Instrumentation instrumentation) {
        try {
            File jar = new File(Agent.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            URL[] path = {jar.toURI().toURL(), new File(jar.getParentFile(), "asm.jar").toURI().toURL()};
            // ASM in a loader of its own, under the bootstrap one: the project's ASM stays the project's.
            ClassLoader loader = new URLClassLoader(path, null);
            boolean modules = !System.getProperty("java.specification.version").startsWith("1.");  // JDK 9 on
            Class<?> transformer = Class.forName(modules ? "daodan.agent.Modular" : "daodan.agent.Agent$Transformer",
                true, loader);
            instrumentation.addTransformer((ClassFileTransformer) transformer
                .getConstructor(String.class, Instrumentation.class).newInstance(options, instrumentation));
        } catch (Throwable error) {
            System.err.println("DAODAN_RECORD_ERROR " + error);
        }
    }

    public static class Transformer implements ClassFileTransformer {
        private static final String RECORDER = "daodan/record/Recorder";
        private static final Set<String> REFLECTIVE = new HashSet<>(Arrays.asList(
            "java/lang/reflect/Method.invoke", "java/lang/reflect/Constructor.newInstance",
            "java/lang/invoke/MethodHandle.invoke", "java/lang/invoke/MethodHandle.invokeExact",
            "java/lang/invoke/MethodHandle.invokeWithArguments"));
        private final String root;  // the URL every project class is loaded from under
        private final Map<String, Integer> sigs = new HashMap<>();  // name and descriptor
        // A method's name and descriptor to the interface methods a lambda or method reference to it implements,
        // and to the methods registered with them: the reference names the declaration, any override may run.
        private final Map<String, Set<Integer>> aliases = new HashMap<>();
        private final Map<String, List<Integer>> named = new HashMap<>();
        private int methods;
        private int sites;

        public Transformer(String options, Instrumentation instrumentation) {
            Map<String, String> given = new HashMap<>();
            for (String option : options.split(",")) {
                given.put(option.substring(0, option.indexOf('=')), option.substring(option.indexOf('=') + 1));
            }
            String folder = new File(given.get("root")).toURI().toString();
            this.root = folder.endsWith("/") ? folder : folder + "/";
            sigs.put("<clinit>()V", Recorder.CLASS_INIT);
            Recorder.open(given.get("out"), "{\"java\":" + quote(System.getProperty("java.version"))
                + ",\"root\":" + quote(given.get("root")) + "}");
        }

        @Override
        public byte[] transform(ClassLoader loader, String name, Class<?> redefined, ProtectionDomain domain,
                                byte[] bytes) {
            try {
                CodeSource source = domain == null ? null : domain.getCodeSource();
                String from = source == null || source.getLocation() == null ? "" : source.getLocation().toString();
                if (name == null || !from.startsWith(root)) {
                    return null;
                }
                synchronized (this) {
                    try {
                        return rewrite(from.substring(root.length()), bytes);
                    } catch (Throwable error) {
                        Recorder.write("{\"skipped\":" + quote(name) + ",\"why\":" + quote(error.toString()) + "}");
                    }
                }
            } catch (Throwable error) {
                System.err.println("DAODAN_RECORD_ERROR " + error);
            }
            return null;
        }

        private int sig(String key) {
            Integer id = sigs.get(key);
            if (id == null) {
                id = sigs.size() + 1;
                sigs.put(key, id);
            }
            return id;
        }

        private byte[] rewrite(String from, byte[] bytes) {
            ClassReader reader = new ClassReader(bytes);
            // The slot after a method's locals keeps what was pending across each of its calls.
            Map<String, Integer> locals = new HashMap<>();
            reader.accept(new ClassVisitor(Opcodes.ASM9) {
                @Override
                public MethodVisitor visitMethod(int access, String name, String desc, String signature,
                                                 String[] exceptions) {
                    return new MethodVisitor(Opcodes.ASM9) {
                        @Override
                        public void visitMaxs(int stack, int max) {
                            locals.put(name + desc, max);
                        }
                    };
                }
            }, ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
            ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
            Rewriter rewriter = new Rewriter(writer, locals);
            reader.accept(rewriter, 0);
            byte[] rewritten = writer.toByteArray();
            // Only a class that was rewritten is registered and written.
            String className = rewriter.name.replace('/', '.');
            StringBuilder line = new StringBuilder("{\"class\":").append(quote(rewriter.name))
                .append(",\"source\":").append(quote(rewriter.source)).append(",\"from\":").append(quote(from));
            if (rewriter.debug != null) {
                line.append(",\"smap\":").append(quote(rewriter.debug));
            }
            line.append(",\"methods\":[");
            String comma = "";
            for (Object[] method : rewriter.methods) {
                int id = (Integer) method[0];
                String key = (String) method[1] + method[2];
                Recorder.method(id, className, (String) method[1], (String) method[2], sig(key));
                named.computeIfAbsent(key, unused -> new ArrayList<>()).add(id);
                for (int alias : aliases.getOrDefault(key, Collections.emptySet())) {
                    Recorder.alias(id, alias);
                }
                line.append(comma).append('[').append(id).append(',').append(quote((String) method[1])).append(',')
                    .append(quote((String) method[2])).append(',').append(method[3]).append(',').append(method[4])
                    .append(']');
                comma = ",";
            }
            line.append("],\"sites\":[");
            comma = "";
            for (Object[] site : rewriter.sites) {
                String owner = (String) site[3];
                String name = (String) site[4];
                String desc = (String) site[5];
                Recorder.site((Integer) site[0], (Integer) site[1], (Integer) site[2],
                    REFLECTIVE.contains(owner + "." + name) ? Recorder.ANY : sig(name + desc));
                line.append(comma).append('[').append(site[0]).append(',').append(site[1]).append(',').append(site[2])
                    .append(',').append(quote(owner)).append(',').append(quote(name)).append(',').append(quote(desc))
                    .append(']');
                comma = ",";
            }
            Recorder.write(line.append("]}").toString());
            return rewritten;
        }

        private void alias(String key, int sig) {
            if (aliases.computeIfAbsent(key, unused -> new HashSet<>()).add(sig)) {
                for (int id : named.getOrDefault(key, Collections.emptyList())) {
                    Recorder.alias(id, sig);
                }
            }
        }

        private final class Rewriter extends ClassVisitor {
            private final Map<String, Integer> locals;
            private final List<Object[]> methods = new ArrayList<>();  // id, name, descriptor, access, first line
            private final List<Object[]> sites = new ArrayList<>();  // id, method, line, owner, name, descriptor
            private String name;
            private String source;
            private String debug;

            Rewriter(ClassVisitor next, Map<String, Integer> locals) {
                super(Opcodes.ASM9, next);
                this.locals = locals;
            }

            @Override
            public void visit(int version, int access, String name, String signature, String superName,
                              String[] interfaces) {
                this.name = name;
                super.visit(version, access, name, signature, superName, interfaces);
            }

            @Override
            public void visitSource(String source, String debug) {
                this.source = source;
                this.debug = debug;
                super.visitSource(source, debug);
            }

            @Override
            public MethodVisitor visitMethod(int access, String name, String desc, String signature,
                                             String[] exceptions) {
                MethodVisitor next = super.visitMethod(access, name, desc, signature, exceptions);
                Integer kept = locals.get(name + desc);
                if (kept == null) {  // abstract or native: no code
                    return next;
                }
                int id = ++Transformer.this.methods;
                Object[] method = {id, name, desc, access, 0};
                methods.add(method);
                return new MethodVisitor(Opcodes.ASM9, next) {
                    private int line;

                    private void push(int value) {
                        if (value <= Short.MAX_VALUE) {
                            super.visitIntInsn(Opcodes.SIPUSH, value);
                        } else {
                            super.visitLdcInsn(value);
                        }
                    }

                    @Override
                    public void visitCode() {
                        super.visitCode();
                        push(id);
                        super.visitMethodInsn(Opcodes.INVOKESTATIC, RECORDER, "enter", "(I)V", false);
                    }

                    @Override
                    public void visitLineNumber(int line, Label start) {
                        super.visitLineNumber(line, start);
                        this.line = line;
                        if ((Integer) method[4] == 0) {
                            method[4] = line;
                        }
                    }

                    @Override
                    public void visitMethodInsn(int opcode, String owner, String called, String calledDesc,
                                                boolean isInterface) {
                        int site = ++Transformer.this.sites;
                        sites.add(new Object[] {site, id, line, owner, called, calledDesc});
                        push(site);
                        super.visitMethodInsn(Opcodes.INVOKESTATIC, RECORDER, "call", "(I)I", false);
                        super.visitVarInsn(Opcodes.ISTORE, kept);
                        super.visitMethodInsn(opcode, owner, called, calledDesc, isInterface);
                        super.visitVarInsn(Opcodes.ILOAD, kept);
                        push(site);
                        super.visitMethodInsn(Opcodes.INVOKESTATIC, RECORDER, "after", "(II)V", false);
                    }

                    @Override
                    public void visitInvokeDynamicInsn(String called, String calledDesc, Handle bootstrap,
                                                       Object... arguments) {
                        if (bootstrap.getOwner().equals("java/lang/invoke/LambdaMetafactory") && arguments.length > 1
                                && arguments[0] instanceof Type && arguments[1] instanceof Handle) {
                            Handle body = (Handle) arguments[1];
                            alias(body.getName() + body.getDesc(), sig(called + ((Type) arguments[0]).getDescriptor()));
                        }
                        super.visitInvokeDynamicInsn(called, calledDesc, bootstrap, arguments);
                    }
                };
            }
        }
    }

    static String quote(String text) {
        if (text == null) {
            return "null";
        }
        StringBuilder out = new StringBuilder("\"");
        for (int at = 0; at < text.length(); at++) {
            char one = text.charAt(at);
            if (one == '"' || one == '\\') {
                out.append('\\').append(one);
            } else if (one < 0x20 || one > 0x7e) {
                out.append(String.format("\\u%04x", (int) one));
            } else {
                out.append(one);
            }
        }
        return out.append('"').toString();
    }
}
