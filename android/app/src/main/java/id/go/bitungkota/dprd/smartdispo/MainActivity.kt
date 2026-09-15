package id.go.bitungkota.dprd.smartdispo

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import dagger.hilt.android.AndroidEntryPoint
import id.go.bitungkota.dprd.smartdispo.core.design.SmartDispoTheme
import id.go.bitungkota.dprd.smartdispo.feature.home.SmartDispoApp

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent { SmartDispoTheme { SmartDispoApp() } }
    }
}
