package com.example.orders

import kotlinx.coroutines.runBlocking
import kotlin.test.Test
import kotlin.test.assertEquals

class OrderServiceTest {
    @Test
    fun sumsAmounts() = runBlocking {
        assertEquals(300L, OrderService().totalOf(listOf(Order("a", 100), Order("b", 200))))
    }
}
