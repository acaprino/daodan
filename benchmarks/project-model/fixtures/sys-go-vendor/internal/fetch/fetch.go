// Package fetch runs lookups in parallel.
package fetch

import (
	"context"
	"strings"

	"golang.org/x/sync/errgroup"
)

// All upper-cases every name in parallel and stops at the first error.
func All(ctx context.Context, names []string) ([]string, error) {
	out := make([]string, len(names))
	g, _ := errgroup.WithContext(ctx)
	for i, n := range names {
		g.Go(func() error {
			out[i] = strings.ToUpper(n)
			return nil
		})
	}
	return out, g.Wait()
}
