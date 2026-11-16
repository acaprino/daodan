package com.example.shapes;

public class Shapes {
    public interface Shape { double area(); }

    public static class Square implements Shape {
        private final double side;
        public Square(double side) { this.side = side; }
        public double area() { return side * side; }
    }

    public static class Circle implements Shape {
        private final double radius;
        public Circle(double radius) { this.radius = radius; }
        public double area() { return Math.PI * radius * radius; }
    }

    public static double total(Shape[] shapes) {
        double sum = 0;
        for (Shape shape : shapes) {
            sum += shape.area();
        }
        return sum;
    }

    public static String label(Shape shape) {
        return shape.getClass().getSimpleName().toLowerCase() + ":" + String.valueOf(shape.area());
    }
}
