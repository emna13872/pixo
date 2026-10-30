package com.pixo.app.ui

import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pixo.app.protocol.WordInfo
import com.pixo.app.session.SongState

/**
 * The song's lyrics, karaoke style: the line being sung, big, with the word being sung lit up, and
 * the picture of that line beside it (most children can't read yet: the picture carries the meaning).
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun LyricsPanel(song: SongState, words: Map<String, WordInfo>, mediaBase: String, modifier: Modifier = Modifier) {
    val line = song.lines.getOrNull(song.lineIndex) ?: return
    val next = song.lines.getOrNull(song.lineIndex + 1)
    val picture = words.values.firstOrNull { it.image == line.image }
    val image = rememberRemoteImage(mediaBase, picture?.imageUrl)

    Row(
        modifier.fillMaxWidth().padding(horizontal = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (image != null) {
            Image(
                image,
                contentDescription = picture?.text,
                modifier = Modifier.fillMaxHeight(0.8f).aspectRatio(1f).clip(RoundedCornerShape(28.dp)),
            )
        }
        Column(Modifier.weight(1f).fillMaxHeight(), verticalArrangement = Arrangement.Center) {
            val parts = line.words.ifEmpty { null }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                if (parts == null) {
                    LyricWordText(line.text, sung = song.position >= line.at)
                } else {
                    parts.forEachIndexed { i, word ->
                        LyricWordText(word.text, sung = i <= song.wordIndex, now = i == song.wordIndex)
                    }
                }
            }
            if (next != null) {
                Text(
                    next.text,
                    fontSize = 26.sp,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.35f),
                    modifier = Modifier.padding(top = 12.dp),
                )
            }
        }
    }
}

@Composable
private fun LyricWordText(text: String, sung: Boolean, now: Boolean = false) {
    val color by animateColorAsState(
        when {
            now -> MaterialTheme.colorScheme.primary
            sung -> MaterialTheme.colorScheme.onSurface
            else -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f)
        },
        label = "lyric",
    )
    Text(text, fontSize = if (now) 52.sp else 44.sp, fontWeight = FontWeight.Bold, color = color)
}
