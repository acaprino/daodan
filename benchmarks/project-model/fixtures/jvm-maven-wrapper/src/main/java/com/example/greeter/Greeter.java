package com.example.greeter;

import org.apache.commons.lang3.StringUtils;

public final class Greeter {
    private Greeter() {
    }

    public static String greet(String name) {
        return "Hello, " + StringUtils.defaultIfBlank(name, "world") + "!";
    }

    public static void main(String[] args) {
        System.out.println(greet(args.length > 0 ? args[0] : null));
    }
}
