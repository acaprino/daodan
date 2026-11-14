package com.example.shop.service;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.example.shop.model.Product;
import java.util.List;
import org.junit.jupiter.api.Test;

class CatalogTest {
    @Test
    void keepsProductsInOrder() {
        Catalog catalog = new Catalog(List.of(new Product("A-1", 250), new Product("B-2", 990)));
        assertEquals("A-1", catalog.products().get(0).sku());
    }
}
