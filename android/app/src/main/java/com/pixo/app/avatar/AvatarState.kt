package com.pixo.app.avatar

/** What Pixo is doing right now. [PixoAvatar] turns it into a drawing or into Rive inputs. */
data class AvatarState(
    val talking: Boolean = false,
    val listening: Boolean = false,
    val cue: AvatarCue? = null,
)

/** A one-shot animation asked by the brain ("show", "happy", "dance"). [seq] keeps two equal cues in a row apart. */
data class AvatarCue(val name: String, val seq: Int)
