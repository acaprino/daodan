package main

import (
	"fmt"

	"example.com/iterdemo/seq"
)

func main() {
	for v := range seq.Count(3) {
		fmt.Println(v)
	}
}
