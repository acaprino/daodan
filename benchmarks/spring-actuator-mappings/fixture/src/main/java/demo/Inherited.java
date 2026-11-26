package demo;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

/** Handlers that are not written in the class that serves them: a generic base class and an interface. */
public class Inherited {
    public abstract static class Base<T> {
        @GetMapping("/base/{id}")
        public T byId(@PathVariable int id) { return load(id); }

        protected abstract T load(int id);
    }

    @RestController
    public static class BaseImpl extends Base<String> {  // the route is declared in Base
        protected String load(int id) { return "base " + id; }
    }

    public interface Api {
        @GetMapping("/api/ping")
        String apiPing();  // the route is declared on the interface
    }

    @RestController
    public static class ApiImpl implements Api {
        public String apiPing() { return "pong"; }
    }
}
