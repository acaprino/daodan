package com.example.hello;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class AppTest {
    @Test
    void skipsNulls() {
        assertEquals("Hello Gradle", App.message("Hello", null, "Gradle"));
    }
}
