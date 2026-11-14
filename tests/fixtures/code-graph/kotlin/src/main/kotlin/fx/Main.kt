package fx

val op: (Int) -> Int = { it + 1 }

fun main() {
    val grid = Grid()
    val box = Box()
    println(Fmt.show(1))
    val cell = grid[2]
    val size = box.size
    println(op(cell + size))
}
