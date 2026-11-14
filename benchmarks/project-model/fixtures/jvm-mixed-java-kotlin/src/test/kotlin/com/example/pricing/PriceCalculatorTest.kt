package com.example.pricing

import kotlin.test.Test
import kotlin.test.assertEquals

class PriceCalculatorTest {
    @Test
    fun appliesDiscountToSum() {
        assertEquals(900L, PriceCalculator().total(listOf(400L, 600L), Discount(10)))
    }
}
