// Added to the build of a copy with `go build -overlay`: the project's tree has no such file. The two public variables of Gin
// (`DebugPrintRouteFunc`, `DebugPrintFunc`) collect each route as it is registered; the line "Listening and serving ..." that every
// `Run*` prints before it binds ends the process, so no port opens (with DAODAN_STOP set).
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/gin-gonic/gin"
)

func init() {
	f, err := os.OpenFile(os.Getenv("DAODAN_OUT"), os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return
	}
	enc := json.NewEncoder(f)
	gin.DebugPrintRouteFunc = func(method, path, handler string, handlers int) {
		enc.Encode(map[string]any{"kind": "route", "method": method, "path": path, "handler": handler, "handlers": handlers})
	}
	gin.DebugPrintFunc = func(format string, values ...any) {
		enc.Encode(map[string]any{"kind": "debug", "text": fmt.Sprintf(format, values...)})
		if os.Getenv("DAODAN_STOP") != "" && strings.HasPrefix(format, "Listening and serving") {
			f.Sync()
			os.Exit(0)
		}
	}
}
