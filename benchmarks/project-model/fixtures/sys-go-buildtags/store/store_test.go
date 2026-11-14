package store

import "testing"

func TestBackendNotEmpty(t *testing.T) {
	if backend() == "" {
		t.Fatal("empty backend")
	}
}
