package fx

fun twice(text: String): String = text + text

fun useAcrossTasks(): String {
    val shown = Fmt.show("a")
    return twice(shown)
}
