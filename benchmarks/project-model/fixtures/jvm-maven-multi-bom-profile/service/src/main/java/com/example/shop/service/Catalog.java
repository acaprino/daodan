package com.example.shop.service;

import com.example.shop.model.Product;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.collect.ImmutableList;
import java.util.List;

public final class Catalog {
    private final ObjectMapper mapper = new ObjectMapper();
    private final ImmutableList<Product> products;

    public Catalog(List<Product> products) {
        this.products = ImmutableList.copyOf(products);
    }

    public List<Product> products() {
        return products;
    }

    public String toJson() throws JsonProcessingException {
        return mapper.writeValueAsString(products);
    }
}
