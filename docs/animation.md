# Animating Pixo (Lottie)

Pixo is animated with [Lottie](https://airbnb.io/lottie/): free, open source, no account and no splash
screen. Each state of Pixo is one short clip, and the app picks which clip plays from the brain's events.
Code and art stay independent: any set of clips that follows the contract below works without touching
the app.

Until the clips exist, the app draws a simple placeholder Pixo in code (`avatar/PlaceholderPixo.kt`)
that reacts to the same events, so the whole loop can be tested today.

## 1. The contract

Files go in `android/app/src/main/res/raw/`, as Lottie JSON (`.json`) or dotLottie (`.lottie`).
Android resource names allow only lowercase letters, digits and `_`.

| File | Kind | Plays when |
|---|---|---|
| `pixo_idle` | loop, **required** | nothing else is happening (breathing, blinking) |
| `pixo_talk` | loop | Pixo speaks a sentence (`say`) |
| `pixo_listen` | loop | the microphone is open (`listen`) |
| `pixo_show` | once | `animate` `show`: Pixo presents a picture |
| `pixo_happy` | once | `animate` `happy`: right answer |
| `pixo_dance` | once | `animate` `dance`: 3 right answers in a row |

Rules:
- Only `pixo_idle` is required. A missing clip falls back to idle; with no idle clip the app uses the
  drawn placeholder.
- **Every clip starts and ends on the same neutral pose** (same position, same size, eyes open, mouth
  closed). That is what makes switching between clips look smooth.
- Same canvas size for every clip, square-ish (for example 512 × 512), Pixo centred.
- Keep each file small (under ~300 KB) and avoid effects Lottie doesn't support on Android (check
  "Supported features" on airbnb.io/lottie).

To try new clips: copy them to `res/raw/`, rebuild. To go back to the placeholder: delete them.

## 2. The state machine (in the app)

With Lottie, the logic that Rive would keep inside its file lives in `avatar/PixoAvatar.kt`:

```
one-shot cue (show / happy / dance)  → play it once, then back to the loop below
talking                              → talk (loop)
listening                            → listen (loop)
otherwise                            → idle (loop)
```

The brain's protocol does not change: it still sends `say`, `listen` and `animate`.

## 3. Getting the clips

**A. Make them** in the LottieFiles editor (browser, free tier), in Jitter, or in After Effects with the
Bodymovin plugin. Draw Pixo once, then make the six clips from the same drawing.

**B. Start from free animations** on lottiefiles.com. Check each file's license (the "Lottie Simple
License" allows commercial use; others may not) and pick clips of the same character.

**C. Commission an animator** with this page as the brief. Ask for the Lottie files *and* the source
files so we can change them later.

## 4. Alternatives considered

- **Rive** (named in the original mission): one file holds the drawing *and* the state machine, with
  smooth blends between states and runtime-driven values (useful for lip sync later). Dropped for
  Prototype 0 because the free plan reportedly shows a Rive splash screen at runtime, and an account is
  needed. Switching back means replacing `LottiePixo` in `PixoAvatar.kt`; the events stay the same.
- **Image frames** (PNG per pose): simple, but heavy files and choppy motion.
- **Spine**: game-industry tool, paid license, more app code.
- **Compose drawing only** (today's placeholder): free and simple, but every animation is code.
