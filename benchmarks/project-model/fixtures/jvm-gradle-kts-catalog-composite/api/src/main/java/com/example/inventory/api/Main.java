package com.example.inventory.api;

import com.example.inventory.domain.Item;
import com.example.money.Money;
import com.fasterxml.jackson.databind.ObjectMapper;

public final class Main {
    private Main() {
    }

    public static void main(String[] args) throws Exception {
        Item item = new Item("A-1", 2, new Money(499, "EUR"));
        System.out.println(new ObjectMapper().writeValueAsString(item.total()));
    }
}
