package com.example.mapping;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class CustomerMapperTest {
    @Test
    void copiesLastNameAndEmail() {
        CustomerDto dto = CustomerMapper.INSTANCE.toDto(new Customer("Ada", "Lovelace", "ada@example.com"));
        assertEquals("Lovelace", dto.getFullName());
        assertEquals("ada@example.com", dto.getEmail());
    }
}
