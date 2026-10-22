package com.pixo.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val PixoColors = lightColorScheme(
    primary = Color(0xFF1E8C80),
    onPrimary = Color.White,
    secondary = Color(0xFFFFB300),
    background = Color(0xFFF6FBFA),
    surface = Color.White,
    error = Color(0xFFC62828),
)

/** Light only for now: bright colours suit young children. */
@Composable
fun PixoTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = PixoColors, content = content)
}
