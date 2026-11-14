package com.acme.shop

import android.app.Activity
import android.os.Bundle
import com.google.firebase.firestore.FirebaseFirestore

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        FirebaseFirestore.getInstance().collection("orders").limit(20).get()
    }
}
