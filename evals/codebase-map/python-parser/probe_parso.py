import parso

g = parso.load_grammar(version="3.14")


def show(label, src):
    m = g.parse(src)
    errs = []
    stack = [m]
    while stack:
        n = stack.pop()
        if n.type in ("error_node", "error_leaf"):
            errs.append((n.type, n.start_pos, n.get_code()[:30]))
        stack.extend(getattr(n, "children", ()))
    top = [c.type for c in m.children]
    print(f"{label:30} errors={len(errs)} top={top[:4]} {errs[:2]}")


show("type alias", "type Pair[T] = tuple[T, T]\n")
show("generic def", "def first[T](xs: list[T]) -> T:\n    return xs[0]\n")
show("py313 default", "def f[T = int](x: T) -> T: return x\n")
show("except no parens 3.14", "try:\n    pass\nexcept ValueError, TypeError:\n    pass\n")
show("t-string", 'name=1\nt = t"hello {name}"\n')
show("fstring nested quotes", 'd={}\nm = f"{d["k"]}"\n')
show("match", "match x:\n    case 1:\n        pass\n")
show("except star", "try:\n    pass\nexcept* ValueError:\n    pass\n")
show("py2 print", "print 'hello'\n")

m = g.parse("import a.b as c, d\nfrom ..x import (y as z, w)\nfrom m import *\n")
for imp in m.iter_imports():
    if imp.type == "import_name":
        print("  import_name", [([p.value for p in path], a.value if a else None)
                                for path, a in imp._dotted_as_names()])
    else:
        names = [] if imp.is_star_import() else [(n.value, a.value if a else None)
                                                  for n, a in imp._as_name_tuples()]
        print("  import_from level", imp.level, [n.value for n in imp.get_from_names()],
              "star", imp.is_star_import(), names)
