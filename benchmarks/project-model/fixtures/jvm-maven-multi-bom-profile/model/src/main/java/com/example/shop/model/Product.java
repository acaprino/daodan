package com.example.shop.model;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public record Product(String sku, long priceCents) {
    @JsonCreator
    public Product(@JsonProperty("sku") String sku, @JsonProperty("priceCents") long priceCents) {
        this.sku = sku;
        this.priceCents = priceCents;
    }
}
