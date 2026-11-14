#pragma once
#include <vector>

namespace geo {

struct Shape {
    virtual ~Shape();
    virtual double area() const = 0;
    virtual const char *name() const { return "shape"; }
};

struct Circle : Shape {
    explicit Circle(double radius);
    double area() const override;
    const char *name() const override;
    double radius;
};

struct Square : Shape {
    explicit Square(double side) : side(side) {}
    double area() const override { return side * side; }
    double side;
};

struct Vec {
    double x, y;
    Vec operator+(const Vec &other) const;
};

template <typename T> T twice(T value) { return value + value; }

int scale(int value);
double scale(double value);
double total(const std::vector<Shape *> &shapes);

}  // namespace geo

extern "C" int c_helper(int value);
