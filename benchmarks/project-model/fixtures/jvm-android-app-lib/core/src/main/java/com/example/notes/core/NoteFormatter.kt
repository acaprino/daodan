package com.example.notes.core

import androidx.core.text.trimmedLength

object NoteFormatter {
    fun title(raw: CharSequence): String =
        if (raw.trimmedLength() == 0) "Untitled" else raw.trim().toString().replaceFirstChar { it.uppercase() }
}
