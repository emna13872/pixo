# 11 · Médias à produire

Chaque média a sa fiche dans `library/media/` (chemin, état, licence). Ce tableau est le récapitulatif de l'unité 1.

## Règles pour tous les médias

- **Images :** PNG carré 1024 × 1024, fond clair uni, **un seul style pour tout le programme** (le style 3D « dessin animé » des 4 images Canva déjà faites), un seul sujet bien centré, pas de texte dans l'image, pas de croix rouge ni de geste négatif.
- **Chansons :** MP3, 20 à 60 secondes, air simple et connu, paroles avec seulement les mots de l'unité, paroles minutées en millisecondes dans la fiche (`lyrics`).
- **Vidéos :** MP4, courtes (moins d'une minute). Aucune n'est utilisée dans l'unité 1.
- **Licence :** noter la source et les conditions dans la fiche. Rien n'est utilisable avec de vrais enfants tant que `terms` n'est pas `cleared`.

## Images de l'unité 1 (16)

| Fiche | Fichier | Ce que montre l'image (consigne de production) | État | Licence |
| --- | --- | --- | --- | --- |
| `m_img_bye` | `media/words/bye.png` | Un enfant qui part en faisant au revoir de la main | existe (test) | to_check |
| `m_img_goodbye` | `media/words/goodbye.png` | Un enfant à la porte qui dit au revoir à sa maman | à produire | to_check |
| `m_img_hello` | `media/words/hello.png` | Un enfant souriant qui fait coucou de la main | existe (test) | to_check |
| `m_img_hi` | `media/words/hi.png` | Deux enfants qui se saluent, main levée | à produire | to_check |
| `m_img_me_too` | `media/words/me_too.png` | Deux enfants qui lèvent la main ensemble | à produire | to_check |
| `m_img_my_name_is` | `media/words/my_name_is.png` | Un enfant qui se montre du doigt avec une étiquette de prénom | à produire | to_check |
| `m_img_no` | `media/words/no.png` | Un enfant qui secoue la tête, main levée (sans croix rouge) | existe (test) | to_check |
| `m_img_ok` | `media/words/ok.png` | Un enfant qui fait le signe OK avec la main | à produire | to_check |
| `m_img_please` | `media/words/please.png` | Un enfant qui tend la main poliment vers un biscuit | à produire | to_check |
| `m_img_see_you` | `media/words/see_you.png` | Deux enfants qui se séparent en souriant devant l'école | à produire | to_check |
| `m_img_sorry` | `media/words/sorry.png` | Un enfant désolé devant un verre renversé | à produire | to_check |
| `m_img_thank_you` | `media/words/thank_you.png` | Un enfant qui reçoit un cadeau, main sur le cœur | à produire | to_check |
| `m_img_well_done` | `media/words/well_done.png` | Un enfant qui reçoit une médaille, confettis | à produire | to_check |
| `m_img_whats_your_name` | `media/words/whats_your_name.png` | Un enfant qui pose une question à un autre, point d'interrogation | à produire | to_check |
| `m_img_wow` | `media/words/wow.png` | Un enfant émerveillé, bouche ouverte, devant un arc-en-ciel | à produire | to_check |
| `m_img_yes` | `media/words/yes.png` | Un enfant qui hoche la tête, pouce levé | existe (test) | to_check |

Les 4 images existantes sont sur le PC dans `content/media/images/word_*.png` : à copier dans `content-db/media/words/` en les renommant (`word_hello.png` → `hello.png`). L'image « no » est à refaire sans croix rouge.

**Consigne type pour le générateur d'images Canva** (garder la même pour toutes) :

> 3D cartoon illustration for young children, soft colours, plain light background, one child character, centred, friendly, no text. Scene: *(la phrase de la colonne « Ce que montre l'image », traduite)*.

## Chanson de l'unité 1

| Fiche | Fichier | État | Licence |
| --- | --- | --- | --- |
| `m_song_hello` | `media/songs/song_hello.mp3` (21 s, air de Frère Jacques) | existe (test) | `test_only` : Suno plan gratuit, à régénérer sur un plan payant avant de vrais enfants |

Paroles : « Hello, hello! Hello, hello! / Yes, yes, yes! Yes, yes, yes! / Hello, friend! Hello, friend! / Bye-bye! Bye-bye! ». Le fichier est sur le PC dans `notes\media\song_hello.mp3` : à copier dans `content-db/media/songs/`.

Idée pour la suite : une 2e version qui reprenne aussi les mots de u1-s2 à u1-s4 (please, thank you, my name's…).

## Ce qui n'est pas un média de contenu

- `celebration_001` (animation de bravo), le visage de Pixo, le signe « je t'écoute » : c'est l'**app** (Montassar).
- La voix de Pixo : synthèse vocale Azure, fabriquée par le moteur.

## Licences à régler avant de vrais enfants

| Source | Question |
| --- | --- |
| Canva (images IA) | Vérifier que la licence de contenu Canva autorise l'usage dans une app pour enfants |
| Suno | Le plan gratuit interdit l'usage commercial : régénérer sur un plan payant |
