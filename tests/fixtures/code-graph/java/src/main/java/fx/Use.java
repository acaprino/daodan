package fx;

import java.lang.reflect.Method;

public class Use {
    static double measure(Shape s) {
        return s.area();
    }

    static String hello(Base b) {
        return b.greet();
    }

    static String print(Printer p) {
        String text = p.show("x");
        return text + p.show(3);
    }

    static Color warm() {
        return Color.RED;
    }

    static Object dynamic(Method m, Object target) throws Exception {
        return m.invoke(target);
    }
}
