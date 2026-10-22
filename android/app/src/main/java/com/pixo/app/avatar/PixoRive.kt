package com.pixo.app.avatar

import android.content.Context
import android.util.Log
import app.rive.runtime.kotlin.core.Rive

/**
 * The Rive contract, see docs/rive.md. Any .riv file that follows it can replace Pixo without
 * changing code: drop it in app/src/main/res/raw/pixo.riv and rebuild.
 */
object PixoRive {
    const val RESOURCE_NAME = "pixo"
    const val STATE_MACHINE = "Pixo"
    const val IS_TALKING = "isTalking"
    const val IS_LISTENING = "isListening"
    val TRIGGERS = setOf("show", "happy", "dance")

    /** False when the Rive engine could not start: the app then uses the drawn placeholder. */
    var engineReady = false
        private set

    fun init(context: Context) {
        engineReady = runCatching { Rive.init(context) }
            .onFailure { Log.w("PixoRive", "Rive engine not available, using the placeholder", it) }
            .isSuccess
    }
}
