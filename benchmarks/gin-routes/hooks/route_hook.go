// Added to the build of a copy's main package with `go build -overlay` (benchmarks/gin-routes, «Applicazioni vere»): the
// project's tree has no such file. Gin's public `DebugPrintRouteFunc` (in every Gin since 1.4; `DebugPrintFunc` is not in
// 1.4, so it is not used) writes each route as it is registered, one JSON line straight to the file (no buffer: a process
// that is killed keeps what it wrote), with the frames that called Gin (`runtime.CallersFrames`): the first frames outside
// Gin are where the project registers the route. Nothing stops the process here: the harness ends it when it listens.
// Written for the oldest Go a project may declare (no `any`).
package main

import (
	"encoding/json"
	"os"
	"runtime"
	"strings"

	"github.com/gin-gonic/gin"
)

func init() {
	out := os.Getenv("DAODAN_OUT")
	if out == "" {
		return
	}
	f, err := os.OpenFile(out, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return
	}
	enc := json.NewEncoder(f)
	enc.Encode(map[string]interface{}{"kind": "hook", "debugging": gin.IsDebugging()})
	gin.DebugPrintRouteFunc = func(method, path, handler string, handlers int) {
		pcs := make([]uintptr, 40)
		frames := runtime.CallersFrames(pcs[:runtime.Callers(2, pcs)])
		callers := []map[string]interface{}{}
		for {
			frame, more := frames.Next()
			if !strings.HasPrefix(frame.Function, "github.com/gin-gonic/gin.") {
				callers = append(callers, map[string]interface{}{"function": frame.Function, "file": frame.File, "line": frame.Line})
			}
			if !more || len(callers) == 4 {
				break
			}
		}
		enc.Encode(map[string]interface{}{"kind": "route", "method": method, "path": path, "handler": handler, "handlers": handlers, "callers": callers})
	}
}
