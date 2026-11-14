//go:build ignore

// gen.go is run by hand with "go run gen.go"; the ignore tag keeps it
// out of package store, which is why it may declare package main.
package main

import "fmt"

func main() { fmt.Println("// nothing to generate yet") }
