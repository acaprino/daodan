package fx;

class Base {
    String greet() { return "base"; }
}

class Loud extends Base {
    String greet() { return super.greet().toUpperCase(); }
}

class Quiet extends Base {
    String greet() { return "..."; }
}

class Printer {
    String show(int n) { return "n" + n; }

    String show(String s) { return "s" + s; }
}
