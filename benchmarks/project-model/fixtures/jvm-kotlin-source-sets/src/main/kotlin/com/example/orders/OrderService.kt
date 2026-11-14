package com.example.orders

import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope

data class Order(val id: String, val amountCents: Long)

class OrderService {
    suspend fun totalOf(orders: List<Order>): Long = coroutineScope {
        orders.map { async { it.amountCents } }.sumOf { it.await() }
    }
}
