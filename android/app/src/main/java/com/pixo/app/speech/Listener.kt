package com.pixo.app.speech

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

/**
 * Pixo's ears for Prototype 0: Android's speech recognizer. Returns the recognizer's guesses, best
 * first; an empty list means silence, nothing understood, or no recognizer on this device.
 * The app never judges the answer: the brain does.
 * Must be called from the main thread.
 */
class Listener(private val context: Context) {
    private var recognizer: SpeechRecognizer? = null

    val isAvailable: Boolean get() = SpeechRecognizer.isRecognitionAvailable(context)

    suspend fun listen(language: String, timeoutMs: Long): List<String> {
        if (!isAvailable) return emptyList()
        val sr = recognizer ?: SpeechRecognizer.createSpeechRecognizer(context).also { recognizer = it }
        val result = withTimeoutOrNull(timeoutMs) {
            suspendCancellableCoroutine { continuation ->
                fun finish(guesses: List<String>) {
                    if (continuation.isActive) continuation.resume(guesses)
                }
                sr.setRecognitionListener(object : RecognitionListener {
                    override fun onResults(results: Bundle) {
                        finish(results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION).orEmpty())
                    }

                    override fun onError(error: Int) = finish(emptyList())

                    override fun onReadyForSpeech(params: Bundle?) = Unit

                    override fun onBeginningOfSpeech() = Unit

                    override fun onRmsChanged(rmsdB: Float) = Unit

                    override fun onBufferReceived(buffer: ByteArray?) = Unit

                    override fun onEndOfSpeech() = Unit

                    override fun onPartialResults(partialResults: Bundle?) = Unit

                    override fun onEvent(eventType: Int, params: Bundle?) = Unit
                })
                continuation.invokeOnCancellation { sr.cancel() }
                sr.startListening(
                    Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
                        putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, MAX_GUESSES)
                        putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
                    },
                )
            }
        }
        if (result == null) recognizer?.cancel()
        return result.orEmpty()
    }

    fun stop() {
        recognizer?.cancel()
    }

    fun destroy() {
        recognizer?.destroy()
        recognizer = null
    }

    private companion object {
        const val MAX_GUESSES = 5
    }
}
