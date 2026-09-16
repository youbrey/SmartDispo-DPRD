package id.go.bitungkota.dprd.smartdispo.core.security

import android.content.Context
import android.provider.Settings

fun deviceFingerprint(context: Context): String =
    Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
        ?: "android-unknown-device"
