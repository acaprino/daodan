package main

import (
	"context"
	"fmt"

	"example.com/fetcher/internal/fetch"
)

func main() {
	got, err := fetch.All(context.Background(), []string{"a", "b"})
	fmt.Println(got, err)
}
