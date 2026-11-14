package com.example.greeting

import kotlin.test.Test
import kotlin.test.assertTrue

class GreetingTest {
    @Test
    fun namesThePlatform() {
        assertTrue(platformName().isNotEmpty())
    }
}
