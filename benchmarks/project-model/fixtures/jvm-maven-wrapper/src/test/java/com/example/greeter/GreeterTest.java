package com.example.greeter;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class GreeterTest {
    @Test
    void blankNameFallsBackToWorld() {
        assertEquals("Hello, world!", Greeter.greet("  "));
    }
}
