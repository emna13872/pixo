package com.pixo.app.avatar

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.drawscope.translate
import kotlinx.coroutines.delay
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.min
import kotlin.math.sin
import kotlin.random.Random

/** The screen behind Pixo's face: Pixo *is* the screen, like Miko. */
val FaceScreen = Color(0xFF05070D)
private val EyeGlow = Color(0xFF39D5FF)
private val EyeCore = Color(0xFFD8F8FF)
private val Cheek = Color(0xFFFF7EB6)
private val Glove = Color(0xFFF7F7FA)
private val GloveEdge = Color(0xFF8C96A8)
private val Star = Color(0xFFFFD54F)

/** How Pixo's on-screen hands are held. */
private enum class Pose { WAVE, THUMBS_UP, THUMBS_DOWN, FINGER_WAG, POINT, CLAP, HANDS_UP, COUNT }

/** What a cue from the brain looks like: the hands, the face's own move, and how long it lasts. */
private data class Move(
    val pose: Pose? = null,
    val count: Int = 0,
    val happyEyes: Boolean = false,
    val bounce: Boolean = false,
    val nod: Boolean = false,
    val shake: Boolean = false,
    val stars: Boolean = false,
    val ms: Int = 1600,
)

/** Cue names are the brain's `animate` names: Pixo's one-shots and the gestures of docs/content-v1.md. */
private fun moveFor(cue: String): Move? = when (cue) {
    "dance", "happy" -> Move(Pose.HANDS_UP, happyEyes = true, bounce = true, ms = 2000)
    "celebrate" -> Move(Pose.HANDS_UP, happyEyes = true, stars = true, ms = 2000)
    "wave", "wave_bye", "high_five", "show_hands", "show" -> Move(Pose.WAVE)
    "thumbs_up" -> Move(Pose.THUMBS_UP, happyEyes = true)
    "thumbs_down" -> Move(Pose.THUMBS_DOWN)
    "finger_wag" -> Move(Pose.FINGER_WAG)
    "point", "point_head", "point_eyes", "point_nose", "point_mouth", "point_ears", "point_feet" ->
        Move(Pose.POINT)
    "clap" -> Move(Pose.CLAP, happyEyes = true)
    "hands_up" -> Move(Pose.HANDS_UP)
    "nod" -> Move(nod = true, ms = 1200)
    "head_shake" -> Move(shake = true, ms = 1200)
    else -> cue.removePrefix("count_").toIntOrNull()?.takeIf { cue.startsWith("count_") && it in 1..5 }
        ?.let { Move(Pose.COUNT, count = it) }
}

/**
 * Pixo's face, drawn in code on a black screen: two big glowing eyes and a mouth. It blinks,
 * floats gently, talks, listens (bigger eyes), and plays the brain's cues: gestures with two
 * cartoon hands, a happy dance (bounce, happy eyes, hands up) and stars to celebrate.
 */
@Composable
fun ScreenFace(state: AvatarState, modifier: Modifier = Modifier) {
    val loop = rememberInfiniteTransition(label = "face")
    val time by loop.animateFloat(
        initialValue = 0f,
        targetValue = 60f,
        animationSpec = infiniteRepeatable(tween(60_000, easing = LinearEasing)),
        label = "time",
    )
    val mouth by loop.animateFloat(
        initialValue = 0.15f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(160), RepeatMode.Reverse),
        label = "mouth",
    )
    val listen by animateFloatAsState(if (state.listening) 1f else 0f, label = "listen")

    // Blinks every few seconds, at random, like a living thing
    val blink = remember { Animatable(1f) }
    LaunchedEffect(Unit) {
        while (true) {
            delay(2500L + Random.nextLong(2500))
            blink.animateTo(0.08f, tween(70))
            blink.animateTo(1f, tween(110))
        }
    }

    // One cue at a time; a new cue (even the same name again) starts over
    var move by remember { mutableStateOf<Move?>(null) }
    val progress = remember { Animatable(0f) }
    LaunchedEffect(state.cue) {
        val next = state.cue?.let { moveFor(it.name) } ?: return@LaunchedEffect
        move = next
        progress.snapTo(0f)
        progress.animateTo(1f, tween(next.ms, easing = LinearEasing))
        move = null
    }

    Canvas(modifier) {
        drawRect(FaceScreen)
        val m = move
        val elapsed = progress.value * (m?.ms ?: 0) / 1000f
        val face = FaceLayout(size)

        var dx = 0f
        var dy = sin(time * 0.9f) * size.height * 0.008f // gentle float
        var tilt = 0f
        if (m != null) {
            if (m.bounce) {
                dy -= abs(sin(elapsed * 2f * PI.toFloat() * 2f)) * size.height * 0.07f
                tilt = sin(elapsed * 2f * PI.toFloat() * 2f) * 6f
            }
            if (m.nod) dy += sin(elapsed * 2f * PI.toFloat() * 1.5f) * size.height * 0.04f
            if (m.shake) dx += sin(elapsed * 2f * PI.toFloat() * 2.5f) * size.width * 0.03f
        }

        translate(dx, dy) {
            rotate(tilt, face.center) {
                val happy = m?.happyEyes == true
                drawEyes(face, blink.value, listen, happy)
                drawMouth(face, talking = state.talking, open = mouth, listening = listen, happy = happy)
                if (happy) drawCheeks(face)
            }
        }
        if (m != null) {
            if (m.stars) drawStars(elapsed)
            m.pose?.let { drawHands(it, m.count, progress.value, elapsed) }
        }
    }
}

/** Where everything sits, from the screen's size. Landscape first; portrait still works. */
private class FaceLayout(size: Size) {
    val center = Offset(size.width / 2f, size.height * 0.44f)
    val eyeW = min(size.width * 0.15f, size.height * 0.28f)
    val eyeH = eyeW * 1.35f
    val eyeGap = eyeW * 0.95f
    val left = Offset(center.x - eyeGap, center.y)
    val right = Offset(center.x + eyeGap, center.y)
    val mouth = Offset(center.x, center.y + eyeH * 0.9f)
}

private fun DrawScope.drawEyes(face: FaceLayout, blink: Float, listen: Float, happy: Boolean) {
    val grow = 1f + 0.12f * listen
    for (eye in listOf(face.left, face.right)) {
        val w = face.eyeW * grow
        val h = face.eyeH * grow
        // Soft glow around the eye, so it reads as light, not as a sticker
        drawCircle(
            Brush.radialGradient(listOf(EyeGlow.copy(alpha = 0.35f), Color.Transparent), eye, h * 0.95f),
            radius = h * 0.95f,
            center = eye,
        )
        if (happy) {
            // ^ ^ : happy, closed eyes
            drawArc(
                EyeGlow,
                startAngle = 200f,
                sweepAngle = 140f,
                useCenter = false,
                topLeft = Offset(eye.x - w / 2f, eye.y - h * 0.25f),
                size = Size(w, h * 0.7f),
                style = Stroke(width = w * 0.22f, cap = StrokeCap.Round),
            )
            continue
        }
        val bh = h * blink
        drawRoundRect(
            EyeGlow,
            topLeft = Offset(eye.x - w / 2f, eye.y - bh / 2f),
            size = Size(w, bh),
            cornerRadius = CornerRadius(w / 2f, min(w, bh) / 2f),
        )
        if (blink > 0.5f) {
            drawCircle(EyeCore, radius = w * 0.16f, center = Offset(eye.x + w * 0.18f, eye.y - bh * 0.22f))
            drawCircle(EyeCore.copy(alpha = 0.7f), radius = w * 0.07f, center = Offset(eye.x - w * 0.12f, eye.y + bh * 0.2f))
        }
    }
}

private fun DrawScope.drawMouth(face: FaceLayout, talking: Boolean, open: Float, listening: Float, happy: Boolean) {
    val w = face.eyeW * 0.9f
    val c = face.mouth
    when {
        happy -> drawArc(
            EyeGlow,
            startAngle = 0f,
            sweepAngle = 180f,
            useCenter = true,
            topLeft = Offset(c.x - w / 2f, c.y - w * 0.35f),
            size = Size(w, w * 0.7f),
        )
        talking -> {
            val h = w * (0.12f + 0.38f * open)
            drawOval(EyeGlow, topLeft = Offset(c.x - w * 0.32f, c.y - h / 2f), size = Size(w * 0.64f, h))
        }
        listening > 0.5f -> drawCircle(EyeGlow, radius = w * 0.12f, center = c)
        else -> drawArc(
            EyeGlow,
            startAngle = 20f,
            sweepAngle = 140f,
            useCenter = false,
            topLeft = Offset(c.x - w / 2f, c.y - w * 0.45f),
            size = Size(w, w * 0.6f),
            style = Stroke(width = w * 0.1f, cap = StrokeCap.Round),
        )
    }
}

private fun DrawScope.drawCheeks(face: FaceLayout) {
    for (eye in listOf(face.left, face.right)) {
        drawOval(
            Cheek.copy(alpha = 0.45f),
            topLeft = Offset(eye.x - face.eyeW * 0.4f, eye.y + face.eyeH * 0.45f),
            size = Size(face.eyeW * 0.8f, face.eyeW * 0.35f),
        )
    }
}

private fun DrawScope.drawStars(elapsed: Float) {
    val spots = listOf(0.12f to 0.2f, 0.85f to 0.18f, 0.2f to 0.78f, 0.8f to 0.75f, 0.5f to 0.1f, 0.65f to 0.85f)
    spots.forEachIndexed { i, (x, y) ->
        val twinkle = 0.6f + 0.4f * sin(elapsed * 9f + i)
        drawStar(Offset(size.width * x, size.height * y), size.height * 0.05f * twinkle)
    }
}

private fun DrawScope.drawStar(c: Offset, r: Float) {
    val path = androidx.compose.ui.graphics.Path()
    for (k in 0 until 10) {
        val radius = if (k % 2 == 0) r else r * 0.45f
        val angle = -PI / 2 + k * PI / 5
        val p = Offset(c.x + radius * kotlin.math.cos(angle).toFloat(), c.y + radius * sin(angle).toFloat())
        if (k == 0) path.moveTo(p.x, p.y) else path.lineTo(p.x, p.y)
    }
    path.close()
    drawPath(path, Star)
}

// --- Hands ----------------------------------------------------------------------------------

/** Which fingers are up: thumb, index, middle, ring, little. */
private data class Fingers(val thumb: Boolean, val up: List<Boolean>)

private val OPEN = Fingers(true, listOf(true, true, true, true))
private val THUMB_ONLY = Fingers(true, listOf(false, false, false, false))
private val INDEX_ONLY = Fingers(false, listOf(true, false, false, false))

private fun counting(n: Int) = Fingers(n >= 5, List(4) { it < n })

private fun DrawScope.drawHands(pose: Pose, count: Int, progress: Float, elapsed: Float) {
    // Pop in, then fade out at the end
    val appear = min(1f, progress * 6f) * min(1f, (1f - progress) * 8f)
    val s = size.height * 0.24f * appear
    if (s <= 0f) return
    val swing = sin(elapsed * 2f * PI.toFloat() * 2f)
    val right = Offset(size.width * 0.84f, size.height * 0.62f)
    val left = Offset(size.width * 0.16f, size.height * 0.62f)
    when (pose) {
        Pose.WAVE -> drawHand(right, s, OPEN, angle = swing * 25f)
        Pose.THUMBS_UP -> drawHand(right + Offset(0f, -abs(swing) * s * 0.15f), s, THUMB_ONLY, angle = 0f)
        Pose.THUMBS_DOWN -> drawHand(right, s, THUMB_ONLY, angle = 180f)
        Pose.FINGER_WAG -> drawHand(right, s, INDEX_ONLY, angle = sin(elapsed * 2f * PI.toFloat() * 3f) * 22f)
        Pose.POINT -> drawHand(right, s, INDEX_ONLY, angle = -55f)
        Pose.COUNT -> drawHand(right, s, counting(count), angle = 0f)
        Pose.HANDS_UP -> {
            val up = Offset(0f, -size.height * 0.28f)
            drawHand(left + up, s, OPEN, angle = -15f + swing * 12f, mirror = true)
            drawHand(right + up, s, OPEN, angle = 15f - swing * 12f)
        }
        Pose.CLAP -> {
            val together = abs(swing) // 0 = apart, 1 = touching
            val cx = size.width / 2f
            val y = size.height * 0.78f
            val gap = s * 0.45f + (size.width * 0.18f) * (1f - together)
            drawHand(Offset(cx - gap, y), s, OPEN, angle = 70f, mirror = true)
            drawHand(Offset(cx + gap, y), s, OPEN, angle = -70f)
        }
    }
}

/** A cartoon glove: a round palm, fingers as capsules. Drawn edge first, then filled, so parts merge. */
private fun DrawScope.drawHand(c: Offset, s: Float, fingers: Fingers, angle: Float, mirror: Boolean = false) {
    val edge = s * 0.035f
    rotate(angle, c) {
        scale(if (mirror) -1f else 1f, 1f, c) {
            for (pass in 0..1) {
                val color = if (pass == 0) GloveEdge else Glove
                val grow = if (pass == 0) edge else 0f
                // fingers: index, middle, ring, little
                val xs = listOf(-0.21f, -0.07f, 0.07f, 0.21f)
                val lengths = listOf(0.36f, 0.42f, 0.38f, 0.3f)
                fingers.up.forEachIndexed { i, up ->
                    val len = s * (if (up) lengths[i] else 0.1f)
                    val w = s * 0.14f
                    drawRoundRect(
                        color,
                        topLeft = Offset(c.x + s * xs[i] - w / 2f - grow, c.y - s * 0.12f - len - grow),
                        size = Size(w + 2 * grow, len + s * 0.15f + 2 * grow),
                        cornerRadius = CornerRadius(w / 2f + grow),
                    )
                }
                // thumb, on the left of a right hand: straight up for a thumbs-up, out to the side otherwise
                val thumbsUp = fingers.thumb && fingers.up.none { it }
                rotate(if (thumbsUp) 0f else if (fingers.thumb) -40f else 10f, Offset(c.x - s * 0.25f, c.y)) {
                    val len = s * (if (thumbsUp) 0.42f else if (fingers.thumb) 0.34f else 0.16f)
                    val w = s * 0.15f
                    drawRoundRect(
                        color,
                        topLeft = Offset(c.x - s * 0.25f - w / 2f - grow, c.y - len - grow),
                        size = Size(w + 2 * grow, len + s * 0.1f + 2 * grow),
                        cornerRadius = CornerRadius(w / 2f + grow),
                    )
                }
                // palm and cuff
                drawCircle(color, radius = s * 0.33f + grow, center = c)
                drawRoundRect(
                    color,
                    topLeft = Offset(c.x - s * 0.24f - grow, c.y + s * 0.22f - grow),
                    size = Size(s * 0.48f + 2 * grow, s * 0.2f + 2 * grow),
                    cornerRadius = CornerRadius(s * 0.08f),
                )
            }
        }
    }
}
