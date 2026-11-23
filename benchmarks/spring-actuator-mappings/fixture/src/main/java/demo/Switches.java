package demo;

import java.net.Socket;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** Two things that keep an application from loading, each behind a property the probe sets; off, they are not beans. */
public class Switches {
    @Component
    @ConditionalOnProperty("probe.db")
    public static class NeedsDatabase {  // a bean that connects as it is built, as a DataSource does
        public NeedsDatabase() throws Exception { new Socket("db.invalid", 5432).close(); }
    }

    @Component
    @ConditionalOnProperty("probe.block")
    public static class NeverEnds implements CommandLineRunner {  // a runner that never returns
        public void run(String... args) throws Exception { Thread.sleep(Long.MAX_VALUE); }
    }
}
