package com.pixo.app.avatar

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import kotlin.math.abs

private val Body = Color(0xFF35B6A6)
private val Belly = Color(0xFFBFEDE6)
private val Ink = Color(0xFF203040)
private val Accent = Color(0xFFFFC94D)
private val Glow = Color(0xFF7FD4FF)

/** A friendly round robot, drawn with Compose. Mouth moves while talking, antenna glows while listening. */
@Composable
internal fun PlaceholderPixo(state: AvatarState, modifier: Modifier) {
    val loop = rememberInfiniteTransition(label = "pixo")
    val mouth by loop.animateFloat(
        initialValue = 0.2f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(170), RepeatMode.Reverse),
        label = "mouth",
    )
    val pulse by loop.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(550), RepeatMode.Reverse),
        label = "pulse",
    )
    // 0 → 1 every 3.6 s; the eyes close briefly near the end of each cycle
    val cycle by loop.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(3600, easing = LinearEasing)),
        label = "blink",
    )
    val blink = if (cycle > 0.94f) 1f - abs(cycle - 0.97f) / 0.03f else 0f
    val jump = remember { Animatable(0f) }
    val tilt = remember { Animatable(0f) }
    val grow = remember { Animatable(1f) }
    LaunchedEffect(state.cue) {
        when (state.cue?.name) {
            "happy" -> repeat(2) {
                jump.animateTo(-0.1f, tween(150))
                jump.animateTo(0f, tween(150))
            }

            "dance" -> {
                repeat(3) {
                    tilt.animateTo(14f, tween(140))
                    tilt.animateTo(-14f, tween(140))
                }
                tilt.animateTo(0f, tween(140))
            }

            "show" -> {
                grow.animateTo(1.08f, tween(200))
                grow.animateTo(1f, tween(200))
            }
        }
    }

    Canvas(
        modifier.graphicsLayer {
            translationY = jump.value * size.height
            rotationZ = tilt.value
            scaleX = grow.value
            scaleY = grow.value
        },
    ) {
        val w = size.minDimension
        val c = center
        val r = w * 0.34f

        // Antenna: yellow at rest, blue and pulsing while Pixo listens
        val tip = Offset(c.x, c.y - r * 1.4f)
        drawLine(Body, Offset(c.x, c.y - r * 0.9f), tip, strokeWidth = w * 0.025f, cap = StrokeCap.Round)
        drawCircle(if (state.listening) Glow.copy(alpha = pulse) else Accent, w * 0.055f, tip)
        if (state.listening) drawCircle(Glow.copy(alpha = 0.3f * pulse), r * 1.22f, c)

        // Body and belly
        drawCircle(Body, r, c)
        drawCircle(Belly, r * 0.5f, Offset(c.x, c.y + r * 0.5f))

        // Eyes (they blink)
        val eyeR = r * 0.19f
        val open = (1f - blink).coerceAtLeast(0.08f)
        for (side in listOf(-1f, 1f)) {
            val eye = Offset(c.x + side * r * 0.38f, c.y - r * 0.22f)
            drawOval(
                Color.White,
                topLeft = Offset(eye.x - eyeR, eye.y - eyeR * open),
                size = Size(eyeR * 2, eyeR * 2 * open),
            )
            if (open > 0.5f) drawCircle(Ink, eyeR * 0.5f, Offset(eye.x, eye.y + eyeR * 0.15f))
        }

        // Mouth: opens and closes while talking, a smile otherwise
        val mouthW = r * 0.5f
        val mouthY = c.y + r * 0.12f
        if (state.talking) {
            val h = r * 0.28f * mouth
            drawOval(Ink, topLeft = Offset(c.x - mouthW / 2, mouthY - h / 2), size = Size(mouthW, h))
        } else {
            drawArc(
                Ink,
                startAngle = 20f,
                sweepAngle = 140f,
                useCenter = false,
                topLeft = Offset(c.x - mouthW / 2, mouthY - mouthW * 0.35f),
                size = Size(mouthW, mouthW * 0.6f),
                style = Stroke(width = w * 0.022f, cap = StrokeCap.Round),
            )
        }
    }
}
