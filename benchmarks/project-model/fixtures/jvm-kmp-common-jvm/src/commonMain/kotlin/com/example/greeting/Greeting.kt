package com.example.greeting

import kotlinx.coroutines.delay

expect fun platformName(): String

class Greeting {
    suspend fun greet(): String {
        delay(1)
        return "Hello from ${platformName()}"
    }
}
