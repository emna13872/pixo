package com.pixo.app.speech

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.SystemClock
import android.speech.RecognitionListener
import android.speech.RecognitionService
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import kotlinx.coroutines.delay
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

/**
 * Pixo's ears for Prototype 0: Android's speech recognizer. Returns the recognizer's guesses, best
 * first; an empty list means silence, nothing understood, or no recognizer on this device.
 * The app never judges the answer: the brain does.
 * Must be called from the main thread.
 *
 * Uses Google's recognizer (the Google app) when installed: on some phones (e.g. Samsung, Android 15)
 * the default service is an on-device one that may not have English and returns nothing.
 */
class Listener(private val context: Context) {
    private var recognizer: SpeechRecognizer? = null

    val isAvailable: Boolean get() = SpeechRecognizer.isRecognitionAvailable(context)

    /** Google's recognition service if the phone has it, otherwise null (= the phone's default). */
    @Suppress("DEPRECATION") // the flags-object overload needs API 33; we support 26+
    private val service: ComponentName? by lazy {
        context.packageManager.queryIntentServices(Intent(RecognitionService.SERVICE_INTERFACE), 0)
            .map { ComponentName(it.serviceInfo.packageName, it.serviceInfo.name) }
            .also { Log.i(TAG, "Recognition services: $it") }
            .firstOrNull { it.packageName == GOOGLE_APP }
    }

    suspend fun listen(language: String, timeoutMs: Long): List<String> {
        if (!isAvailable) {
            Log.w(TAG, "No speech recognizer on this device")
            return emptyList()
        }
        val started = SystemClock.elapsedRealtime()
        val first = listenOnce(language, timeoutMs)
        // A recognizer that fails at once is usually still busy (just after text-to-speech): retry once
        val elapsed = SystemClock.elapsedRealtime() - started
        if (first is Outcome.Failed && elapsed < FAST_FAILURE_MS) {
            delay(RETRY_DELAY_MS)
            return listenOnce(language, timeoutMs - elapsed - RETRY_DELAY_MS).guesses
        }
        return first.guesses
    }

    private suspend fun listenOnce(language: String, timeoutMs: Long): Outcome {
        // A fresh recognizer each time: reusing one after an error often leaves it "busy"
        destroy()
        val sr = (service?.let { SpeechRecognizer.createSpeechRecognizer(context, it) }
            ?: SpeechRecognizer.createSpeechRecognizer(context)).also { recognizer = it }
        Log.i(TAG, "Listening ($language) with ${service ?: "default service"}")
        val outcome = withTimeoutOrNull(timeoutMs.coerceAtLeast(MIN_TIMEOUT_MS)) {
            suspendCancellableCoroutine { continuation ->
                fun finish(outcome: Outcome) {
                    if (continuation.isActive) continuation.resume(outcome)
                }
                sr.setRecognitionListener(object : RecognitionListener {
                    override fun onResults(results: Bundle) {
                        val guesses = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION).orEmpty()
                        Log.i(TAG, "Heard $guesses")
                        finish(Outcome.Heard(guesses))
                    }

                    override fun onError(error: Int) {
                        Log.w(TAG, "Recognizer error $error (${errorName(error)})")
                        finish(Outcome.Failed(error))
                    }

                    override fun onReadyForSpeech(params: Bundle?) {
                        Log.d(TAG, "Ready for speech")
                    }

                    override fun onBeginningOfSpeech() {
                        Log.d(TAG, "Speech started")
                    }

                    override fun onRmsChanged(rmsdB: Float) = Unit

                    override fun onBufferReceived(buffer: ByteArray?) = Unit

                    override fun onEndOfSpeech() {
                        Log.d(TAG, "Speech ended")
                    }

                    override fun onPartialResults(partialResults: Bundle?) = Unit

                    override fun onEvent(eventType: Int, params: Bundle?) = Unit
                })
                continuation.invokeOnCancellation { sr.cancel() }
                sr.startListening(
                    Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, language)
                        putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, MAX_GUESSES)
                        putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
                        putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
                    },
                )
            }
        }
        if (outcome == null) {
            Log.w(TAG, "No answer from the recognizer within $timeoutMs ms")
            recognizer?.cancel()
        }
        return outcome ?: Outcome.Failed(-1)
    }

    fun stop() {
        recognizer?.cancel()
    }

    fun destroy() {
        recognizer?.destroy()
        recognizer = null
    }

    private sealed interface Outcome {
        val guesses: List<String>

        data class Heard(override val guesses: List<String>) : Outcome

        data class Failed(val error: Int) : Outcome {
            override val guesses: List<String> get() = emptyList()
        }
    }

    private companion object {
        const val TAG = "PixoEars"
        const val GOOGLE_APP = "com.google.android.googlequicksearchbox"
        const val MAX_GUESSES = 5
        const val FAST_FAILURE_MS = 1000L
        const val RETRY_DELAY_MS = 300L
        const val MIN_TIMEOUT_MS = 2000L

        fun errorName(error: Int): String = when (error) {
            SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "network timeout"
            SpeechRecognizer.ERROR_NETWORK -> "network"
            SpeechRecognizer.ERROR_AUDIO -> "audio"
            SpeechRecognizer.ERROR_SERVER -> "server"
            SpeechRecognizer.ERROR_CLIENT -> "client"
            SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "no speech"
            SpeechRecognizer.ERROR_NO_MATCH -> "no match"
            SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "busy"
            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "no microphone permission"
            SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED -> "language not supported"
            SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE -> "language not downloaded"
            else -> "other"
        }
    }
}
