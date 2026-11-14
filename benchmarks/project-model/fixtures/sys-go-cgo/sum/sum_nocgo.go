//go:build !cgo

// Package sum adds floats; without cgo the loop runs in Go.
package sum

// Floats returns the sum of xs.
func Floats(xs []float64) float64 {
	var t float64
	for _, x := range xs {
		t += x
	}
	return t
}
