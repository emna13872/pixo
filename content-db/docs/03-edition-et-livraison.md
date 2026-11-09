# 03 · Édition et livraison : ta version et celle de Viven

## L'idée : un Word et son PDF

Une même séance existe sous **deux formes** :

| | Document d'**édition** (le « Word ») | Fichier **livré** (le « PDF ») |
| --- | --- | --- |
| Où | `library/sessions/u1-s1.json` (plus tard : table `content_document` dans Supabase) | `published/u1-s1.v1.json` (plus tard : table `published_session`) |
| Qui l'écrit | Toi | L'outil de publication, jamais à la main |
| Forme | Cite les autres documents **par leur id** | **Autonome** : tout est recopié dedans |
| Format | Le nôtre ([schéma](../schemas/session.schema.json)) | Celui de Viven, contrat v0.5 + nos ajouts ([schéma](../schemas/delivered-session.schema.json)) |
| Change ? | Oui, tant que tu travailles | **Jamais** une fois publié (figé) |

## Pourquoi deux formes

- **Pour toi (édition) :** un mot existe une seule fois. Si tu corriges les variantes de « hello », toutes les séances qui l'utilisent sont corrigées. Recopier « hello » dans 30 séances, c'est 30 endroits à corriger.
- **Pour le moteur (livré) :** il reçoit un fichier complet et n'a rien à chercher ailleurs. C'est plus simple, plus rapide, et ça marche hors ligne.
- **Viven n'a pas à changer son format :** il reçoit toujours son JSON.

## Ce que fait la publication, exactement

| Dans ton document d'édition | Devient dans le fichier livré |
| --- | --- |
| `"objectives": ["obj_gse10_speak_greet"]` | `"objectives": [{"id": "obj_gse10_speak_greet", "title": "Saluer et prendre congé (hello, hi, bye)", "framework": "GSE Young Learners", "gse_value": 10, "skill": "speaking"}]` |
| `"new_words": ["w_hello", …]` + les mots cités dans les activités | `"words": [{"id": "w_hello", "word": "Hello", "uri": "media/words/hello.png", "type": "vocabulary", "accepted_variants": [...]}, …]` |
| `"media_id": "m_song_hello"` (chanson) | `"media_uri"`, `"lyrics"` (texte complet) et `"timestamps"` (lignes minutées en ms) |
| `"images": [{"word_id": "w_hello"}, …]`, `"correct_word_id": "w_hello"` (touch) | `"images": [{"label": "Hello", "uri": "media/words/hello.png"}, …]`, `"correct_label": "Hello"` |

Avant de fabriquer quoi que ce soit, la publication **vérifie tout** (voir [07-verifications](07-verifications.md)). S'il y a une seule erreur, rien n'est publié.

## Les versions figées

- Chaque document a un champ `version`. Le fichier livré s'appelle `<séance>.v<version>.json`.
- Une fois publié, **on n'y touche plus**. Pour corriger : modifier le document d'édition, passer `version` à 2, republier. Le fichier `.v1` reste, le `.v2` s'ajoute.
- L'outil le garantit : si `u1-s1.v1.json` existe déjà et que le contenu a changé, il refuse (code `F01`) et demande de passer en version 2. Dans Supabase, un déclencheur empêche aussi de modifier une version publiée.

**Pourquoi :**

1. Un enfant au milieu de la version 1 ne voit pas la séance changer sous ses yeux.
2. La progression enregistre « u1-s1 **version 1** » : on saura toujours exactement ce que l'enfant a vu.
3. On peut comparer deux versions et revenir en arrière.

Khan Academy fait pareil (ils publient des versions figées de leur contenu).

## Pourquoi JSON

- C'est le format d'échange le plus courant entre programmes : Python (Viven) et Kotlin (Montassar) le lisent directement.
- Il se lit et s'écrit à la main (tu as écrit la séance Colours toi-même).
- Il gère bien les choses **imbriquées** (une séance contient des activités, qui contiennent des images), ce que des tableaux à colonnes fixes gèrent mal.
- Postgres (Supabase) sait le stocker et le chercher (JSONB), et un **schéma JSON** permet de le vérifier automatiquement.

## Et le fichier Colours (u2-s1) déjà envoyé à Viven ?

C'est un fichier **livré**, écrit à la main avant l'outil. Il respecte le schéma livré (vérifié). Quand l'unité 2 sera écrite dans `library/`, il sera refait par la publication.
