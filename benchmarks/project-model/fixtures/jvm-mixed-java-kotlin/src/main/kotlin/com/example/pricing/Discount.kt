package com.example.pricing

data class Discount(val percent: Int) {
    init {
        require(percent in 0..100) { "percent out of range: $percent" }
    }

    fun applyTo(cents: Long): Long = cents - cents * percent / 100
}
