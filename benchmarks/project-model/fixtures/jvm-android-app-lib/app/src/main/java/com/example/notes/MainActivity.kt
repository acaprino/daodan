package com.example.notes

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.notes.core.NoteFormatter

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val text = NoteFormatter.title("first note") + "\n" + FeatureGate.describe(this)
        setContentView(TextView(this).apply { this.text = text })
    }
}
