//go:build cgo

// Package sum adds floats; with cgo the loop runs in C.
package sum

/*
#cgo CFLAGS: -O2 -DFASTSUM_UNROLL=4
#cgo linux LDFLAGS: -lm
#include "fastsum.h"
*/
import "C"

import "unsafe"

// Floats returns the sum of xs, computed in C.
func Floats(xs []float64) float64 {
	if len(xs) == 0 {
		return 0
	}
	return float64(C.fastsum((*C.double)(unsafe.Pointer(&xs[0])), C.size_t(len(xs))))
}
