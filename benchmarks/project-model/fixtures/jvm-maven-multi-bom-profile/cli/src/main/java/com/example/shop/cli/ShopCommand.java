package com.example.shop.cli;

import com.example.shop.model.Product;
import com.example.shop.service.Catalog;
import java.util.List;
import java.util.concurrent.Callable;
import picocli.CommandLine;
import picocli.CommandLine.Command;

@Command(name = "shop", mixinStandardHelpOptions = true, description = "Prints the catalog as JSON.")
public final class ShopCommand implements Callable<Integer> {
    @Override
    public Integer call() throws Exception {
        System.out.println(new Catalog(List.of(new Product("A-1", 250))).toJson());
        return 0;
    }

    public static void main(String[] args) {
        System.exit(new CommandLine(new ShopCommand()).execute(args));
    }
}
