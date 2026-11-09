# 04 · Le JSON d'une séance, champ par champ

Deux schémas : [`session.schema.json`](../schemas/session.schema.json) (édition, ce que tu écris) et
[`delivered-session.schema.json`](../schemas/delivered-session.schema.json) (livré, fabriqué par l'outil).
Exemple complet : [`library/sessions/u1-s1.json`](../library/sessions/u1-s1.json) → [`published/u1-s1.v1.json`](../published/u1-s1.v1.json).

## Un schéma JSON, c'est quoi ?

Un fichier qui décrit **la forme obligatoire** d'un document : quels champs, de quel type, lesquels sont obligatoires, quelles valeurs sont permises. L'outil compare chaque document à son schéma (erreur `S01` si ça ne colle pas). C'est comme un formulaire avec des cases obligatoires.

## L'en-tête de la séance (édition)

| Champ | Obligatoire | Exemple | Rôle |
| --- | --- | --- | --- |
| `id` | oui | `"u1-s1"` | Nom permanent. Identique au nom du fichier |
| `type` | oui | `"session"` | Type de document |
| `version` | oui | `1` | +1 à chaque publication d'un changement |
| `status` | oui | `"draft"` | `draft` (brouillon), `published`, `archived` |
| `updated_at` / `updated_by` | oui | `"2026-11-09T15:00:00Z"` / `"emna"` | Qui a modifié, quand |
| `program_id`, `module_id`, `unit_id` | oui | `"pixo-english"`, `"m1"`, `"u1-hello"` | Où la séance se range |
| `position` | oui | `1` | Ordre dans l'unité |
| `title` | oui | `"Hello and bye"` | Titre court (anglais) |
| `goal_fr` | non | `"Dire bonjour, au revoir, oui et non"` | Le but, en français |
| `objectives` | oui | `["obj_gse10_speak_greet"]` | Ids des objectifs visés (un ou plusieurs) |
| `new_words` | oui | `["w_hello", "w_bye", "w_yes", "w_no"]` | Ids des mots nouveaux de la séance |
| `activities` | oui | `[ … ]` | La liste des activités |

Dans le fichier **livré**, l'en-tête garde `id`, `version`, `position`, `title`, `program_id`, `module_id`, `unit_id`, et reçoit `objectives` (objets complets) et `words` (mots complets). `type`, `status`, `updated_*`, `goal_fr` et `new_words` ne sont pas livrés.

## Les champs communs à toutes les activités

| Champ | Exemple | Rôle |
| --- | --- | --- |
| `id` | `"a_repeat_hello"` | Unique dans la séance |
| `position` | `4` | Ordre de passage : 1, 2, 3… sans trou. Le moteur trie par position, jamais par l'ordre du tableau |
| `category` | `"exercise"` | `routine`, `teaching`, `exercise` ou `reward` (imposé par le type) |
| `type` | `"repeat"` | Un des 8 types ([06-activites](06-activites.md)) |
| `execution_mode` | `"normal"` | `normal` : jouée pour tous. `retry_only` : seulement comme rattrapage |
| `instruction` | `"Say hello, {name}!"` | Ce que dit Pixo. `{name}` = le prénom de l'enfant |

## Les champs des exercices

| Champ | Exemple | Rôle |
| --- | --- | --- |
| `score` | `10` | Points si réussi (0 pour un rattrapage, en attendant le modèle de score) |
| `max_attempts` | `3` | Nombre d'essais (2 pour un rattrapage) |
| `retry_activity_ids` | `["a_repeat_hello_retry_1"]` | Rattrapages si l'exercice est raté (vide pour un rattrapage) |
| `success_celebration` | `"celebration_001"` | Nom de l'animation de bravo (l'app choisit l'animation) |
| `response_timeout` | `5` | Secondes d'attente d'une réponse orale (`repeat`, `visual_description`) |

## Les champs propres à chaque type

| Type | Édition (toi) | Livré (moteur) |
| --- | --- | --- |
| `greeting` | `moment` : `hello` ou `bye` | pareil |
| `present` | `word_id`, `say_times` (2) | pareil |
| `repeat` | `word_id` | pareil (le mot complet est dans `words`) |
| `touch` | `images: [{word_id}]`, `correct_word_id` | `images: [{label, uri}]`, `correct_label` |
| `visual_description` | `image_media`, `expected_word_id` | `uri`, `expected_word_id` |
| `review` | `review_count`, `review_activity_type` | pareil (le moteur choisit les mots) |
| `sing_with_me` | `media_id` | `media_uri`, `lyrics`, `timestamps` |
| `watch_video` | `media_id` | `media_uri` |

## Exemples (édition)

```json
{ "id": "a_present_hello", "position": 3, "category": "teaching", "type": "present",
  "execution_mode": "normal", "instruction": "Look! Hello!", "word_id": "w_hello", "say_times": 2 }

{ "id": "a_repeat_hello", "position": 4, "category": "exercise", "type": "repeat",
  "execution_mode": "normal", "score": 10, "instruction": "Say hello, {name}!", "word_id": "w_hello",
  "max_attempts": 3, "response_timeout": 5, "success_celebration": "celebration_001",
  "retry_activity_ids": ["a_repeat_hello_retry_1"] }

{ "id": "a_touch_1", "position": 11, "category": "exercise", "type": "touch",
  "execution_mode": "normal", "score": 10, "instruction": "Touch hello!",
  "images": [{"word_id": "w_hello"}, {"word_id": "w_bye"}, {"word_id": "w_yes"}],
  "correct_word_id": "w_hello", "max_attempts": 3, "success_celebration": "celebration_001",
  "retry_activity_ids": ["a_touch_1_retry_1"] }

{ "id": "a_repeat_hello_retry_1", "position": 13, "category": "exercise", "type": "repeat",
  "execution_mode": "retry_only", "score": 0, "instruction": "Again! Hello!", "word_id": "w_hello",
  "max_attempts": 2, "response_timeout": 5, "success_celebration": "celebration_001",
  "retry_activity_ids": [] }
```

## L'ordre d'une séance (positions)

1. `greeting` hello → 2. `sing_with_me` → 3. `review` (sauf 1re séance) → pour chaque mot : `present` puis `repeat` → 2 `touch` → les rattrapages (`retry_only`) → `greeting` bye **en dernier**.

## Conventions de nommage des ids

| Quoi | Forme | Exemple |
| --- | --- | --- |
| Séance | `u<unité>-s<n>` | `u1-s3` |
| Activité | `a_<type>_<mot>` ou `a_touch_<n>`, rattrapage `…_retry_1` | `a_repeat_ok_retry_1` |
| Mot | `w_<mot>` | `w_thank_you` |
| Objectif | `obj_gse<valeur>_<compétence>_<sujet>` | `obj_gse12_speak_ask_name` |
| Média | `m_img_<mot>`, `m_song_<unité>` | `m_img_hello`, `m_song_hello` |

Lettres minuscules, chiffres, `_` et `-` seulement. Un id ne change **jamais**, même si on renomme le titre.
