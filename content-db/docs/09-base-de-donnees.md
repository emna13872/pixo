# 09 · La base de contenu (Supabase)

Script : [`db/001_content_schema.sql`](../db/001_content_schema.sql). Données : `db/seed.sql`, fabriqué par `pixo_content.py sql`.
État : **testé en local** (Postgres 16) ; pas encore installé dans Supabase.

## Le choix en 4 phrases

1. Le contenu est stocké en **documents JSON entiers**, pas découpé en dizaines de tables (« non relationnel », comme demandé par l'équipe).
2. On le met quand même dans **Supabase**, parce que Postgres a un type de colonne **JSONB** : une case qui contient un document JSON complet, qu'on peut chercher et vérifier. On a donc une base de documents *dans* la base que l'équipe utilise déjà, sans MongoDB ni Firebase.
3. Les **fichiers** (images, chansons, vidéos) vont dans **Supabase Storage** (un dossier dans le cloud), la base garde seulement leur chemin.
4. La base de **progression** (enfants, essais, scores) est séparée et reste relationnelle : c'est celle de Viven.

## Les 4 tables

```
content_schema        content_document              content_version             published_session
(1 ligne par type)    (version de travail)          (versions publiées, FIGÉES)  (fichiers livrés, FIGÉS)
doc_type ─────────▶   id         w_hello            id + version                 session_id + version
schema (JSON)         doc_type   word               body (copie figée)           delivered (format Viven)
                      version    1                                                channel  test | release
                      status     draft
                      body       { le document entier }
```

| Table | Une ligne = | Qui écrit | Particularité |
| --- | --- | --- | --- |
| `content_schema` | Un schéma JSON (le contenu de `schemas/*.schema.json`) | L'outil | Sert à vérifier les documents |
| `content_document` | Un document en édition : séance, mot, objectif, média ou programme | L'outil (plus tard : l'éditeur) | Vérifié contre son schéma à chaque écriture (déclencheur + `pg_jsonschema`) |
| `content_version` | Une version publiée d'un document | La publication | **Figée** : un déclencheur refuse toute modification ou suppression |
| `published_session` | Un fichier livré au moteur (`published/u1-s1.v1.json`) | La publication | **Figée** aussi. `channel` : `test` ou `release` (vrais enfants) |

Plus une **vue** `latest_published_session` : « donne-moi la dernière version de chaque séance ». C'est ce que le moteur lit.

## Les mécanismes, expliqués simplement

- **Vérification à l'écriture :** quand on enregistre un document, Postgres le compare à son schéma JSON (extension `pg_jsonschema`, disponible dans Supabase). Un document mal formé est refusé, même s'il vient d'un autre outil.
- **Cohérence colonnes / document :** l'`id`, le type, la version et le statut sont à la fois dans des colonnes (pour chercher vite) et dans le document ; une contrainte vérifie qu'ils sont identiques.
- **Versions figées :** un déclencheur (`content_frozen`) refuse `UPDATE` et `DELETE` sur les versions publiées. Corriger = publier la version suivante.
- **Recherche dans les documents :** un index GIN permet des requêtes comme « quelles séances enseignent w_hello ? » :

```sql
select id from content_document where body @> '{"type": "session", "new_words": ["w_hello"]}';
```

- **Sécurité (RLS) :** lecture pour tout utilisateur connecté (moteur, app) ; écriture seulement par le rôle `service_role` (l'outil de publication). Les éditeurs de contenu seront branchés plus tard avec Supabase Auth.
- **Stockage :** un bucket privé `content-media` pour les fichiers.

## Ce qui va où

| Chose | Où |
| --- | --- |
| Programme, séances, mots, objectifs, fiches médias | `content_document` (JSONB) |
| Images, chansons, vidéos | Storage `content-media` (chemin dans la fiche média) |
| Séances livrées au moteur | `published_session` (et, si Viven préfère, aussi en fichiers dans Storage) |
| Ce que chaque enfant a fait | Base de progression (Viven), **pas ici** |

## Comment l'installer (quand on sera prêts)

1. Créer un projet Supabase **de test** (gratuit), pas celui de l'équipe.
2. Database > Extensions : activer `pg_jsonschema`.
3. SQL Editor : coller et lancer `db/001_content_schema.sql`.
4. Lancer `pixo_content.py sql`, puis coller et lancer `db/seed.sql`.
5. Vérifier : `select doc_type, count(*) from content_document group by 1;` → 1 programme, 4 séances, 16 mots, 4 objectifs, 17 médias.

Avant de toucher au Supabase de l'équipe : en parler avec Viven (c'est son projet, et sa base de progression y vit).

## Test local déjà fait

Script lancé sur Postgres 16 (avec `pg_jsonschema` simulé, car il n'existe que dans Supabase) : les tables se créent, les 42 documents et 4 séances se chargent, la modification d'une version publiée est bien refusée, et la recherche par mot fonctionne.

## Pas encore fait (prochaines étapes)

- Brancher la publication directement sur Supabase (aujourd'hui elle écrit des fichiers, puis `seed.sql` les charge).
- Remplir `content_version` à chaque publication.
- Choisir l'éditeur (Directus se branche directement sur ces tables).
