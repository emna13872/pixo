package com.pixo.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.pixo.app.avatar.AvatarState
import com.pixo.app.avatar.PixoAvatar
import com.pixo.app.session.Link
import com.pixo.app.session.UiState

/** For the adult: connect to the brain, type the child's nickname, start a session. */
@Composable
fun HomeScreen(
    state: UiState,
    onServerUrlChange: (String) -> Unit,
    onNicknameChange: (String) -> Unit,
    onConnect: () -> Unit,
    onDisconnect: () -> Unit,
    onStartSession: (String) -> Unit,
) {
    Column(
        Modifier
            .fillMaxSize()
            .safeDrawingPadding()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        PixoAvatar(AvatarState(), Modifier.size(160.dp))
        Text("Pixo", style = MaterialTheme.typography.headlineLarge)

        state.lastResult?.let { result ->
            val text = if (result.stopped) {
                "Session ${result.session} stopped."
            } else {
                "Session ${result.session} finished: ${result.successes} / ${result.asks} right."
            }
            Card(Modifier.fillMaxWidth()) { Text(text, Modifier.padding(16.dp)) }
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Brain", style = MaterialTheme.typography.titleMedium)
                OutlinedTextField(
                    value = state.serverUrl,
                    onValueChange = onServerUrlChange,
                    label = { Text("Address") },
                    singleLine = true,
                    enabled = state.link == Link.Disconnected,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
                    modifier = Modifier.fillMaxWidth(),
                )
                Text(
                    "USB: run `adb reverse tcp:8000 tcp:8000` and keep ws://127.0.0.1:8000/ws. " +
                        "Wi-Fi: start the brain with --host 0.0.0.0 and use the PC's address.",
                    style = MaterialTheme.typography.bodySmall,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    when (state.link) {
                        Link.Disconnected -> Button(onClick = onConnect) { Text("Connect") }
                        Link.Connecting -> OutlinedButton(onClick = onDisconnect) { Text("Cancel") }
                        Link.Connected -> OutlinedButton(onClick = onDisconnect) { Text("Disconnect") }
                    }
                    Text(
                        when (state.link) {
                            Link.Disconnected -> "Not connected"
                            Link.Connecting -> "Connecting…"
                            Link.Connected -> "Connected"
                        },
                    )
                }
                state.problem?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        }

        if (state.link == Link.Connected) {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Child", style = MaterialTheme.typography.titleMedium)
                    OutlinedTextField(
                        value = state.nickname,
                        onValueChange = onNicknameChange,
                        label = { Text("Nickname") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Text("Sessions", style = MaterialTheme.typography.titleMedium)
                    if (state.sessions.isEmpty()) Text("The brain has no sessions.")
                    state.sessions.forEach { session ->
                        Button(
                            onClick = { onStartSession(session.id) },
                            enabled = state.nickname.isNotBlank(),
                            modifier = Modifier.fillMaxWidth(),
                        ) { Text("${session.id}  ·  ${session.title}") }
                    }
                }
            }
        }
    }
}
