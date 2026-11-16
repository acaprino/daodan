package com.example.shapes;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class ShapesTest {
    @Test
    public void totalAddsEachArea() {
        Shapes.Shape[] shapes = new Shapes.Shape[] {new Shapes.Square(2), new Shapes.Square(3)};
        assertEquals(13.0, Shapes.total(shapes), 0.0001);
    }

    @Test
    public void labelNamesTheShape() {
        assertEquals("square:4.0", Shapes.label(new Shapes.Square(2)));
    }
}
