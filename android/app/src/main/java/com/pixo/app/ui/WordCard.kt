package com.pixo.app.ui

import android.annotation.SuppressLint
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pixo.app.media.RemoteImages
import com.pixo.app.protocol.WordInfo

/**
 * One word picture. Uses, in order: the picture the brain serves (media/images/…), the drawable
 * named after the word's image id (res/drawable/word_hello.png), then an emoji or a colour.
 */
@SuppressLint("DiscouragedApi") // looked up by name: the brain sends image ids
@Composable
fun WordCard(
    wordId: String,
    word: WordInfo?,
    highlighted: Boolean,
    tappable: Boolean,
    onTap: () -> Unit,
    modifier: Modifier = Modifier,
    mediaBase: String = "",
) {
    val context = LocalContext.current
    val remote = rememberRemoteImage(mediaBase, word?.imageUrl)
    val drawable = remember(word?.image) {
        word?.image?.takeIf { it.isNotEmpty() }
            ?.let { context.resources.getIdentifier(it, "drawable", context.packageName) } ?: 0
    }
    val border = when {
        highlighted -> BorderStroke(6.dp, MaterialTheme.colorScheme.secondary)
        tappable -> BorderStroke(3.dp, MaterialTheme.colorScheme.primary)
        else -> null
    }
    Card(
        onClick = onTap,
        enabled = tappable,
        shape = RoundedCornerShape(24.dp),
        border = border,
        colors = CardDefaults.cardColors(
            containerColor = Color.White,
            disabledContainerColor = Color.White,
            contentColor = Color(0xFF1B2330),
            disabledContentColor = Color(0xFF1B2330),
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = if (highlighted) 8.dp else 2.dp),
        modifier = modifier.fillMaxHeight().aspectRatio(0.8f),
    ) {
        Column(
            Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceEvenly,
        ) {
            Box(Modifier.weight(1f), contentAlignment = Alignment.Center) {
                val swatch = COLOR_WORDS[wordId]
                when {
                    remote != null -> Image(remote, contentDescription = word?.text)
                    drawable != 0 -> Image(painterResource(drawable), contentDescription = word?.text)
                    swatch != null -> Box(
                        Modifier
                            .size(72.dp)
                            .background(swatch, CircleShape)
                            .border(2.dp, Color(0x33000000), CircleShape),
                    )
                    else -> Text(PLACEHOLDER_EMOJI[wordId] ?: "❓", fontSize = 56.sp)
                }
            }
            // The written word helps the adult testing; the child goes by the picture
            Text(word?.text ?: wordId, style = MaterialTheme.typography.titleMedium)
        }
    }
}

/** The brain's picture for a word, once downloaded; null while loading or if there is none. */
@Composable
fun rememberRemoteImage(mediaBase: String, imageUrl: String?): ImageBitmap? {
    val url = imageUrl?.takeIf { it.isNotEmpty() && mediaBase.isNotEmpty() }?.let { mediaBase + it }
    return produceState<ImageBitmap?>(null, url) { value = url?.let { RemoteImages.load(it) } }.value
}

/** Stand-ins until the real word pictures exist (see words.yaml, field `image`). */
private val PLACEHOLDER_EMOJI = mapOf(
    "hello" to "🙋",
    "bye" to "👋",
    "yes" to "👍",
    "no" to "👎",
    "one" to "1️⃣",
    "two" to "2️⃣",
    "three" to "3️⃣",
    "four" to "4️⃣",
    "five" to "5️⃣",
    "head" to "🧒",
    "eyes" to "👀",
    "nose" to "👃",
    "mouth" to "👄",
    "ears" to "👂",
    "hands" to "🙌",
    "feet" to "🦶",
)

private val COLOR_WORDS = mapOf(
    "red" to Color(0xFFE53935),
    "blue" to Color(0xFF1E88E5),
    "yellow" to Color(0xFFFDD835),
    "green" to Color(0xFF43A047),
    "pink" to Color(0xFFF48FB1),
    "black" to Color(0xFF212121),
    "white" to Color(0xFFFFFFFF),
)
