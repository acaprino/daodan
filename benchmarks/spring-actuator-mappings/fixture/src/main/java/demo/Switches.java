package demo;

import java.net.Socket;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** Things that keep an application from loading or from ending, each behind a property the probe sets; off, they are not beans. */
public class Switches {
    @Component
    @ConditionalOnProperty("probe.db")
    public static class NeedsDatabase {  // a bean that connects as it is built, as a DataSource does
        public NeedsDatabase() throws Exception { new Socket("db.invalid", 5432).close(); }
    }

    @Component
    @ConditionalOnProperty("probe.block")
    public static class NeverEnds implements CommandLineRunner {  // a runner that never returns: after the context is built
        public void run(String... args) throws Exception { Thread.sleep(Long.MAX_VALUE); }
    }

    @Component
    @ConditionalOnProperty("probe.refresh")
    public static class NeverBuilds implements InitializingBean {  // a bean that never finishes: while the context is built
        public void afterPropertiesSet() throws Exception { Thread.sleep(Long.MAX_VALUE); }
    }

    @Component
    @ConditionalOnProperty("probe.hang")
    public static class NeverCloses implements DisposableBean {  // a bean that never lets the context close: the shutdown hook hangs
        public void destroy() throws Exception { Thread.sleep(Long.MAX_VALUE); }
    }
}
