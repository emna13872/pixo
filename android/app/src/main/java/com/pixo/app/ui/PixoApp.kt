package com.pixo.app.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.pixo.app.session.SessionViewModel
import com.pixo.app.ui.theme.PixoTheme

/** Two screens: home (connect, pick a session) and the session itself. */
@Composable
fun PixoApp(viewModel: SessionViewModel = viewModel()) {
    val state by viewModel.ui.collectAsStateWithLifecycle()
    PixoTheme {
        Surface(Modifier.fillMaxSize()) {
            val session = state.session
            if (session == null) {
                HomeScreen(
                    state = state,
                    onServerUrlChange = viewModel::onServerUrlChange,
                    onNicknameChange = viewModel::onNicknameChange,
                    onConnect = viewModel::connect,
                    onDisconnect = viewModel::disconnect,
                    onStartSession = viewModel::startSession,
                )
            } else {
                SessionScreen(session = session, onTap = viewModel::onTap, onStop = viewModel::stopSession)
            }
        }
    }
}
