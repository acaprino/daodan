// A measuring tool of benchmarks/gin-routes, not part of Daodan and not of the project it reads: with
// golang.org/x/tools/go/packages (the Go team's loader over `go list`, types from go/types) it says, for the module in
// the working directory, how the project reaches its *gin.Engine. It runs no code of the project; the loader compiles
// the export data of the dependencies, in the container.
//
//	finder <root>     (prints one JSON document; positions relative to <root>)
//	finder -names     (reads symbol names on stdin; for each, the parts the standard library's debug/gosym gives it)
//
// - the functions and methods whose results hold *gin.Engine (exported or not, with their parameters);
// - the functions and methods with a *gin.Engine, *gin.RouterGroup or gin.IRouter/IRoutes parameter (registrars);
// - the functions and methods that return a gin.HandlerFunc (middleware and handler factories);
// - every call of gin.New or gin.Default, with the function it is written in;
// - every call of a Gin function or method whose last parameter is ...gin.HandlerFunc (GET, Handle, Any, Group, Use...: chosen by
//   type, not by name), with the line of its parenthesis and what its last argument is: a function or method the type checker
//   resolves (with its position), a function literal (its own position), a call (a factory: the function it calls), a variable;
// - the main packages and whether each depends on Gin (the import graph).
package main

import (
	"bufio"
	"debug/gosym"
	"encoding/json"
	"fmt"
	"go/ast"
	"go/token"
	"go/types"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"golang.org/x/tools/go/packages"
	"golang.org/x/tools/go/types/typeutil"
)

const gin = "github.com/gin-gonic/gin"

type function struct {
	Package  string   `json:"package"`
	Name     string   `json:"name"`
	Receiver string   `json:"receiver,omitempty"`
	Exported bool     `json:"exported"`
	Params   []string `json:"params"`
	Results  []string `json:"results"`
	Pos      string   `json:"pos"`
}

type call struct {
	Callee string `json:"callee"`
	In     string `json:"in"`
	Pos    string `json:"pos"`
}

type mainPackage struct {
	Package   string `json:"package"`
	Dir       string `json:"dir"`
	DependsOn bool   `json:"depends_on_gin"`
}

var root string

func where(fset *token.FileSet, pos token.Pos) string {
	p := fset.Position(pos)
	rel, err := filepath.Rel(root, p.Filename)
	if err != nil {
		rel = p.Filename
	}
	return filepath.ToSlash(rel) + ":" + itoa(p.Line)
}

func itoa(n int) string { b, _ := json.Marshal(n); return string(b) }

// ginNamed says whether t is the named type gin.<name>, through one pointer when pointer is true.
func ginNamed(t types.Type, name string, pointer bool) bool {
	if pointer {
		p, ok := t.(*types.Pointer)
		if !ok {
			return false
		}
		t = p.Elem()
	}
	n, ok := types.Unalias(t).(*types.Named)
	return ok && n.Obj().Pkg() != nil && n.Obj().Pkg().Path() == gin && n.Obj().Name() == name
}

func list(t *types.Tuple) []string {
	out := []string{}
	for i := 0; i < t.Len(); i++ {
		out = append(out, t.At(i).Type().String())
	}
	return out
}

// argument says what the last argument of a call that registers handlers is, from the type checker.
func argument(p *packages.Package, e ast.Expr) map[string]interface{} {
	e = ast.Unparen(e)
	switch x := e.(type) {
	case *ast.FuncLit:
		return map[string]interface{}{"kind": "function literal", "pos": where(p.Fset, x.Pos())}
	case *ast.CallExpr:
		out := map[string]interface{}{"kind": "call"}
		if f, ok := typeutil.Callee(p.TypesInfo, x).(*types.Func); ok {
			out["callee"], out["pos"] = f.FullName(), where(p.Fset, f.Pos())
		}
		return out
	case *ast.IndexExpr:
		return argument(p, x.X)
	case *ast.IndexListExpr:
		return argument(p, x.X)
	}
	var id *ast.Ident
	switch x := e.(type) {
	case *ast.Ident:
		id = x
	case *ast.SelectorExpr:
		id = x.Sel
	}
	if id != nil {
		switch o := p.TypesInfo.Uses[id].(type) {
		case *types.Func:
			kind := "function"
			if o.Type().(*types.Signature).Recv() != nil {
				kind = "method"
			}
			return map[string]interface{}{"kind": kind, "name": o.FullName(), "pos": where(p.Fset, o.Pos())}
		case *types.Var:
			return map[string]interface{}{"kind": "variable", "name": o.Name(), "pos": where(p.Fset, o.Pos())}
		}
	}
	return map[string]interface{}{"kind": fmt.Sprintf("%T", e)}
}

func main() {
	if os.Args[1] == "-names" { // a name as the Go runtime writes it (`runtime.FuncForPC(pc).Name()`, Gin's handler name), split by the standard library
		lines, enc := bufio.NewScanner(os.Stdin), json.NewEncoder(os.Stdout)
		for lines.Scan() {
			s := gosym.Sym{Name: lines.Text()}
			enc.Encode(map[string]string{"name": s.Name, "package": s.PackageName(), "receiver": s.ReceiverName(), "base": s.BaseName()})
		}
		return
	}
	root, _ = filepath.Abs(os.Args[1])
	out := map[string]interface{}{}

	// the import graph: which main packages depend on Gin
	graph, err := packages.Load(&packages.Config{Mode: packages.NeedName | packages.NeedImports | packages.NeedDeps | packages.NeedFiles}, "./...")
	if err != nil {
		out["error"] = err.Error()
		json.NewEncoder(os.Stdout).Encode(out)
		os.Exit(1)
	}
	reaches := map[string]bool{}
	var depends func(p *packages.Package) bool
	depends = func(p *packages.Package) bool {
		if v, ok := reaches[p.PkgPath]; ok {
			return v
		}
		reaches[p.PkgPath] = false
		v := p.PkgPath == gin
		for _, q := range p.Imports {
			if depends(q) {
				v = true
			}
		}
		reaches[p.PkgPath] = v
		return v
	}
	mains, dirs := []mainPackage{}, map[string]string{}
	for _, p := range graph {
		if len(p.GoFiles) > 0 {
			if dir, err := filepath.Rel(root, filepath.Dir(p.GoFiles[0])); err == nil && !strings.HasPrefix(dir, "..") {
				dirs[p.PkgPath] = filepath.ToSlash(dir) // the folder of each package of the module: where a handler's package is
			}
		}
		if p.Name == "main" && len(p.GoFiles) > 0 {
			dir, _ := filepath.Rel(root, filepath.Dir(p.GoFiles[0]))
			mains = append(mains, mainPackage{p.PkgPath, filepath.ToSlash(dir), depends(p)})
		}
	}
	out["main_packages"] = mains
	out["package_dirs"] = dirs
	out["packages"] = len(graph)

	// the types of the project's packages (dependencies from export data)
	pkgs, err := packages.Load(&packages.Config{Mode: packages.NeedName | packages.NeedFiles | packages.NeedTypes | packages.NeedSyntax | packages.NeedTypesInfo}, "./...")
	if err != nil {
		out["error"] = err.Error()
		json.NewEncoder(os.Stdout).Encode(out)
		os.Exit(1)
	}
	builders, registrars, factories, calls, errors := []function{}, []function{}, []function{}, []call{}, []string{}
	handlerCalls := []map[string]interface{}{}
	consider := func(p *packages.Package, f *types.Func, receiver string) {
		sig := f.Type().(*types.Signature)
		entry := function{p.PkgPath, f.Name(), receiver, f.Exported(), list(sig.Params()), list(sig.Results()), where(p.Fset, f.Pos())}
		for i := 0; i < sig.Results().Len(); i++ {
			if ginNamed(sig.Results().At(i).Type(), "Engine", true) {
				builders = append(builders, entry)
				break
			}
		}
		for i := 0; i < sig.Results().Len(); i++ { // a function that returns a gin.HandlerFunc: a middleware or handler factory
			if ginNamed(sig.Results().At(i).Type(), "HandlerFunc", false) {
				factories = append(factories, entry)
				break
			}
		}
		for i := 0; i < sig.Params().Len(); i++ {
			t := sig.Params().At(i).Type()
			if ginNamed(t, "Engine", true) || ginNamed(t, "RouterGroup", true) || ginNamed(t, "IRouter", false) || ginNamed(t, "IRoutes", false) {
				registrars = append(registrars, entry)
				break
			}
		}
	}
	for _, p := range pkgs {
		for _, e := range p.Errors {
			errors = append(errors, e.Error())
		}
		if p.Types == nil {
			continue
		}
		scope := p.Types.Scope()
		for _, name := range scope.Names() {
			switch obj := scope.Lookup(name).(type) {
			case *types.Func:
				consider(p, obj, "")
			case *types.TypeName:
				if named, ok := obj.Type().(*types.Named); ok {
					for i := 0; i < named.NumMethods(); i++ {
						consider(p, named.Method(i), obj.Name())
					}
				}
			}
		}
		for _, file := range p.Syntax {
			ast.Inspect(file, func(n ast.Node) bool {
				c, ok := n.(*ast.CallExpr)
				if !ok || len(c.Args) == 0 {
					return true
				}
				var id *ast.Ident
				switch fun := c.Fun.(type) {
				case *ast.SelectorExpr:
					id = fun.Sel
				case *ast.Ident:
					id = fun
				}
				if id == nil {
					return true
				}
				f, ok := p.TypesInfo.Uses[id].(*types.Func)
				if !ok || f.Pkg() == nil || f.Pkg().Path() != gin {
					return true
				}
				sig := f.Type().(*types.Signature)
				if !sig.Variadic() {
					return true
				}
				last, ok := sig.Params().At(sig.Params().Len() - 1).Type().(*types.Slice)
				if !ok || !ginNamed(last.Elem(), "HandlerFunc", false) {
					return true
				}
				handlerCalls = append(handlerCalls, map[string]interface{}{"callee": f.Name(), "at": where(p.Fset, c.Lparen), "start": where(p.Fset, c.Pos()),
					"args": len(c.Args), "spread": c.Ellipsis.IsValid(), "last": argument(p, c.Args[len(c.Args)-1])})
				return true
			})
		}
		for _, file := range p.Syntax {
			for _, decl := range file.Decls {
				fd, ok := decl.(*ast.FuncDecl)
				if !ok || fd.Body == nil {
					continue
				}
				in := fd.Name.Name
				if fd.Recv != nil && len(fd.Recv.List) > 0 {
					in = types.ExprString(fd.Recv.List[0].Type) + "." + in
				}
				ast.Inspect(fd.Body, func(n ast.Node) bool {
					c, ok := n.(*ast.CallExpr)
					if !ok {
						return true
					}
					var id *ast.Ident
					switch fun := c.Fun.(type) {
					case *ast.SelectorExpr:
						id = fun.Sel
					case *ast.Ident:
						id = fun
					}
					if id == nil {
						return true
					}
					if f, ok := p.TypesInfo.Uses[id].(*types.Func); ok && f.Pkg() != nil && f.Pkg().Path() == gin && (f.Name() == "New" || f.Name() == "Default") {
						calls = append(calls, call{"gin." + f.Name(), p.PkgPath + "." + in, where(p.Fset, c.Pos())})
					}
					return true
				})
			}
		}
	}
	sort.Slice(calls, func(i, j int) bool { return calls[i].Pos < calls[j].Pos })
	out["engine_builders"] = builders
	out["handler_factories"] = factories
	out["registrars"] = len(registrars)
	out["registrars_sample"] = registrars[:min(len(registrars), 8)]
	out["engine_calls"] = calls
	out["handler_calls"] = handlerCalls
	out["load_errors"] = errors[:min(len(errors), 12)]
	out["load_error_count"] = len(errors)
	json.NewEncoder(os.Stdout).Encode(out)
}
