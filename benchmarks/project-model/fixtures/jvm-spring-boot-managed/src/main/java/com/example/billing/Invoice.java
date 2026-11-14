package com.example.billing;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;

@Entity
public class Invoice {
    @Id
    @GeneratedValue
    private Long id;

    private long amountCents;

    protected Invoice() {
    }

    public Invoice(long amountCents) {
        this.amountCents = amountCents;
    }

    public Long getId() {
        return id;
    }

    public long getAmountCents() {
        return amountCents;
    }
}
