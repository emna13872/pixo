# Pixo in Rive

Pixo is animated with [Rive](https://rive.app): one file, `pixo.riv`, holds the drawing, the animations
and a **state machine** that the app drives with a few inputs. Code and art stay independent: any file
that follows the contract below works without touching the app.

Until that file exists, the app draws a simple placeholder Pixo in code (`avatar/PixoAvatar.kt`) that
reacts to the same events, so the whole loop can be tested today.

## 1. The contract

| What | Name | Type | When the app sets it |
|---|---|---|---|
| File | `android/app/src/main/res/raw/pixo.riv` | – | at build time |
| State machine | `Pixo` | – | started when the screen opens |
| Input | `isTalking` | boolean | `true` while Pixo speaks a sentence (`say`) |
| Input | `isListening` | boolean | `true` while the microphone is open (`listen`) |
| Input | `show` | trigger | `animate` `show`: Pixo presents a picture |
| Input | `happy` | trigger | `animate` `happy`: right answer |
| Input | `dance` | trigger | `animate` `dance`: 3 right answers in a row |

Rules:
- Names are case-sensitive and must match exactly.
- The state machine must have an **idle** state that loops (breathing, blinking), which plays when no
  input is active.
- Triggers play once and return to idle (or to talking/listening if that input is still `true`).
- A missing input does not crash the app: it is logged (`PixoRive` in Logcat) and ignored.
- Use the default artboard. Keep it square-ish: the app fits it in the space above the pictures.

To swap Pixo: copy the file to `res/raw/pixo.riv`, rebuild. To go back to the placeholder: delete it.

## 2. Getting a `pixo.riv`

**A. Build it in the Rive editor (recommended for the real Pixo).**
1. Create a free account on rive.app, open the editor (browser or desktop app).
2. New file → one artboard (for example 500 × 500).
3. Draw Pixo with shapes, or import an SVG made in Figma/Illustrator. Put the parts that move in
   their own groups: body, eyes, mouth, antenna.
4. Make timelines: `idle` (loop: breathe, blink), `talk` (loop: mouth opens/closes), `listen` (loop:
   antenna glows), `show`, `happy`, `dance` (one shot each).
5. Add a state machine named `Pixo`, add the inputs from the table, and wire the transitions
   (for example `idle → talk` when `isTalking` is true, `talk → idle` when false; `Any State → happy`
   on the `happy` trigger, `happy → idle` at the end).
6. Test it in the editor's state machine panel, then **Export → for runtime** to get the `.riv` file.

   Check the export rules of your Rive plan before investing time: Rive has changed what the free plan
   can export more than once. If export needs a paid plan, the alternatives are below.

**B. Start from a community file.** The Rive community (rive.app/community) has free characters that
can be remixed. Check each file's license (some allow commercial use, some don't) and rename its state
machine and inputs to match the contract.

**C. Commission an animator** with this page as the brief. Ask for the `.riv` file *and* the source
`.rev` file so we can change it later.

## 3. Alternatives to Rive (for the record)

- **Lottie** (After Effects export): good for one-shot animations, but no state machine; the app would
  have to manage the states itself.
- **Spine / sprite sheets**: game-industry standard, heavier tooling, more code on the app side.
- **Compose drawing only** (today's placeholder): free and simple, but every animation is code.

Rive was chosen because the official mission names it and because its state machine keeps the
animation logic inside the art file.

## 4. Rive API version

The app uses Rive Android 11's `RiveAnimationView` with state machine inputs. Rive 11 marks this API
as legacy in favour of its new `app.rive` API and **data binding** (view model properties instead of
inputs). The legacy API works and is the one most examples use, so Prototype 0 keeps it. When the real
`pixo.riv` is made, decide whether to build it with data binding instead; the contract above then
becomes view model properties with the same names.
