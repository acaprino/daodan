// Command basic shows how to embed the tool. The go command skips
// directories whose name starts with "_", so ./... never builds it.
package main

import (
	"fmt"

	"example.com/tool"
)

func main() { fmt.Println("embedded:", tool.Banner()) }
