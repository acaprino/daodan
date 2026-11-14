package fx

import "strings"

func helper() int { return 1 }

func one() int { return 1 }

func two() int { return 2 }

func triple() int { return 3 }

var pick = triple

// Run calls through every way Go binds a function to a name.
func Run(s Shape, f func() int) int {
    h := helper
    x, y := one, two
    var g = two
    lit := func() int { return 7 }
    total := h()
    total += x()
    total += y()
    total += g()
    total += lit()
    total += pick()
    total += int(s.Area())
    total += f()
    total += len(strings.ToUpper("fx"))
    return total
}
