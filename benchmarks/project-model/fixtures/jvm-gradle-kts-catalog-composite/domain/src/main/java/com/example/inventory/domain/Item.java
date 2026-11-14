package com.example.inventory.domain;

import com.example.money.Money;
import com.google.common.base.Preconditions;

public record Item(String sku, int quantity, Money unitPrice) {
    public Item {
        Preconditions.checkArgument(quantity >= 0, "quantity must not be negative");
    }

    public Money total() {
        return new Money(unitPrice.cents() * quantity, unitPrice.currency());
    }
}
