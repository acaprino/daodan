package com.example.hello;

import com.google.common.base.Joiner;

public final class App {
    private App() {
    }

    static String message(String... words) {
        return Joiner.on(' ').skipNulls().join(words);
    }

    public static void main(String[] args) {
        System.out.println(message("Hello", null, "Gradle"));
    }
}
