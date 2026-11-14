//go:build integration

package store_test

import (
	"testing"

	"example.com/tags/store"
)

func TestOpenTwice(t *testing.T) {
	if store.Open() != store.Open() {
		t.Fatal("backend changed")
	}
}
