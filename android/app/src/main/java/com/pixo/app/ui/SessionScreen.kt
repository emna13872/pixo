package com.pixo.app.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.pixo.app.avatar.FaceScreen
import com.pixo.app.avatar.PixoAvatar
import com.pixo.app.session.ActiveSession

/** On the black screen, text and the lyrics' highlight glow like Pixo's eyes. */
private val SessionColors = darkColorScheme(
    primary = Color(0xFF39D5FF),
    secondary = Color(0xFFFFD54F),
    background = FaceScreen,
    surface = FaceScreen,
    onSurface = Color.White,
)

/** What fills the screen: Pixo alone, Pixo beside one picture, or the content alone. */
private enum class Stage { FACE, FACE_AND_PICTURE, CONTENT }

private fun stageOf(session: ActiveSession): Stage = when {
    session.song != null -> Stage.CONTENT
    session.tapChoices.isNotEmpty() || session.shown.size >= 2 -> Stage.CONTENT
    session.shown.size == 1 -> Stage.FACE_AND_PICTURE
    else -> Stage.FACE
}

/**
 * For the child, phone held sideways. Pixo's face fills the screen; when a word is taught, the
 * face moves to the left half and the picture takes the right half; during the song and the
 * game, the face steps aside and the lyrics or the pictures fill the screen.
 */
@Composable
fun SessionScreen(session: ActiveSession, onTap: (String) -> Unit, onStop: () -> Unit) {
    // The screen must not go to sleep while Pixo talks to the child
    val view = LocalView.current
    DisposableEffect(view) {
        view.keepScreenOn = true
        onDispose { view.keepScreenOn = false }
    }

    val stage = stageOf(session)
    val faceShare by animateFloatAsState(
        when (stage) {
            Stage.FACE -> 1f
            Stage.FACE_AND_PICTURE -> 0.5f
            Stage.CONTENT -> 0f
        },
        animationSpec = tween(450),
        label = "face",
    )

    MaterialTheme(colorScheme = SessionColors) {
        Box(Modifier.fillMaxSize().background(FaceScreen)) {
            Row(Modifier.fillMaxSize().safeDrawingPadding()) {
                if (faceShare > 0.01f) {
                    PixoAvatar(session.avatar, Modifier.fillMaxHeight().weight(faceShare))
                }
                if (faceShare < 0.99f) {
                    Box(
                        Modifier.fillMaxHeight().weight(1f - faceShare).padding(24.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Content(session, onTap)
                    }
                }
            }

            // For the adult testing: the session, a way out, and what Pixo just said
            Row(
                Modifier.align(Alignment.TopEnd).safeDrawingPadding().padding(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    "${session.id} · ${session.title}",
                    style = MaterialTheme.typography.labelMedium,
                    color = Color.White.copy(alpha = 0.4f),
                )
                TextButton(onClick = onStop) { Text("Stop") }
            }
            AnimatedVisibility(
                visible = session.subtitle.isNotEmpty() && session.song == null,
                enter = fadeIn(),
                exit = fadeOut(),
                modifier = Modifier.align(Alignment.BottomCenter).safeDrawingPadding().padding(8.dp),
            ) {
                Text(
                    session.subtitle,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White.copy(alpha = 0.45f),
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
}

/** The right side of the screen: the lyrics, or the word pictures. */
@Composable
private fun Content(session: ActiveSession, onTap: (String) -> Unit) {
    val song = session.song
    if (song != null) {
        LyricsPanel(song, session.words, session.mediaBase, Modifier.fillMaxSize())
        return
    }
    Row(
        Modifier.fillMaxWidth().fillMaxHeight(0.85f),
        horizontalArrangement = Arrangement.spacedBy(24.dp, Alignment.CenterHorizontally),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        session.shown.forEach { wordId ->
            WordCard(
                wordId = wordId,
                word = session.words[wordId],
                highlighted = wordId == session.highlight,
                tappable = wordId in session.tapChoices,
                onTap = { onTap(wordId) },
                modifier = Modifier.weight(1f, fill = false),
                mediaBase = session.mediaBase,
            )
        }
    }
}
