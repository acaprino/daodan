package color

// Code generated files of this package (color_string.go) must not be
// edited by hand; this file is hand-written and may be.

// Describe says whether c is a primary additive color.
func Describe(c Color) string {
	switch c {
	case Red, Green, Blue:
		return c.String() + " is primary"
	}
	return c.String() + " is mixed"
}
