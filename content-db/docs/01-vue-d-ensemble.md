# 01 · Vue d'ensemble

## En une phrase

**Je fabrique des séances, Viven les fait jouer, Montassar les montre.**

## Les 3 rôles

| Qui | Partie | Ce qu'elle fait | Ce qu'elle ne fait pas |
| --- | --- | --- | --- |
| **Emna** | Contenu | Décide **quoi** enseigner : programme, séances, mots et variantes, consignes de Pixo, objectifs, médias et licences | Ne décide pas comment le moteur juge une réponse |
| **Viven** | Moteur (Python) | Décide **comment** jouer : lit le JSON, fait parler Pixo, écoute, juge, lance les rattrapages, choisit les mots à réviser, enregistre la progression | N'invente pas de contenu |
| **Montassar** | App (Android) | **Montre** : visage de Pixo, images, boutons, micro | Ne décide jamais rien |

## Le chemin d'une séance

```
 Toi                     Publication                       Moteur (Viven)          App (Montassar)
 library/  ──check──▶  vérifie + recopie + fige  ──▶  published/u1-s1.v1.json  ──▶  joue  ──▶  affiche
 (renvois par id)                                     (autonome, format Viven)       ▲
                                                                                      │
                                                          Base de progression ◀───────┘
                                                          (ce que chaque enfant sait)
```

## Les 2 bases de données (à bien distinguer)

| | Base de **contenu** (toi) | Base de **progression** (Viven) |
| --- | --- | --- |
| Contient | Ce qu'on enseigne | Ce que chaque enfant a fait |
| Exemples | séances, mots, objectifs, médias | parents, enfants, essais, scores, boîtes des mots |
| Change | Rarement (quand tu écris) | Tout le temps (à chaque réponse) |
| Pareil pour tous ? | Oui | Non, une ligne par enfant |
| Forme | Documents JSON (JSONB) | Tables classiques |
| Fiche | [09-base-de-donnees](09-base-de-donnees.md) | (document de Viven) |

## Ce qui est décidé et ce qui ne l'est pas

- **Décidé par moi (contenu) :** référentiels, programme, types d'activités, variantes, règles pédagogiques, format d'édition, objectifs partagés, médias avec licence. Voir [02](02-programme-et-referentiels.md) et [06](06-activites.md).
- **À caler avec Viven et Montassar (leur code) :** qui choisit les mots de révision, le modèle de score, ce qui se passe quand un rattrapage échoue, les animations. Voir la fin de [06-activites](06-activites.md).
- **Pas encore choisi :** l'outil d'édition (Directus ou le Lesson Manager). En attendant, on écrit les JSON à la main dans `library/` et l'outil les vérifie.
