plugins {
    id("inventory.java-conventions")
    `java-library`
}

dependencies {
    api(libs.guava)
    api("com.example.money:money")

    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testRuntimeOnly(libs.junit.launcher)
}
