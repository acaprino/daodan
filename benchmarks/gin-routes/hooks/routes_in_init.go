// Added to the build of a copy with `go build -overlay`. It calls the project's `setupRouter()`: a name the Gin documentation uses for
// tests, NOT a convention every project follows. It shows what `(*Engine).Routes()` gives, with the file and line of each handler
// from `runtime.FuncForPC(pc).FileLine(pc)`, and ends the process in `init`, before `main` can reach `Run`.
package main

import (
	"encoding/json"
	"os"
	"reflect"
	"runtime"
)

func init() {
	if os.Getenv("DAODAN_ROUTES") == "" {
		return
	}
	routes := []map[string]any{}
	for _, info := range setupRouter().Routes() {
		pc := reflect.ValueOf(info.HandlerFunc).Pointer()
		fn := runtime.FuncForPC(pc)
		file, line := fn.FileLine(pc)
		routes = append(routes, map[string]any{"method": info.Method, "path": info.Path, "handler": info.Handler,
			"funcForPC": fn.Name(), "file": file, "line": line})
	}
	data, _ := json.Marshal(routes)
	os.WriteFile(os.Getenv("DAODAN_OUT"), data, 0o644)
	os.Exit(0)
}
