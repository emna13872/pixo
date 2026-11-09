# 05 · Les 4 autres documents : mot, objectif, média, programme

Les champs `id`, `type`, `version`, `status`, `updated_at`, `updated_by` sont communs à tous (voir [04](04-schema-seance.md)).

## Mot (`word`) · [schéma](../schemas/word.schema.json) · exemple [`w_hello.json`](../library/words/w_hello.json)

| Champ | Exemple | Rôle |
| --- | --- | --- |
| `id` | `"w_hello"` | Commence par `w_` |
| `text` | `"Hello"` | Le mot tel que Pixo le dit. Devient `word` dans le fichier livré |
| `kind` | `"vocabulary"` | `vocabulary` (un mot) ou `chunk` (expression apprise d'un bloc : « thank you ») |
| `accepted_variants` | `["hello", "helo", "hallo", "hullo"]` | Ce que la reconnaissance vocale peut écrire et qu'on accepte. **Minuscules**. Jamais un synonyme, jamais un autre mot du programme |
| `match` | `"exact"` | `starts_with` pour une expression suivie d'un prénom (« my name's Sami ») |
| `image_media` | `"m_img_hello"` | L'image du mot (id d'un média) |
| `unit_id`, `taught_in` | `"u1-hello"`, `"u1-s1"` | Où le mot est enseigné |
| `cambridge_list` | `true` | Dans la liste officielle Starters ? |

**Pourquoi « hi » n'est pas accepté pour « hello » :** c'est un mot à part entière (u1-s2). L'accepter en variante empêcherait de savoir si l'enfant connaît « hello ». L'outil le refuse (code `V01`). Même chose pour « thanks » (u18) et « nose » (u3).

## Objectif (`objective`) · [schéma](../schemas/objective.schema.json) · exemple [`obj_gse10_speak_greet.json`](../library/objectives/obj_gse10_speak_greet.json)

| Champ | Exemple | Rôle |
| --- | --- | --- |
| `id` | `"obj_gse10_speak_greet"` | Commence par `obj_` |
| `title_fr` | `"Saluer et prendre congé (hello, hi, bye)"` | Recopié dans le fichier livré |
| `framework` | `"GSE Young Learners"` | Le référentiel |
| `gse_value` | `10` | La note GSE (10 à 90) |
| `skill` | `"speaking"` | `listening`, `speaking`, `reading`, `writing` |
| `cefr` | `"Pre-A1"` | Le niveau |
| `official_code` | `null` | Code exact Pearson, à recopier avant usage officiel |

**Pourquoi un document à part (et pas écrit dans chaque séance) :** plusieurs séances visent le même objectif. Avec un document partagé, on peut répondre à « quelles séances travaillent GSE 12 ? » et prouver que le programme couvre le référentiel (voir `objective_to_sessions` dans `published/index.json`).

## Média (`media`) · [schéma](../schemas/media.schema.json) · exemples [`m_img_hello.json`](../library/media/m_img_hello.json), [`m_song_hello.json`](../library/media/m_song_hello.json)

| Champ | Exemple | Rôle |
| --- | --- | --- |
| `id` | `"m_img_hello"` | Commence par `m_` |
| `kind` | `"image"` | `image`, `audio`, `video` |
| `mime_type` | `"image/png"` | PNG/SVG pour les images, MP3 pour l'audio, MP4 pour la vidéo |
| `storage_path` | `"media/words/hello.png"` | Chemin du fichier (dans Storage, ou `content-db/media/` en local). Devient `uri` dans le fichier livré |
| `production` | `"test"` | `todo` (à produire), `test` (provisoire), `final` |
| `alt_text` | `"Un enfant souriant qui fait coucou"` | Ce que montre l'image ; sert aussi de consigne pour la produire |
| `duration_ms`, `lyrics` | `21000`, `[{start_ms, end_ms, text}]` | Obligatoires pour l'audio. Paroles minutées en **millisecondes** |
| `words` | `["w_hello", "w_yes"]` | Mots présents dans la chanson |
| `licence` | `{source, terms, cleared_for_children, note}` | `terms` : `cleared`, `test_only` ou `to_check` |

**Pourquoi la licence :** sans elle, rien ne garde la trace des droits. Règle : en publication `--release` (vrais enfants), un média non `cleared` est **refusé** (code `M01`). En publication de test, c'est un avertissement.

## Programme (`program`) · [schéma](../schemas/program.schema.json) · [`program.json`](../library/program.json)

La **carte** seulement : niveaux > modules > unités > ids des séances. Il ne contient pas le contenu des séances.

| Champ | Exemple | Rôle |
| --- | --- | --- |
| `title` | `"Pixo English"` | Nom du programme |
| `subject` | `"english"` | La matière (prépare l'ajout des maths) |
| `references` | `["CECRL (CEFR)", …]` | Les référentiels suivis |
| `levels[]` | `pre-a1`, `a1`, `a2` | `detail` : `full` (détaillé) ou `outline` (plan) |
| `levels[].modules[].units[].sessions` | `["u1-s1", "u1-s2", …]` | Les ids des séances, dans l'ordre |

**Pourquoi pas un seul gros fichier pour tout le programme :** chaque correction toucherait tout, et on ne pourrait pas versionner séance par séance.

## Et les maths, plus tard ?

Le même modèle marche : un programme `subject: "maths"`, des séances faites d'activités, de nouveaux types (compter, toucher le chiffre 3), et des items `n_3` à côté des mots `w_red`. Côté progression, on enregistre un « item » au lieu d'un « mot ». Rien à reconstruire.
