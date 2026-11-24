package demo;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/people")
public class PersonController {  // needs the repository, which needs the database
    private final PersonRepository people;

    public PersonController(PersonRepository people) { this.people = people; }

    @GetMapping
    public List<Person> all() { return people.findAll(); }
}
