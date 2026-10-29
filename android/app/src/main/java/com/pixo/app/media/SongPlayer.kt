package com.pixo.app.media

import android.media.AudioAttributes
import android.media.MediaPlayer
import android.util.Log
import kotlinx.coroutines.delay
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

/** Plays one song from the brain (http://<pc>:8000/media/songs/…) and reports where it is. */
class SongPlayer {
    private var player: MediaPlayer? = null

    /**
     * Plays [url] to the end, calling [onPosition] with the position in seconds about 20 times a
     * second. Returns false if the song could not be played (the caller can still show the lyrics).
     */
    suspend fun play(url: String, onPosition: (Double) -> Unit): Boolean {
        val mp = MediaPlayer()
        player = mp
        try {
            mp.setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .build(),
            )
            val prepared = suspendCancellableCoroutine { continuation ->
                mp.setOnPreparedListener { if (continuation.isActive) continuation.resume(true) }
                mp.setOnErrorListener { _, what, extra ->
                    Log.w(TAG, "Cannot play $url ($what/$extra)")
                    if (continuation.isActive) continuation.resume(false)
                    true
                }
                runCatching {
                    mp.setDataSource(url)
                    mp.prepareAsync()
                }.onFailure {
                    Log.w(TAG, "Cannot open $url", it)
                    if (continuation.isActive) continuation.resume(false)
                }
            }
            if (!prepared) return false
            var finished = false
            mp.setOnCompletionListener { finished = true }
            mp.start()
            while (!finished) {
                onPosition(mp.currentPosition / 1000.0)
                delay(TICK_MS)
            }
            return true
        } finally {
            mp.release()
            player = null
        }
    }

    fun stop() {
        runCatching { player?.stop() }
    }

    private companion object {
        const val TAG = "Pixo"
        const val TICK_MS = 50L
    }
}
