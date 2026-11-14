package com.example.inventory.domain;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.example.money.Money;
import org.junit.jupiter.api.Test;

class ItemTest {
    @Test
    void totalMultipliesUnitPrice() {
        assertEquals(new Money(750, "EUR"), new Item("A-1", 3, new Money(250, "EUR")).total());
    }
}
