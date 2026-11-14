package com.example.tally;

public final class CounterCheck {
    private CounterCheck() {
    }

    public static void main(String[] args) {
        Counter counter = new Counter();
        counter.add("A");
        counter.add("a");
        if (counter.counts().get("a") != 2) {
            throw new AssertionError("expected 2, got " + counter.counts());
        }
        System.out.println("ok");
    }
}
