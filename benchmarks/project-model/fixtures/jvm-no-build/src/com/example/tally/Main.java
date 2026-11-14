package com.example.tally;

public final class Main {
    private Main() {
    }

    public static void main(String[] args) {
        Counter counter = new Counter();
        for (String arg : args) {
            counter.add(arg);
        }
        System.out.println(counter.counts());
    }
}
