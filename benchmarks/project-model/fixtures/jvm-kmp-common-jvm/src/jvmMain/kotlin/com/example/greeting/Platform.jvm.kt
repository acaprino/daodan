package com.example.greeting

import org.slf4j.LoggerFactory

private val log = LoggerFactory.getLogger("com.example.greeting.Platform")

actual fun platformName(): String {
    val name = "JVM " + System.getProperty("java.version")
    log.debug("platform {}", name)
    return name
}
