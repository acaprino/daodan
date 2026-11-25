package demo;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/items")
public class ItemController {
    @GetMapping
    public List<String> list() { return List.of("a", "b"); }

    @GetMapping("/{id}")
    public String one(@PathVariable int id) { return "item " + id; }

    @PostMapping
    public String create(@RequestBody String body) { return body; }

    @PutMapping("/{id}")
    public String replace(@PathVariable int id, @RequestBody String body) { return body; }

    @DeleteMapping("/{id}")
    public void remove(@PathVariable int id) { }

    // two overloads of one name, told apart by a request parameter: the descriptor is the only difference
    @GetMapping(path = "/search", params = "q")
    public String search(@RequestParam String q) { return q; }

    @GetMapping(path = "/search", params = "n")
    public String search(@RequestParam int n) { return "n" + n; }

    @RequestMapping(path = "/multi", method = {RequestMethod.GET, RequestMethod.HEAD})
    public String multi() { return "multi"; }

    // one mapping with two paths: one handler, two routes
    @GetMapping({"/alias-a", "/alias-b"})
    public String alias() { return "alias"; }

    // annotation, signature and body over several lines: which line does the class file give the method?
    @GetMapping(
        path = "/spread")
    public String spread(
            @RequestParam(defaultValue = "x") String a,
            @RequestParam(defaultValue = "y") String b) {
        String joined = a
            + b;
        return joined;
    }
}
