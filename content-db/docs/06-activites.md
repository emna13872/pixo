# 06 · Les activités

Une séance est une liste d'activités. Chaque activité a un **type** (ce qu'on fait) et une **catégorie** (à quoi elle sert).
Les champs exacts : [04-schema-seance](04-schema-seance.md).

## Les 8 types en service

| Catégorie | Type | Pixo… | L'écran (Montassar) | L'enfant | Noté ? |
| --- | --- | --- | --- | --- | --- |
| `routine` | `greeting` | dit bonjour / au revoir avec le prénom | Pixo en grand | écoute | non |
| `teaching` | `present` | montre une image, dit le mot 2 fois | image du mot en grand | regarde, écoute | non |
| `exercise` | `repeat` | « Say hello, {name}! » | image + signe « je t'écoute » | dit le mot | oui |
| `exercise` | `touch` | « Touch yes! » | 2 à 4 grandes images | touche la bonne | oui |
| `exercise` | `visual_description` | « What's this? » | une image + « je t'écoute » | dit ce qu'il voit | oui |
| `exercise` | `review` | « Do you remember? » | comme le type indiqué | révise 2 mots déjà vus | oui |
| `reward` | `sing_with_me` | « Let's sing! » | Pixo danse, paroles en karaoké | chante s'il veut | non |
| `reward` | `watch_video` | — | vidéo plein écran | regarde | non |

`repeat`, `touch`, `visual_description`, `sing_with_me`, `watch_video` viennent du contrat v0.5 de Viven. J'ai ajouté `greeting`, `present`, `review` et les catégories `routine`, `teaching`.

## Réussite et échec (pour Viven)

- **repeat / visual_description :** réussi si ce que la reconnaissance vocale entend est dans `accepted_variants` du mot (ou **commence** par une variante si `match` = `starts_with`). Silence pendant `response_timeout` secondes = essai raté.
- **touch :** réussi si l'image touchée a le `label` égal à `correct_label`.
- **Pas réussi :** Pixo encourage (« Try again! »), **jamais « No » ni « Wrong »**, redit le mot. Après `max_attempts` essais ratés, on passe à la suite et le rattrapage est noté.
- Une image ratée se secoue doucement, sans croix rouge.

## Les rattrapages

1. Le moteur joue toutes les activités `normal` dans l'ordre des positions.
2. Un exercice raté (tous les essais) → ses `retry_activity_ids` sont notés.
3. Juste avant l'au revoir, le moteur joue les rattrapages notés, dans l'ordre de la liste.
4. Un rattrapage est `retry_only`, plus facile (moins d'images, « Again! Hello! »), 2 essais, 0 point.
5. Un rattrapage n'a pas de rattrapage ; une récompense non plus.
6. Tout réussi → aucun rattrapage joué. L'au revoir est **toujours la dernière activité**.

## Les types proposés (à implémenter plus tard)

Pas utilisés dans l'unité 1 ; Viven et Montassar n'ont qu'à les prévoir. Inspirés de Duolingo et Duolingo ABC, adaptés à des enfants qui ne lisent pas encore (l'image et le son remplacent le texte).

| Type | Catégorie | Niveau | Idée |
| --- | --- | --- | --- |
| `match_pairs` | exercise | Pré-A1 | Relier chaque son à son image (plus tard : chaque mot écrit à son image) |
| `dialogue` | exercise | Pré-A1 | Petit échange avec Pixo, chacun son tour (« What's your name? » → « My name's Sami ») |
| `find_in_scene` | exercise | Pré-A1 | Trouver un objet dans une grande image (« Find the red ball! ») |
| `memory` | reward | Pré-A1 | Cartes à retourner ; Pixo dit le mot de chaque carte |
| `trace` | exercise | A1 (7-8 ans) | Tracer une lettre ou un mot au doigt |
| `build_word` / `build_sentence` | exercise | A1 (7-8 ans) | Remettre lettres ou mots dans l'ordre |

L'écriture au clavier n'est pas proposée (pas adaptée à cet âge).

## Le mode « jouer avec Pixo » (proposition)

Pas un type d'activité : un **mode de l'app**, entre les séances. Pixo est un robot que l'enfant a tous les jours ; il voudra jouer plus que 3 fois par semaine.

- Contenu : révisions, la chanson, `memory`, `match_pairs`, petits `dialogue`, **seulement avec les mots déjà vus**.
- Le moteur choisit le contenu à partir de la progression (comme `review`).
- Compte dans la limite de temps par jour du parent (20 min par défaut).
- Met à jour les boîtes des mots, ne débloque jamais une nouvelle séance.

## Points à caler avec Viven et Montassar

| Point | Pour qui | Ma proposition |
| --- | --- | --- |
| Qui choisit les mots de `review` | Viven | Le moteur, il a la progression ([08](08-revision-boites-et-rythme.md)) |
| Modèle de score A, B ou C | Viven | B, score par objectif (colle aux objectifs GSE, évite de compter deux fois les rattrapages) |
| Rattrapage aussi raté | Viven | Pixo encourage, dit le mot une dernière fois, passe à la suite ; le mot revient en révision |
| « My name's {name} » | Viven | Réussi si la réponse commence par une variante (`match: starts_with`) |
| Animation `celebration_001`, signe « je t'écoute » | Montassar | Côté app, avec le visage de Pixo validé |
| Ordre des images dans `touch` | Montassar | L'app mélange à chaque essai |
| Voix de Pixo | Viven, Montassar | Même voix pour mots et expressions, débit lent |
