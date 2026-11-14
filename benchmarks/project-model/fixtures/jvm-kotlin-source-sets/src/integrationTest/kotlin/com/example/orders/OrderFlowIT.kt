package com.example.orders

import kotlinx.coroutines.runBlocking
import org.assertj.core.api.Assertions.assertThat
import kotlin.test.Test

class OrderFlowIT {
    @Test
    fun emptyListTotalsZero() = runBlocking {
        assertThat(OrderService().totalOf(emptyList())).isZero()
    }
}
