package com.pixo.app.protocol

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Frames copied from docs/protocol.md: the app must read exactly what the brain sends. */
class MessagesTest {
    @Test
    fun `reads welcome with its sessions`() {
        val msg = parseBrainMessage(
            """{"type": "welcome", "protocol": "0.1", "sessions": [{"id": "1.1", "title": "Hello!"}]}""",
        )
        assertEquals(BrainMessage.Welcome("0.1", listOf(SessionInfo("1.1", "Hello!"))), msg)
    }

    @Test
    fun `reads session_started words`() {
        val msg = parseBrainMessage(
            """{"type": "session_started", "session": "1.1", "title": "Hello!",
               "words": {"hello": {"text": "hello", "image": "word_hello"}}}""",
        )
        assertEquals(
            BrainMessage.SessionStarted("1.1", "Hello!", mapOf("hello" to WordInfo("hello", "word_hello"))),
            msg,
        )
    }

    @Test
    fun `reads a word's picture address`() {
        val msg = parseBrainMessage(
            """{"type": "session_started", "session": "u1-s1", "title": "Hello!",
               "words": {"hello": {"text": "hello", "image": "word_hello", "image_url": "media/images/word_hello.png"}}}""",
        ) as BrainMessage.SessionStarted
        assertEquals("media/images/word_hello.png", msg.words.getValue("hello").imageUrl)
    }

    @Test
    fun `reads a slow say and a song with timed lyrics`() {
        assertEquals(
            BrainMessage.Say(3, "Hello!", slow = true),
            parseBrainMessage("""{"type": "say", "id": 3, "text": "Hello!", "slow": true}"""),
        )
        val sing = parseBrainMessage(
            """{"type": "sing", "id": 4, "song": "song_hello", "url": "media/songs/song_hello.mp3",
               "timing": [{"at": 3.1, "text": "Hello, hello!", "image": "word_hello",
                           "words": [{"at": 3.22, "text": "Hello,"}, {"at": 5.22, "text": "hello!"}]},
                          {"at": 16.36, "text": "Bye-bye!"}]}""",
        )
        assertEquals(
            BrainMessage.Sing(
                4,
                "song_hello",
                "media/songs/song_hello.mp3",
                listOf(
                    LyricLine(3.1, "Hello, hello!", "word_hello", listOf(LyricWord(3.22, "Hello,"), LyricWord(5.22, "hello!"))),
                    LyricLine(16.36, "Bye-bye!", null, emptyList()),
                ),
            ),
            sing,
        )
    }

    @Test
    fun `reads session_ended, stopped or not`() {
        assertEquals(
            BrainMessage.SessionEnded("1.1", successes = 4, asks = 4, stopped = false),
            parseBrainMessage("""{"type": "session_ended", "session": "1.1", "successes": 4, "asks": 4}"""),
        )
        val stopped = parseBrainMessage(
            """{"type": "session_ended", "session": "1.1", "successes": 1, "asks": 2, "stopped": true}""",
        )
        assertTrue((stopped as BrainMessage.SessionEnded).stopped)
    }

    @Test
    fun `reads every command`() {
        assertEquals(BrainMessage.Say(7, "Hello, Sara!"), parseBrainMessage("""{"type": "say", "id": 7, "text": "Hello, Sara!"}"""))
        assertEquals(
            BrainMessage.Show(8, listOf("hello", "bye"), "hello"),
            parseBrainMessage("""{"type": "show", "id": 8, "words": ["hello", "bye"], "highlight": "hello"}"""),
        )
        assertEquals(
            BrainMessage.Show(9, listOf("hello"), null),
            parseBrainMessage("""{"type": "show", "id": 9, "words": ["hello"], "highlight": null}"""),
        )
        assertEquals(BrainMessage.Clear(10), parseBrainMessage("""{"type": "clear", "id": 10}"""))
        assertEquals(BrainMessage.Animate(11, "dance"), parseBrainMessage("""{"type": "animate", "id": 11, "name": "dance"}"""))
        assertEquals(
            BrainMessage.Listen(12, "en-US", 8000),
            parseBrainMessage("""{"type": "listen", "id": 12, "language": "en-US", "timeout_ms": 8000}"""),
        )
        assertEquals(
            BrainMessage.WaitTap(13, listOf("hello", "bye"), 10000),
            parseBrainMessage("""{"type": "wait_tap", "id": 13, "choices": ["hello", "bye"], "timeout_ms": 10000}"""),
        )
    }

    @Test
    fun `reads errors`() {
        assertEquals(
            BrainMessage.Error("unknown_session", "no session 9.9"),
            parseBrainMessage("""{"type": "error", "code": "unknown_session", "message": "no session 9.9"}"""),
        )
    }

    @Test
    fun `never throws on bad frames`() {
        listOf(
            "not json",
            "[1, 2]",
            """{"no_type": 1}""",
            """{"type": "say", "text": "a command without id"}""",
            """{"type": "teleport", "id": 1}""",
        ).forEach { raw -> assertEquals(BrainMessage.Unknown(raw), parseBrainMessage(raw)) }
    }

    @Test
    fun `writes the app messages`() {
        fun obj(frame: String) = Json.parseToJsonElement(frame).jsonObject

        val hello = obj(AppMessages.hello("0.1.0"))
        assertEquals("hello", hello["type"]!!.jsonPrimitive.content)
        assertEquals(PROTOCOL_VERSION, hello["protocol"]!!.jsonPrimitive.content)

        val start = obj(AppMessages.startSession("1.1", "Sara"))
        assertEquals("Sara", start["nickname"]!!.jsonPrimitive.content)

        assertEquals("""{"type":"done","id":7}""", AppMessages.done(7))

        val heard = obj(AppMessages.heard(12, listOf("hello", "yellow")))
        assertEquals(2, (heard["transcripts"] as JsonArray).size)

        assertEquals("bye", obj(AppMessages.tapped(13, "bye"))["word"]!!.jsonPrimitive.content)
        assertEquals(JsonNull, obj(AppMessages.tapped(13, null))["word"])
    }
}
