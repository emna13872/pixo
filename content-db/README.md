# content-db : le contenu pédagogique de Pixo

Tout le contenu pédagogique au même endroit : ce que Pixo enseigne, les règles qui le vérifient,
les fichiers livrés au moteur et la base de données. Référente : **Emna**.

> Nouveau ici ? Lis dans l'ordre [01-vue-d-ensemble](docs/01-vue-d-ensemble.md), puis
> [03-edition-et-livraison](docs/03-edition-et-livraison.md), puis les [fiches mémo](docs/fiches-memo.md).

## Le dossier

| Dossier | Ce qu'il contient | Qui l'écrit |
| --- | --- | --- |
| `library/` | **La bibliothèque** : les documents que tu écris (programme, séances, mots, objectifs, médias). C'est la source de vérité. | Toi |
| `schemas/` | Les schémas JSON : la forme exacte de chaque type de document | Toi (rarement) |
| `published/` | Les **fichiers livrés** au moteur (format de Viven), un par séance et par version, + `index.json` | L'outil, jamais à la main |
| `tools/` | `pixo_content.py` : vérifie la bibliothèque, publie, exporte en SQL | — |
| `db/` | Le script SQL de la base de contenu Supabase (`001_content_schema.sql`) et `seed.sql` (généré) | — |
| `media/` | Les fichiers images et chansons en local (pas dans Git) | Toi |
| `reference/` | Le curriculum Pré-A1 complet (CSV + générateur) | — |
| `docs/` | Toute la documentation, en fiches | — |

## Où on en est

- Unité 1 « Hello! » : 16 mots, 4 objectifs, 4 séances écrites, vérifiées et publiées en version 1 (test).
- Médias : 4 images et la chanson existent en version de test ; 12 images à produire. Voir [11-medias-a-produire](docs/11-medias-a-produire.md).
- Base de données : script prêt et testé en local, pas encore installé dans Supabase. Voir [09-base-de-donnees](docs/09-base-de-donnees.md).

## Les 3 commandes

Depuis la racine du dépôt `pixo`, dans PowerShell :

```powershell
uv run --with jsonschema python content-db/tools/pixo_content.py check     # vérifier après chaque modification
uv run --with jsonschema python content-db/tools/pixo_content.py publish   # fabriquer les fichiers livrés
uv run --with jsonschema python content-db/tools/pixo_content.py sql       # fabriquer db/seed.sql pour Supabase
```

Détails : [10-commandes](docs/10-commandes.md).

## Toutes les fiches

| Fiche | Sujet |
| --- | --- |
| [01-vue-d-ensemble](docs/01-vue-d-ensemble.md) | Les 3 parties du système, les 2 bases, qui fait quoi |
| [02-programme-et-referentiels](docs/02-programme-et-referentiels.md) | CECRL, GSE, Cambridge, le programme en chiffres, l'unité 1 |
| [03-edition-et-livraison](docs/03-edition-et-livraison.md) | Ta version et celle de Viven, la publication, les versions figées |
| [04-schema-seance](docs/04-schema-seance.md) | Le JSON d'une séance, champ par champ (édition et livré) |
| [05-schemas-mot-objectif-media-programme](docs/05-schemas-mot-objectif-media-programme.md) | Les 4 autres types de documents |
| [06-activites](docs/06-activites.md) | Les 8 types d'activités, les rattrapages, les types proposés, le mode « jouer avec Pixo » |
| [07-verifications](docs/07-verifications.md) | Chaque règle vérifiée par l'outil, avec son code |
| [08-revision-boites-et-rythme](docs/08-revision-boites-et-rythme.md) | La révision espacée (boîtes de Leitner) et le rythme des séances |
| [09-base-de-donnees](docs/09-base-de-donnees.md) | La base Supabase : tables, pourquoi JSONB, versions figées, sécurité |
| [10-commandes](docs/10-commandes.md) | Comment vérifier, publier, ajouter une séance |
| [11-medias-a-produire](docs/11-medias-a-produire.md) | Les images et chansons à produire, avec leurs consignes et licences |
| [fiches-memo](docs/fiches-memo.md) | Questions / réponses pour réviser avant une réunion |
| [glossaire](docs/glossaire.md) | Les mots techniques en une phrase |

Le suivi du travail et le journal des décisions sont dans `notes/content-db/` (sur le PC seulement, jamais poussés).
