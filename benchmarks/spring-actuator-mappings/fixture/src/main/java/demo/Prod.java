package demo;

import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Profile("prod")
public class Prod {  // a route that exists only under a profile the probe does not activate
    @GetMapping("/prod-only")
    public String only() { return "prod"; }
}
