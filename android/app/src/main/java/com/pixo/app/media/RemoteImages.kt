package com.pixo.app.media

import android.graphics.BitmapFactory
import android.util.Log
import android.util.LruCache
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request

/** Word pictures served by the brain (media/images/…), downloaded once and kept in memory. */
object RemoteImages {
    private val client = OkHttpClient()
    private val cache = LruCache<String, ImageBitmap>(CACHE_SIZE)

    /** The picture at [url], or null if it cannot be loaded (the card then shows a stand-in). */
    suspend fun load(url: String): ImageBitmap? {
        cache.get(url)?.let { return it }
        return withContext(Dispatchers.IO) {
            runCatching {
                client.newCall(Request.Builder().url(url).build()).execute().use { response ->
                    if (!response.isSuccessful) return@use null
                    val bytes = response.body?.bytes() ?: return@use null
                    BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
                }
            }.onFailure { Log.w("Pixo", "Cannot load $url", it) }.getOrNull()
        }?.also { cache.put(url, it) }
    }

    private const val CACHE_SIZE = 32
}

/** ws://192.168.1.5:8000/ws -> http://192.168.1.5:8000/ (where the brain serves media/). */
fun httpBase(webSocketUrl: String): String {
    val http = webSocketUrl.trim()
        .replaceFirst(Regex("^ws://", RegexOption.IGNORE_CASE), "http://")
        .replaceFirst(Regex("^wss://", RegexOption.IGNORE_CASE), "https://")
    return http.substringBeforeLast("/ws").trimEnd('/') + "/"
}
