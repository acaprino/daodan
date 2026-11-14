package com.example.notes

import android.content.Context
import androidx.biometric.BiometricManager

object FeatureGate {
    fun describe(context: Context): String {
        val status = BiometricManager.from(context).canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_WEAK)
        return if (status == BiometricManager.BIOMETRIC_SUCCESS) "Paid tier: biometric lock on" else "Paid tier: no biometric hardware"
    }
}
