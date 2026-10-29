package com.pixo.app.protocol

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray

/** The app ↔ brain protocol, see docs/protocol.md. The app only executes; the brain decides. */
const val PROTOCOL_VERSION = "0.1"

data class SessionInfo(val id: String, val title: String)

/** [imageUrl] is relative to the brain's address (e.g. "media/images/word_hello.png"), or empty. */
data class WordInfo(val text: String, val image: String, val imageUrl: String = "")

/** One word of a song, and the second it starts in the audio. */
data class LyricWord(val at: Double, val text: String)

/** One line of a song: when it starts, its text, an optional picture id and its words. */
data class LyricLine(val at: Double, val text: String, val image: String?, val words: List<LyricWord>)

/** Everything the brain can send to the app. */
sealed interface BrainMessage {
    data class Welcome(val protocol: String, val sessions: List<SessionInfo>) : BrainMessage

    data class SessionStarted(
        val session: String,
        val title: String,
        val words: Map<String, WordInfo>,
    ) : BrainMessage

    data class SessionEnded(
        val session: String,
        val successes: Int,
        val asks: Int,
        val stopped: Boolean,
    ) : BrainMessage

    data class Error(val code: String, val message: String) : BrainMessage

    /** A command: the app does it, then answers with the same [id]. */
    sealed interface Command : BrainMessage {
        val id: Int
    }

    /** [slow]: Pixo models a word for the child to repeat. */
    data class Say(override val id: Int, val text: String, val slow: Boolean = false) : Command

    /** Play the song at [url] (relative to the brain's address) and show its timed lyrics. */
    data class Sing(
        override val id: Int,
        val song: String,
        val url: String,
        val timing: List<LyricLine>,
    ) : Command

    data class PlayVideo(override val id: Int, val video: String, val url: String) : Command

    data class Show(override val id: Int, val words: List<String>, val highlight: String?) : Command

    data class Clear(override val id: Int) : Command

    data class Animate(override val id: Int, val name: String) : Command

    data class Listen(override val id: Int, val language: String, val timeoutMs: Long) : Command

    data class WaitTap(override val id: Int, val choices: List<String>, val timeoutMs: Long) :
        Command

    /** Anything we don't understand: logged and ignored, never a crash. */
    data class Unknown(val raw: String) : BrainMessage
}

private val json = Json { ignoreUnknownKeys = true }

private fun JsonObject.string(key: String): String? = (this[key] as? JsonPrimitive)?.contentOrNull

private fun JsonObject.int(key: String): Int? = (this[key] as? JsonPrimitive)?.intOrNull

private fun JsonObject.double(key: String): Double? = (this[key] as? JsonPrimitive)?.doubleOrNull

private fun JsonObject.lyricLine(): LyricLine? {
    val at = double("at") ?: return null
    val words = (this["words"] as? JsonArray).orEmpty().mapNotNull { element ->
        val w = element as? JsonObject ?: return@mapNotNull null
        LyricWord(w.double("at") ?: return@mapNotNull null, w.string("text").orEmpty())
    }
    return LyricLine(at, string("text").orEmpty(), string("image"), words)
}

private fun JsonObject.strings(key: String): List<String> =
    (this[key] as? JsonArray)?.mapNotNull { (it as? JsonPrimitive)?.contentOrNull }.orEmpty()

/** Parse one text frame from the brain. Never throws. */
fun parseBrainMessage(raw: String): BrainMessage {
    val obj = runCatching { json.parseToJsonElement(raw) as? JsonObject }.getOrNull()
        ?: return BrainMessage.Unknown(raw)
    val type = obj.string("type") ?: return BrainMessage.Unknown(raw)
    val id = obj.int("id")
    return when {
        type == "welcome" -> BrainMessage.Welcome(
            protocol = obj.string("protocol").orEmpty(),
            sessions = (obj["sessions"] as? JsonArray).orEmpty().mapNotNull { element ->
                val s = element as? JsonObject ?: return@mapNotNull null
                SessionInfo(s.string("id") ?: return@mapNotNull null, s.string("title").orEmpty())
            },
        )

        type == "session_started" -> BrainMessage.SessionStarted(
            session = obj.string("session").orEmpty(),
            title = obj.string("title").orEmpty(),
            words = (obj["words"] as? JsonObject).orEmpty().mapNotNull { (wordId, value) ->
                val w = value as? JsonObject ?: return@mapNotNull null
                wordId to WordInfo(
                    w.string("text") ?: wordId,
                    w.string("image").orEmpty(),
                    w.string("image_url").orEmpty(),
                )
            }.toMap(),
        )

        type == "session_ended" -> BrainMessage.SessionEnded(
            session = obj.string("session").orEmpty(),
            successes = obj.int("successes") ?: 0,
            asks = obj.int("asks") ?: 0,
            stopped = (obj["stopped"] as? JsonPrimitive)?.booleanOrNull ?: false,
        )

        type == "error" -> BrainMessage.Error(
            obj.string("code").orEmpty(),
            obj.string("message").orEmpty(),
        )

        id == null -> BrainMessage.Unknown(raw)
        type == "say" -> BrainMessage.Say(
            id,
            obj.string("text").orEmpty(),
            (obj["slow"] as? JsonPrimitive)?.booleanOrNull ?: false,
        )

        type == "sing" -> BrainMessage.Sing(
            id,
            obj.string("song").orEmpty(),
            obj.string("url").orEmpty(),
            (obj["timing"] as? JsonArray).orEmpty().mapNotNull { (it as? JsonObject)?.lyricLine() },
        )

        type == "play_video" -> BrainMessage.PlayVideo(
            id,
            obj.string("video").orEmpty(),
            obj.string("url").orEmpty(),
        )

        type == "show" -> BrainMessage.Show(id, obj.strings("words"), obj.string("highlight"))
        type == "clear" -> BrainMessage.Clear(id)
        type == "animate" -> BrainMessage.Animate(id, obj.string("name").orEmpty())
        type == "listen" -> BrainMessage.Listen(
            id,
            obj.string("language") ?: "en-US",
            obj.int("timeout_ms")?.toLong() ?: 8000L,
        )

        type == "wait_tap" -> BrainMessage.WaitTap(
            id,
            obj.strings("choices"),
            obj.int("timeout_ms")?.toLong() ?: 10000L,
        )

        else -> BrainMessage.Unknown(raw)
    }
}

/** Messages the app sends. Each function returns one JSON text frame. */
object AppMessages {
    fun hello(appVersion: String): String = buildJsonObject {
        put("type", "hello")
        put("protocol", PROTOCOL_VERSION)
        put("app", "pixo-android $appVersion")
    }.toString()

    fun startSession(session: String, nickname: String): String = buildJsonObject {
        put("type", "start_session")
        put("session", session)
        put("nickname", nickname)
    }.toString()

    fun stopSession(): String = buildJsonObject { put("type", "stop_session") }.toString()

    fun done(id: Int): String = buildJsonObject {
        put("type", "done")
        put("id", id)
    }.toString()

    fun heard(id: Int, transcripts: List<String>): String = buildJsonObject {
        put("type", "heard")
        put("id", id)
        putJsonArray("transcripts") { transcripts.forEach { add(JsonPrimitive(it)) } }
    }.toString()

    fun tapped(id: Int, word: String?): String = buildJsonObject {
        put("type", "tapped")
        put("id", id)
        put("word", word?.let { JsonPrimitive(it) } ?: JsonNull)
    }.toString()
}

private fun JsonObject?.orEmpty(): JsonObject = this ?: JsonObject(emptyMap())

private fun JsonArray?.orEmpty(): List<JsonElement> = this ?: emptyList()
