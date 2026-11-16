package com.example.shapes;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class ReportTest {
    @Test
    public void lineNamesTheArea() {
        assertEquals("area square:4.0", Report.INSTANCE.line(new Shapes.Square(2)));
    }
}
