package id.go.bitungkota.dprd.smartdispo.core.design

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Green = Color(0xFF185B43)
private val Gold = Color(0xFFB9903D)
private val LightColors = lightColorScheme(
    primary = Green,
    secondary = Gold,
    background = Color(0xFFF7F9F8),
    surface = Color.White,
    error = Color(0xFFB3261E),
)
private val DarkColors = darkColorScheme(primary = Color(0xFF83D5AF), secondary = Color(0xFFE4C477))

@Composable
fun SmartDispoTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (isSystemInDarkTheme()) DarkColors else LightColors, content = content)
}
