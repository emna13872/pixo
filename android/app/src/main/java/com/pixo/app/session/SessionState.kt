package com.pixo.app.session

import com.pixo.app.avatar.AvatarState
import com.pixo.app.protocol.BrainMessage
import com.pixo.app.protocol.LyricLine
import com.pixo.app.protocol.SessionInfo
import com.pixo.app.protocol.WordInfo

enum class Link { Disconnected, Connecting, Connected }

/** Everything the screens show. One immutable value, replaced on each change. */
data class UiState(
    val serverUrl: String,
    val nickname: String,
    val link: Link = Link.Disconnected,
    val problem: String? = null,
    val sessions: List<SessionInfo> = emptyList(),
    val session: ActiveSession? = null,
    val lastResult: BrainMessage.SessionEnded? = null,
)

/** The session being played: what is on screen and what Pixo is doing. */
data class ActiveSession(
    val id: String,
    val title: String,
    val words: Map<String, WordInfo>,
    val shown: List<String> = emptyList(),
    val highlight: String? = null,
    /** Non-empty while the brain waits for the child to touch one of these words. */
    val tapChoices: Set<String> = emptySet(),
    /** The last sentence Pixo said, shown small for the adult testing the app. */
    val subtitle: String = "",
    val avatar: AvatarState = AvatarState(),
    /** Where the brain serves pictures and songs, e.g. "http://192.168.1.5:8000/". */
    val mediaBase: String = "",
    /** Non-null while a song plays: its lyrics and how far it is. */
    val song: SongState? = null,
)

/** A song being sung, karaoke style. [position] is in seconds from the start of the audio. */
data class SongState(val lines: List<LyricLine>, val position: Double = 0.0) {
    /** The line being sung (the first one before the singing starts). */
    val lineIndex: Int get() = lines.indexOfLast { it.at <= position }.coerceAtLeast(0)

    /** The word being sung in the current line, or -1 between words. */
    val wordIndex: Int
        get() {
            val line = lines.getOrNull(lineIndex) ?: return -1
            return if (position < line.at) -1 else line.words.indexOfLast { it.at <= position }
        }

    /** When the last word starts, to keep the lyrics on screen if the audio cannot play. */
    val lastStart: Double get() = lines.flatMap { line -> line.words.map { it.at } + line.at }.maxOrNull() ?: 0.0
}
