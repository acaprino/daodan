package com.example.clock;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

public final class Clock {
    private Clock() {
    }

    public static String nowUtc() {
        return DateTimeFormatter.ISO_LOCAL_DATE_TIME.format(Instant.now().atOffset(ZoneOffset.UTC));
    }

    public static void main(String[] args) {
        System.out.println(nowUtc());
    }
}
