package com.pixo.app.protocol

import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.ReceiveChannel
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

/** What happens on the WebSocket, in order. */
sealed interface ConnectionEvent {
    data object Open : ConnectionEvent

    data class Message(val message: BrainMessage) : ConnectionEvent

    data class Closed(val reason: String) : ConnectionEvent
}

/**
 * One WebSocket connection to the brain (`ws://<pc>:8000/ws`).
 *
 * Incoming frames are parsed and delivered in order on [events]; the caller handles them one at a
 * time, which matches the protocol: the brain sends one command and waits for its answer.
 */
class BrainConnection(private val url: String, private val appVersion: String) {
    private val client = OkHttpClient.Builder()
        .pingInterval(15, TimeUnit.SECONDS)
        .build()
    private val channel = Channel<ConnectionEvent>(Channel.UNLIMITED)
    private var socket: WebSocket? = null

    val events: ReceiveChannel<ConnectionEvent> get() = channel

    fun open() {
        socket = client.newWebSocket(Request.Builder().url(url).build(), Listener())
    }

    fun send(frame: String): Boolean = socket?.send(frame) ?: false

    fun close() {
        socket?.close(1000, "bye")
        socket = null
    }

    private inner class Listener : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) {
            webSocket.send(AppMessages.hello(appVersion))
            channel.trySend(ConnectionEvent.Open)
        }

        override fun onMessage(webSocket: WebSocket, text: String) {
            channel.trySend(ConnectionEvent.Message(parseBrainMessage(text)))
        }

        override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
            channel.trySend(ConnectionEvent.Closed(reason.ifBlank { "closed ($code)" }))
        }

        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
            channel.trySend(ConnectionEvent.Closed(t.message ?: t.javaClass.simpleName))
        }
    }
}
