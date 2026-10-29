package com.pixo.app.speech

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.suspendCancellableCoroutine
import java.util.Locale
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import kotlin.coroutines.resume

/**
 * Pixo's voice for Prototype 0: Android's built-in text-to-speech, American English, slow.
 * (Later replaced by the Azure voice, streamed by the brain.)
 */
class Speaker(context: Context) {
    private val ready = CompletableDeferred<Boolean>()
    private val pending = ConcurrentHashMap<String, () -> Unit>()
    private val tts: TextToSpeech = TextToSpeech(context.applicationContext) { status ->
        ready.complete(status == TextToSpeech.SUCCESS)
    }

    init {
        tts.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String) = Unit

            override fun onDone(utteranceId: String) {
                pending.remove(utteranceId)?.invoke()
            }

            @Deprecated("Deprecated in Java")
            override fun onError(utteranceId: String) {
                pending.remove(utteranceId)?.invoke()
            }

            override fun onError(utteranceId: String, errorCode: Int) {
                pending.remove(utteranceId)?.invoke()
            }
        })
    }

    /** Speaks [text] and returns once it has been fully said (or failed). */
    suspend fun speak(text: String) {
        if (!ready.await()) return
        tts.language = Locale.US
        tts.setSpeechRate(SPEECH_RATE)
        tts.setPitch(PITCH)
        val id = UUID.randomUUID().toString()
        suspendCancellableCoroutine { continuation ->
            pending[id] = { if (continuation.isActive) continuation.resume(Unit) }
            continuation.invokeOnCancellation {
                pending.remove(id)
                tts.stop()
            }
            if (tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, id) != TextToSpeech.SUCCESS) {
                pending.remove(id)?.invoke()
            }
        }
    }

    fun stop() {
        tts.stop()
    }

    fun shutdown() {
        tts.shutdown()
    }

    private companion object {
        const val SPEECH_RATE = 0.85f // the pedagogy rules ask for a slow pace
        const val PITCH = 1.3f // a younger, friendlier voice
    }
}
