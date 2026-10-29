package com.pixo.app.session

import android.Manifest
import android.app.Application
import android.content.Context
import android.content.pm.PackageManager
import android.util.Log
import androidx.core.content.ContextCompat
import androidx.core.content.edit
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.pixo.app.BuildConfig
import com.pixo.app.avatar.AvatarCue
import com.pixo.app.protocol.AppMessages
import com.pixo.app.protocol.BrainConnection
import com.pixo.app.protocol.BrainMessage
import com.pixo.app.protocol.ConnectionEvent
import com.pixo.app.speech.Listener
import com.pixo.app.speech.Speaker
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

/**
 * Runs the app side of the protocol: connects to the brain, executes each command (speak, show,
 * listen, wait for a touch…) and answers it. It never decides what happens next: the brain does.
 */
class SessionViewModel(app: Application) : AndroidViewModel(app) {
    private val prefs = app.getSharedPreferences("pixo", Context.MODE_PRIVATE)
    private val speaker = Speaker(app)
    private val listener = Listener(app)

    private val _ui = MutableStateFlow(
        UiState(
            serverUrl = prefs.getString(KEY_URL, null) ?: DEFAULT_URL,
            nickname = prefs.getString(KEY_NICKNAME, null).orEmpty(),
        ),
    )
    val ui: StateFlow<UiState> = _ui.asStateFlow()

    private var connection: BrainConnection? = null
    private var eventsJob: Job? = null
    private var commandJob: Job? = null
    private var pendingTap: CompletableDeferred<String>? = null
    private var cueSeq = 0

    fun onServerUrlChange(url: String) = _ui.update { it.copy(serverUrl = url) }

    fun onNicknameChange(nickname: String) = _ui.update { it.copy(nickname = nickname) }

    fun connect() {
        disconnect()
        val url = _ui.value.serverUrl.trim()
        prefs.edit { putString(KEY_URL, url) }
        val c = BrainConnection(url, BuildConfig.VERSION_NAME)
        connection = c
        _ui.update { it.copy(link = Link.Connecting, problem = null) }
        eventsJob = viewModelScope.launch {
            runCatching { c.open() }.onFailure {
                _ui.update { s -> s.copy(link = Link.Disconnected, problem = "Bad address: ${it.message}") }
                return@launch
            }
            for (event in c.events) handle(event)
        }
    }

    fun disconnect() {
        cancelCommand()
        eventsJob?.cancel()
        eventsJob = null
        connection?.close()
        connection = null
        _ui.update { it.copy(link = Link.Disconnected, session = null, sessions = emptyList()) }
    }

    fun startSession(sessionId: String) {
        val nickname = _ui.value.nickname.trim()
        if (nickname.isEmpty()) return
        prefs.edit { putString(KEY_NICKNAME, nickname) }
        connection?.send(AppMessages.startSession(sessionId, nickname))
    }

    fun stopSession() {
        cancelCommand()
        connection?.send(AppMessages.stopSession())
    }

    /** The child touched a word card. Counts only while the brain is waiting for a touch. */
    fun onTap(word: String) {
        val tap = pendingTap ?: return
        if (word in _ui.value.session?.tapChoices.orEmpty()) tap.complete(word)
    }

    private fun handle(event: ConnectionEvent) {
        when (event) {
            ConnectionEvent.Open -> Unit // "connected" only once the brain says welcome

            is ConnectionEvent.Closed -> {
                cancelCommand()
                connection = null
                _ui.update {
                    it.copy(link = Link.Disconnected, session = null, sessions = emptyList(), problem = event.reason)
                }
                eventsJob?.cancel()
            }

            is ConnectionEvent.Message -> handle(event.message)
        }
    }

    private fun handle(message: BrainMessage) {
        when (message) {
            is BrainMessage.Welcome -> _ui.update {
                it.copy(link = Link.Connected, sessions = message.sessions, problem = null)
            }

            is BrainMessage.SessionStarted -> _ui.update {
                it.copy(
                    session = ActiveSession(message.session, message.title, message.words),
                    lastResult = null,
                    problem = null,
                )
            }

            is BrainMessage.SessionEnded -> {
                cancelCommand()
                _ui.update { it.copy(session = null, lastResult = message) }
            }

            is BrainMessage.Error -> _ui.update { it.copy(problem = "${message.code}: ${message.message}") }

            is BrainMessage.Command -> {
                // The brain sends one command at a time; a new one replaces anything still running.
                commandJob?.cancel()
                commandJob = viewModelScope.launch {
                    val answer = perform(message)
                    connection?.send(answer)
                }
            }

            is BrainMessage.Unknown -> Log.w(TAG, "Ignored message: ${message.raw}")
        }
    }

    /** Does one command and returns the answer frame. Cancelled (no answer) if the session stops. */
    private suspend fun perform(command: BrainMessage.Command): String = when (command) {
        is BrainMessage.Say -> {
            updateSession { copy(subtitle = command.text, avatar = avatar.copy(talking = true)) }
            try {
                speaker.speak(command.text)
            } finally {
                updateSession { copy(avatar = avatar.copy(talking = false)) }
            }
            AppMessages.done(command.id)
        }

        is BrainMessage.Show -> {
            updateSession { copy(shown = command.words, highlight = command.highlight) }
            AppMessages.done(command.id)
        }

        is BrainMessage.Clear -> {
            updateSession { copy(shown = emptyList(), highlight = null) }
            AppMessages.done(command.id)
        }

        is BrainMessage.Animate -> {
            cueSeq += 1
            updateSession { copy(avatar = avatar.copy(cue = AvatarCue(command.name, cueSeq))) }
            delay(ANIMATION_MS) // let the child see it before Pixo speaks again
            AppMessages.done(command.id)
        }

        is BrainMessage.Listen -> {
            val guesses = if (hasMicrophone()) {
                updateSession { copy(avatar = avatar.copy(listening = true)) }
                try {
                    listener.listen(command.language, command.timeoutMs)
                } finally {
                    updateSession { copy(avatar = avatar.copy(listening = false)) }
                }
            } else {
                emptyList()
            }
            AppMessages.heard(command.id, guesses)
        }

        is BrainMessage.WaitTap -> {
            val tap = CompletableDeferred<String>()
            pendingTap = tap
            updateSession { copy(tapChoices = command.choices.toSet()) }
            val word = try {
                withTimeoutOrNull(command.timeoutMs) { tap.await() }
            } finally {
                pendingTap = null
                updateSession { copy(tapChoices = emptySet()) }
            }
            AppMessages.tapped(command.id, word)
        }
    }

    private fun cancelCommand() {
        commandJob?.cancel()
        commandJob = null
        speaker.stop()
        listener.stop()
    }

    private fun updateSession(change: ActiveSession.() -> ActiveSession) =
        _ui.update { state -> state.session?.let { state.copy(session = it.change()) } ?: state }

    private fun hasMicrophone(): Boolean =
        ContextCompat.checkSelfPermission(getApplication(), Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED

    override fun onCleared() {
        disconnect()
        speaker.shutdown()
        listener.destroy()
    }

    private companion object {
        const val TAG = "Pixo"
        const val KEY_URL = "server_url"
        const val KEY_NICKNAME = "nickname"

        /** Over USB, after `adb reverse tcp:8000 tcp:8000`. */
        const val DEFAULT_URL = "ws://127.0.0.1:8000/ws"
        const val ANIMATION_MS = 900L
    }
}
