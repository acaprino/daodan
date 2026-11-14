package com.example.pricing;

import java.util.List;

public final class PriceCalculator {
    public long total(List<Long> prices, Discount discount) {
        long sum = 0;
        for (long price : prices) {
            sum += price;
        }
        return discount.applyTo(sum);
    }
}
