package daodan.record;

import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Stream;

/**
 * `Recorder.Frames` from StackWalker, which hides reflection and lambda frames and gives each frame's descriptor
 * (JDK 10 and later; compiled for Java 10, so `Recorder` loads it only there). JDK only.
 */
public final class Walker implements Recorder.Frames {
    private static final StackWalker WALKER = StackWalker.getInstance();
    // Frames from the walk: at(), Recorder.called(), enter(), the method that starts, then its caller.
    private static final Function<Stream<StackWalker.StackFrame>, Optional<StackWalker.StackFrame>> CALLER =
        new Function<Stream<StackWalker.StackFrame>, Optional<StackWalker.StackFrame>>() {
            @Override
            public Optional<StackWalker.StackFrame> apply(Stream<StackWalker.StackFrame> frames) {
                return frames.skip(4).findFirst();
            }
        };

    @Override
    public boolean at(String className, String methodName, String descriptor, int line) {
        StackWalker.StackFrame frame = WALKER.walk(CALLER).orElse(null);
        return frame != null && frame.getLineNumber() == line && frame.getMethodName().equals(methodName)
            && frame.getClassName().equals(className) && frame.getDescriptor().equals(descriptor);
    }
}
