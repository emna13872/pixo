package com.pixo.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.pixo.app.avatar.PixoAvatar
import com.pixo.app.session.ActiveSession

/** For the child: Pixo, the pictures, nothing else to read. */
@Composable
fun SessionScreen(session: ActiveSession, onTap: (String) -> Unit, onStop: () -> Unit) {
    // The screen must not go to sleep while Pixo talks to the child
    val view = LocalView.current
    DisposableEffect(view) {
        view.keepScreenOn = true
        onDispose { view.keepScreenOn = false }
    }

    Column(
        Modifier
            .fillMaxSize()
            .safeDrawingPadding()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(
                "${session.id} · ${session.title}",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.weight(1f),
            )
            TextButton(onClick = onStop) { Text("Stop") }
        }

        PixoAvatar(session.avatar, Modifier.weight(1f).fillMaxWidth())

        Text(
            when {
                session.avatar.listening -> "🎤"
                session.tapChoices.isNotEmpty() -> "👆"
                else -> ""
            },
            style = MaterialTheme.typography.displaySmall,
        )
        Text(
            session.subtitle,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(16.dp))

        val song = session.song
        if (song != null) {
            LyricsPanel(song, session.words, session.mediaBase, Modifier.height(180.dp))
            return@Column
        }

        Row(
            Modifier
                .fillMaxWidth()
                .height(180.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterHorizontally),
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
}
