#include "shapes.hpp"

namespace geo {

Shape::~Shape() {}

Circle::Circle(double radius) : radius(radius) {}

double Circle::area() const { return 3.0 * radius * radius; }

const char *Circle::name() const { return "circle"; }

Vec Vec::operator+(const Vec &other) const { return Vec{x + other.x, y + other.y}; }

int scale(int value) { return twice(value); }

double scale(double value) { return value * 2.0; }

double total(const std::vector<Shape *> &shapes) {
    double sum = 0;
    for (const Shape *shape : shapes) sum += shape->area();
    return sum;
}

}  // namespace geo

extern "C" int c_helper(int value) { return value + 1; }
