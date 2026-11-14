#include <cstdio>
#include "shapes.hpp"

using geo::twice;

int main() {
    geo::Circle circle(2.0);
    geo::Shape *shape = new geo::Square(3.0);
    std::vector<geo::Shape *> shapes{&circle, shape};
    auto doubled = [](int v) { return geo::scale(v); };
    geo::Vec a{1, 2}, b{3, 4};
    geo::Vec c = a + b;
    double sum = /* é */ geo::total(shapes) + shape->area() + circle.area();
    sum += twice(1.5) + geo::scale(2.0) + doubled(4);
    std::printf("%s %f %f\n", shape->name(), sum, c.x);
    shapes.push_back(shape);
    sum += static_cast<double>(c_helper(1)) + int(sum);
    printf("plain\n");
    delete shape;
    return 0;
}
