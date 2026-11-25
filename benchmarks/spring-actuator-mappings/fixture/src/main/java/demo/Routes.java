package demo;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.function.RouterFunction;
import org.springframework.web.servlet.function.RouterFunctions;
import org.springframework.web.servlet.function.ServerResponse;

@Configuration
public class Routes {
    @Bean
    public RouterFunction<ServerResponse> functional() {  // a route with no handler method
        return RouterFunctions.route().GET("/fn/hello", request -> ServerResponse.ok().body("hi")).build();
    }
}
