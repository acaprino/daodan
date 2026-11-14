package fx;

interface Shape {
    double area();
}

class Circle implements Shape {
    final double r;

    Circle(double r) { this.r = r; }

    public double area() { return 3 * r * r; }
}

class Square implements Shape {
    final double s;

    Square(double s) { this.s = s; }

    public double area() { return s * s; }
}

/** A decoy: an area method outside the Shape hierarchy. */
class Report {
    double area() { return 0; }
}

enum Color {
    RED("r"), GREEN("g");

    final String code;

    Color(String code) { this.code = code; }
}
