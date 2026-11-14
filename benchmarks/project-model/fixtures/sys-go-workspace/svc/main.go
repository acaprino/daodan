package main

import (
	"fmt"

	"github.com/google/uuid"

	"example.com/ws/api"
)

func main() {
	o := api.Order{ID: uuid.NewString(), Total: 1200}
	fmt.Printf("%+v\n", o)
}
