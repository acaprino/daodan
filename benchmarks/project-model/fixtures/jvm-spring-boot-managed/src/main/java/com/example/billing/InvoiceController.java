package com.example.billing;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class InvoiceController {
    private final InvoiceRepository invoices;

    public InvoiceController(InvoiceRepository invoices) {
        this.invoices = invoices;
    }

    @GetMapping("/invoices")
    public List<Invoice> list() {
        return invoices.findAll();
    }

    @PostMapping("/invoices")
    public Invoice create(@RequestParam long amountCents) {
        return invoices.save(new Invoice(amountCents));
    }
}
