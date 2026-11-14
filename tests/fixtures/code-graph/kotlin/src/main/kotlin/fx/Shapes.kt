package fx

object Fmt {
    fun show(n: Int): String = "n$n"
    fun show(s: String): String = "s$s"
}

/** A decoy: the same name and parameter as Fmt.show(String). */
object Other {
    fun show(s: String): String = "other$s"
}

class Box {
    val size: Int = 3
}

class Grid {
    operator fun get(i: Int): Int = i * 2
}
