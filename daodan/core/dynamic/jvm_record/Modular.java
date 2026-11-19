package daodan.agent;

import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import java.util.Collections;

import daodan.record.Recorder;

/**
 * The agent's transformer on JDK 9 and later (compiled for Java 9, loaded only there): a class is rewritten as on
 * JDK 8, and a class of a named module, whose module would not read the recorder's (the bootstrap loader's
 * unnamed module), gets that read edge, or runs unchanged as `skipped`: its rewritten calls would fail.
 */
public final class Modular extends Agent.Transformer {
    private final Instrumentation instrumentation;

    public Modular(String options, Instrumentation instrumentation) {
        super(options, instrumentation);
        this.instrumentation = instrumentation;
    }

    @Override
    public byte[] transform(Module module, ClassLoader loader, String name, Class<?> redefined,
                            ProtectionDomain domain, byte[] bytes) {
        byte[] rewritten = transform(loader, name, redefined, domain, bytes);
        if (rewritten == null || module == null || !module.isNamed()) {
            return rewritten;
        }
        try {
            Module boot = Recorder.class.getModule();
            if (!module.canRead(boot)) {
                instrumentation.redefineModule(module, Collections.singleton(boot), Collections.emptyMap(),
                    Collections.emptyMap(), Collections.emptySet(), Collections.emptyMap());
            }
            return rewritten;
        } catch (Throwable error) {
            Recorder.write("{\"skipped\":" + Agent.quote(name) + ",\"why\":" + Agent.quote(error.toString()) + "}");
            return null;
        }
    }
}
