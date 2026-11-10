# 10 · Les commandes et les gestes du quotidien

Toutes les commandes se lancent depuis la racine du dépôt `pixo`, dans PowerShell. `uv` installe tout seul la bibliothèque `jsonschema` le temps de la commande.

| Commande | Ce qu'elle fait |
| --- | --- |
| `uv run --with jsonschema python content-db/tools/pixo_content.py check` | Vérifie toute la bibliothèque. À lancer après **chaque** modification |
| `… pixo_content.py check --release` | Même chose avec les règles strictes (vrais enfants : licences, médias finis) |
| `… pixo_content.py publish` | Vérifie, puis fabrique `published/<séance>.v<version>.json` et `published/index.json` |
| `… pixo_content.py publish --release` | Publication pour de vrais enfants (refuse tout média non autorisé) |
| `… pixo_content.py sql` | Fabrique `db/seed.sql` pour charger la bibliothèque dans Supabase |

Résultat : `OK : 0 erreur(s), N avertissement(s)` ou `ÉCHEC`. Chaque code est expliqué dans [07-verifications](07-verifications.md).

## Corriger une séance déjà publiée

1. Ouvrir `library/sessions/u1-s1.json`, corriger.
2. Passer `"version": 1` à `"version": 2` et mettre à jour `updated_at`.
3. `publish` → `published/u1-s1.v2.json` s'ajoute ; `v1` reste tel quel.
4. Envoyer le nouveau fichier à Viven.

Si tu oublies l'étape 2, l'outil refuse (code `F01`).

## Corriger un mot

1. Modifier `library/words/w_hello.json` (par exemple ajouter une variante), passer sa `version` à +1.
2. Les séances qui utilisent ce mot doivent être republiées : passer leur `version` à +1, puis `publish`.

## Ajouter une séance (exemple : u2-s1)

1. Créer les **objectifs** manquants dans `library/objectives/`.
2. Créer les **mots** dans `library/words/` (`w_red.json`…) avec leurs variantes et leur image.
3. Créer les **fiches médias** dans `library/media/` (`m_img_red.json`, `m_song_colours.json`).
4. Copier une séance existante dans `library/sessions/u2-s1.json`, changer l'id, l'unité, les mots, les consignes.
5. `check` jusqu'à 0 erreur, puis `publish`.

L'id doit déjà être dans `program.json` (c'est le cas pour les 96 séances du Pré-A1).

## Ajouter un fichier média

1. Mettre le fichier au chemin de sa fiche : `content-db/media/words/hello.png`.
2. Dans la fiche (`library/media/m_img_hello.json`), mettre `production` à `test` ou `final` et remplir la licence.
3. `check` : l'avertissement M02 / M03 disparaît.

Les fichiers médias ne vont pas dans Git (trop lourds) : ils restent sur le PC, puis iront dans Supabase Storage.

## Git

- Le contenu (`library/`, `schemas/`, `published/`, `docs/`) est poussé sur GitHub, sur une branche, puis fusionné par une pull request.
- Les notes de travail (`notes/content-db/`) restent sur le PC.
