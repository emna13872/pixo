package com.pixo.app.avatar

import android.annotation.SuppressLint
import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import com.airbnb.lottie.LottieComposition
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.rememberLottieAnimatable
import com.airbnb.lottie.compose.rememberLottieComposition

/**
 * The animation contract, see docs/animation.md: one Lottie clip per state, in res/raw.
 * Loops: idle, talk, listen. One-shots (played once, then back to the loop): show, happy, dance.
 * Only `pixo_idle` is required; a missing clip falls back to idle.
 */
object PixoClips {
    const val IDLE = "idle"
    const val TALK = "talk"
    const val LISTEN = "listen"
    val ONE_SHOTS = listOf("show", "happy", "dance")
    val ALL = listOf(IDLE, TALK, LISTEN) + ONE_SHOTS

    /** Resource id of res/raw/pixo_<clip>.json (or .lottie), 0 when the app doesn't ship it. */
    @SuppressLint("DiscouragedApi") // looked up by name so the app builds with or without the files
    fun resource(context: Context, clip: String): Int =
        context.resources.getIdentifier("pixo_$clip", "raw", context.packageName)
}

/**
 * Pixo on screen. Plays the Lottie clips when the app ships them (the real, animated Pixo);
 * otherwise a placeholder drawn in code, so the whole loop can be tested before the art exists.
 */
@Composable
fun PixoAvatar(state: AvatarState, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val clips = remember { PixoClips.ALL.associateWith { PixoClips.resource(context, it) }.filterValues { it != 0 } }
    if (PixoClips.IDLE in clips) {
        LottiePixo(clips, state, modifier)
    } else {
        PlaceholderPixo(state, modifier)
    }
}

/**
 * The state machine lives here, in code: the brain's events pick the clip.
 * A one-shot cue wins; otherwise talking, then listening, then idle.
 */
@Composable
private fun LottiePixo(clips: Map<String, Int>, state: AvatarState, modifier: Modifier) {
    // Load every clip once, up front, so switching never shows an empty frame
    val loaded: Map<String, LottieComposition?> = clips.mapValues { (_, resId) ->
        rememberLottieComposition(LottieCompositionSpec.RawRes(resId)).value
    }
    var oneShot by remember { mutableStateOf<AvatarCue?>(null) }
    LaunchedEffect(state.cue) {
        state.cue?.takeIf { it.name in PixoClips.ONE_SHOTS && it.name in clips }?.let { oneShot = it }
    }

    val loop = when {
        state.talking && PixoClips.TALK in clips -> PixoClips.TALK
        state.listening && PixoClips.LISTEN in clips -> PixoClips.LISTEN
        else -> PixoClips.IDLE
    }
    val clip = oneShot?.name ?: loop
    val composition = loaded[clip]

    val animatable = rememberLottieAnimatable()
    LaunchedEffect(composition, oneShot) {
        if (composition == null) return@LaunchedEffect
        if (oneShot != null) {
            animatable.animate(composition, iterations = 1)
            oneShot = null // back to the loop
        } else {
            animatable.animate(composition, iterations = LottieConstants.IterateForever)
        }
    }
    LottieAnimation(composition, { animatable.progress }, modifier)
}
