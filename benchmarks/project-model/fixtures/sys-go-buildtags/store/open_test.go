package store_test

import (
	"testing"

	"example.com/tags/store"
)

func TestOpen(t *testing.T) {
	if store.Open() == "" {
		t.Fatal("empty")
	}
}
