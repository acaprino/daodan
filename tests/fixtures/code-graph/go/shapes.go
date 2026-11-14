package fx

// Shape is implemented by Circle and Square.
type Shape interface {
    Area() float64
}

type Circle struct{ R float64 }

func (c Circle) Area() float64 { return 3 * c.R * c.R }

type Square struct{ S float64 }

func (s Square) Area() float64 { return s.S * s.S }

// Plot is a decoy: an Area of another signature, so not a Shape, and a helper method.
type Plot struct{}

func (p Plot) Area(scale int) float64 { return float64(scale) }

func (p Plot) helper() int { return 0 }
