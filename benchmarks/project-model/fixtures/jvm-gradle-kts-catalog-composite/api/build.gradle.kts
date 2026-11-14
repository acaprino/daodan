plugins {
    id("inventory.java-conventions")
    application
}

dependencies {
    implementation(project(":domain"))
    implementation(libs.jackson.databind)
}

application {
    mainClass = "com.example.inventory.api.Main"
}
