package demo;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@Controller
public class PageController {
    @GetMapping("/")
    public String home() { return "home"; }

    @RestController
    public static class Ping {  // a nested class
        @GetMapping("/ping")
        public String ping() { return "pong"; }
    }
}
