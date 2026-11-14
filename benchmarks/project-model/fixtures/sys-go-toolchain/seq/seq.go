// Package seq uses range-over-func iterators, which need Go 1.23.
package seq

import "iter"

// Count yields 0..n-1.
func Count(n int) iter.Seq[int] {
	return func(yield func(int) bool) {
		for i := range n {
			if !yield(i) {
				return
			}
		}
	}
}
