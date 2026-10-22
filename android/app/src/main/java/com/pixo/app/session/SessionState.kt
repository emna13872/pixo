package com.pixo.app.session

import com.pixo.app.avatar.AvatarState
import com.pixo.app.protocol.BrainMessage
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
)
