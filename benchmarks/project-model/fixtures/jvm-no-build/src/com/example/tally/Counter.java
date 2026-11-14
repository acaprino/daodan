package com.example.tally;

import java.util.Map;
import java.util.TreeMap;

public final class Counter {
    private final Map<String, Integer> counts = new TreeMap<>();

    public void add(String word) {
        counts.merge(word.toLowerCase(), 1, Integer::sum);
    }

    public Map<String, Integer> counts() {
        return counts;
    }
}
