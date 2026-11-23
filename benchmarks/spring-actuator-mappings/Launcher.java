import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

/**
 * Loads the application of a Spring Boot project and writes what Spring's own interface says of its routes to a file.
 * Run in source-file mode (`java -cp <classes>:<lib>/* Launcher.java <main class> <out file> <mode> [property=value ...]`):
 * nothing of the project is compiled or changed. `server.port=-1` makes the context without an HTTP connector.
 * mode `actuator`: the JSON of the bean of the endpoint whose id is `mappings`; mode `handler-methods`: the handler
 * methods of `RequestMappingHandlerMapping` (spring-webmvc, for a project without Actuator). Reflection only: the
 * names of the packages of Spring Boot's classes are not the launcher's concern.
 */
public class Launcher {
    public static void main(String[] args) throws Exception {
        int code = 0;
        String json;
        try {
            Map<String, Object> properties = new HashMap<>(Map.of(
                "server.port", "-1", "management.endpoints.web.exposure.include", "mappings", "spring.main.banner-mode", "off"));
            for (int i = 3; i < args.length; i++) {
                int eq = args[i].indexOf('=');
                properties.put(args[i].substring(0, eq), args[i].substring(eq + 1));
            }
            SpringApplication application = new SpringApplication(Class.forName(args[0]));
            application.setDefaultProperties(properties);
            ConfigurableApplicationContext context = application.run();
            json = args[2].equals("actuator") ? actuator(context) : handlerMethods(context);
        } catch (Throwable error) {
            code = 1;
            StringBuilder chain = new StringBuilder();
            for (Throwable t = error; t != null; t = t.getCause()) {
                chain.append(chain.length() == 0 ? "" : " <- ").append(t.getClass().getName()).append(": ").append(t.getMessage());
            }
            json = "{\"error\": " + quote(chain.toString()) + "}";
        }
        Files.writeString(Path.of(args[1]), json);
        System.exit(code);
    }

    static String actuator(ConfigurableApplicationContext context) throws Exception {
        for (String name : context.getBeanDefinitionNames()) {
            Class<?> type = context.getType(name);
            if (type == null) continue;
            for (Annotation annotation : type.getAnnotations()) {
                if (annotation.annotationType().getName().equals("org.springframework.boot.actuate.endpoint.annotation.Endpoint")
                        && "mappings".equals(annotation.annotationType().getMethod("id").invoke(annotation))) {
                    Object descriptor = type.getMethod("mappings").invoke(context.getBean(name));
                    Class<?> mapper = Class.forName("com.fasterxml.jackson.databind.ObjectMapper");
                    Object instance = context.getBeanProvider(mapper).getIfAvailable();
                    if (instance == null) instance = mapper.getDeclaredConstructor().newInstance();
                    return (String) mapper.getMethod("writeValueAsString", Object.class).invoke(instance, descriptor);
                }
            }
        }
        return "{\"error\": \"no bean of an endpoint with the id mappings\"}";
    }

    static String handlerMethods(ConfigurableApplicationContext context) throws Exception {
        Class<?> type = Class.forName("org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping");
        Map<?, ?> methods = (Map<?, ?>) type.getMethod("getHandlerMethods").invoke(context.getBean(type));
        StringBuilder out = new StringBuilder("[");
        for (Map.Entry<?, ?> entry : methods.entrySet()) {
            Method method = (Method) entry.getValue().getClass().getMethod("getMethod").invoke(entry.getValue());
            out.append(out.length() > 1 ? "," : "").append("{\"mapping\": ").append(quote(entry.getKey().toString()))
               .append(", \"class\": ").append(quote(method.getDeclaringClass().getName()))
               .append(", \"method\": ").append(quote(method.getName()))
               .append(", \"parameters\": ").append(quote(java.util.Arrays.toString(method.getParameterTypes()))).append("}");
        }
        return out.append("]").toString();
    }

    static String quote(String text) {
        return "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\"";
    }
}
