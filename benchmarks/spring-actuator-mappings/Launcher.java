import java.lang.annotation.Annotation;
import java.lang.invoke.MethodType;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.context.event.ApplicationPreparedEvent;
import org.springframework.boot.context.event.ApplicationStartedEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.context.ConfigurableApplicationContext;

/**
 * Loads the application of a Spring Boot project and writes what Spring's own interface says of its routes to a file.
 * Run in source-file mode: `java -cp <classes>:<lib>/* Launcher.java <main class> <out file> <mode> <stop> <how> [key=value ...]`.
 * Nothing of the project is compiled or changed.
 * mode `actuator`: the JSON of the bean of the endpoint whose id is `mappings`. mode `handler-methods`: the handler
 * methods of every `RequestMappingHandlerMapping` bean (spring-webmvc, no Actuator needed), as JSON.
 * stop `started`: at `ApplicationStartedEvent`, the context refreshed and the runners (`CommandLineRunner`,
 * `ApplicationRunner`) not yet called; `returned`: when `SpringApplication.run` returns, after them; `aot`: at
 * `ApplicationPreparedEvent`, the bean definitions loaded and the context not refreshed: the context is taken up to
 * where `GenericApplicationContext.refreshForAotProcessing` (Spring Framework 6, the one Spring's AOT processing
 * uses) leaves it, and only the beans the mode asks for are created.
 * how `args`: the properties are command-line arguments (`--key=value`, the highest precedence of Spring Boot's
 * externalized configuration); `defaults`: `SpringApplication.setDefaultProperties` (the lowest).
 * Reflection only: the names of the packages of Spring Boot's classes are not the launcher's concern.
 */
public class Launcher {
    static String out, mode;

    public static void main(String[] args) throws Exception {
        out = args[1];
        mode = args[2];
        String stop = args[3], how = args[4];
        try {
            Map<String, Object> properties = new HashMap<>();
            List<String> arguments = new ArrayList<>();
            for (int i = 5; i < args.length; i++) {
                int eq = args[i].indexOf('=');
                properties.put(args[i].substring(0, eq), args[i].substring(eq + 1));
                arguments.add("--" + args[i]);
            }
            SpringApplication application = new SpringApplication(Class.forName(args[0]));
            if (how.equals("defaults")) application.setDefaultProperties(properties);
            if (stop.equals("started")) application.addListeners(new AtStart());
            if (stop.equals("aot")) application.addListeners(new AtPrepared());
            ConfigurableApplicationContext context = application.run(how.equals("args") ? arguments.toArray(new String[0]) : new String[0]);
            finish(context);
        } catch (Throwable error) {
            fail(error);
        }
    }

    static class AtStart implements ApplicationListener<ApplicationStartedEvent> {
        public void onApplicationEvent(ApplicationStartedEvent event) {
            finish(event.getApplicationContext());
        }
    }

    static class AtPrepared implements ApplicationListener<ApplicationPreparedEvent> {
        public void onApplicationEvent(ApplicationPreparedEvent event) {
            try {
                Object context = event.getApplicationContext();
                Class<?> hints = Class.forName("org.springframework.aot.hint.RuntimeHints");
                context.getClass().getMethod("refreshForAotProcessing", hints).invoke(context, hints.getDeclaredConstructor().newInstance());
                finish(event.getApplicationContext());
            } catch (Throwable error) {
                fail(error);
            }
        }
    }

    static void finish(ConfigurableApplicationContext context) {
        try {
            String json = mode.equals("actuator") ? actuator(context) : handlerMethods(context);
            Files.writeString(Path.of(out), json);
            System.exit(json.startsWith("{\"error\"") ? 2 : 0);
        } catch (Throwable error) {
            fail(error);
        }
    }

    static void fail(Throwable error) {
        StringBuilder chain = new StringBuilder();
        for (Throwable t = error; t != null; t = t.getCause()) {
            chain.append(chain.length() == 0 ? "" : " <- ").append(t.getClass().getName()).append(": ").append(t.getMessage());
        }
        try {
            Files.writeString(Path.of(out), "{\"error\": " + quote(chain.toString()) + "}");
        } catch (Exception ignored) {
        }
        System.exit(1);
    }

    static String actuator(ConfigurableApplicationContext context) throws Exception {
        for (String name : context.getBeanDefinitionNames()) {
            Class<?> type = context.getType(name);
            if (type == null) continue;
            for (Annotation annotation : type.getAnnotations()) {
                if (annotation.annotationType().getName().equals("org.springframework.boot.actuate.endpoint.annotation.Endpoint")
                        && "mappings".equals(annotation.annotationType().getMethod("id").invoke(annotation))) {
                    Object descriptor = type.getMethod("mappings").invoke(context.getBean(name));
                    Class<?> mapper = null;  // Jackson 3 (Spring Boot 4) is `tools.jackson`, Jackson 2 `com.fasterxml.jackson`
                    for (String candidate : new String[] {"tools.jackson.databind.ObjectMapper", "com.fasterxml.jackson.databind.ObjectMapper"}) {
                        try {
                            mapper = Class.forName(candidate);
                            break;
                        } catch (ClassNotFoundException absent) {
                        }
                    }
                    Object instance = context.getBeanProvider(mapper).getIfAvailable();
                    if (instance == null && mapper.getName().startsWith("tools.")) {
                        Class<?> json = Class.forName("tools.jackson.databind.json.JsonMapper");
                        Object builder = json.getMethod("builder").invoke(null);
                        instance = builder.getClass().getMethod("build").invoke(builder);
                    } else if (instance == null) {
                        instance = mapper.getDeclaredConstructor().newInstance();
                    }
                    return (String) mapper.getMethod("writeValueAsString", Object.class).invoke(instance, descriptor);
                }
            }
        }
        return "{\"error\": \"no bean of an endpoint with the id mappings\"}";
    }

    static String handlerMethods(ConfigurableApplicationContext context) throws Exception {
        Class<?> type = Class.forName("org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping");
        StringBuilder out = new StringBuilder("[");
        for (Map.Entry<String, ?> bean : context.getBeansOfType(type).entrySet()) {
            Map<?, ?> methods = (Map<?, ?>) type.getMethod("getHandlerMethods").invoke(bean.getValue());
            for (Map.Entry<?, ?> entry : methods.entrySet()) {
                Object info = entry.getKey(), handler = entry.getValue();
                Method method = (Method) handler.getClass().getMethod("getMethod").invoke(handler);
                Class<?> beanType = (Class<?>) handler.getClass().getMethod("getBeanType").invoke(handler);
                Object conditions = info.getClass().getMethod("getMethodsCondition").invoke(info);
                Object methodsOf = conditions.getClass().getMethod("getMethods").invoke(conditions);
                Object patterns = info.getClass().getMethod("getPatternValues").invoke(info);
                java.security.CodeSource source = method.getDeclaringClass().getProtectionDomain().getCodeSource();
                out.append(out.length() > 1 ? "," : "").append("{\"bean\": ").append(quote(bean.getKey()))
                   .append(", \"mapping\": ").append(quote(info.toString()))
                   .append(", \"methods\": ").append(array(methodsOf))
                   .append(", \"patterns\": ").append(array(patterns))
                   .append(", \"declaringClass\": ").append(quote(method.getDeclaringClass().getName()))
                   .append(", \"beanType\": ").append(quote(beanType.getName()))
                   .append(", \"name\": ").append(quote(method.getName()))
                   .append(", \"descriptor\": ").append(quote(
                       MethodType.methodType(method.getReturnType(), method.getParameterTypes()).toMethodDescriptorString()))
                   .append(", \"codeSource\": ").append(quote(source == null || source.getLocation() == null ? "" : source.getLocation().toString()))
                   .append("}");
            }
        }
        return out.append("]").toString();
    }

    static String array(Object collection) {
        StringBuilder out = new StringBuilder("[");
        for (Object item : (java.util.Collection<?>) collection) {
            out.append(out.length() > 1 ? ", " : "").append(quote(String.valueOf(item)));
        }
        return out.append("]").toString();
    }

    static String quote(String text) {
        return "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\"";
    }
}
