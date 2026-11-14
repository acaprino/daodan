// Package color names the palette colors.
package color

//go:generate stringer -type=Color

// Color is one palette entry.
type Color int

const (
	Red Color = iota
	Green
	Blue
)
