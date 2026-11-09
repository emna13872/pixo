# 07 · Les vérifications de l'outil

`pixo_content.py check` (et `publish`, qui vérifie d'abord) affiche chaque problème avec un **code**.

- **ERREUR** : bloque la publication. À corriger.
- **ATTENTION** : n'empêche pas une publication de test, mais à régler avant de vrais enfants.

## Forme (S)

| Code | Vérifie | Exemple de message |
| --- | --- | --- |
| S01 | Le document respecte son schéma JSON (champs, types, valeurs permises) | `schéma word : accepted_variants/0 : 'Hello' does not match …` |
| S02 | Le nom du fichier est l'id | `le nom du fichier doit être l'id (w_hello.json)` |
| S03 | Chaque id est unique dans toute la bibliothèque | `id w_hello déjà utilisé dans …` |
| S04 | Le fichier livré respecte le schéma de Viven | (ne devrait jamais arriver : c'est l'outil qui le fabrique) |

## Renvois (R)

| Code | Vérifie |
| --- | --- |
| R01 | Chaque média cité (image d'un mot, chanson) existe |
| R02 | Chaque mot cité par un média existe |
| R03 | Chaque séance est dans la carte du programme (`program.json`) |
| R04 | Chaque objectif cité existe |
| R05 | Chaque mot cité (mots nouveaux, activités, images) existe |
| R06 | ATTENTION : un mot dit être enseigné dans une séance pas encore écrite |

## Variantes (V)

| Code | Vérifie |
| --- | --- |
| V01 | Une variante n'est jamais un autre mot du programme (comparé aux 384 items du curriculum et aux autres mots) |
| V02 | Variantes en minuscules, et une même variante n'est pas acceptée pour deux mots |

## Structure de la séance (A)

| Code | Vérifie |
| --- | --- |
| A01 | Ids des activités uniques |
| A02 | Positions de 1 à N, sans trou ni doublon |
| A03 | Première activité = bonjour, dernière = au revoir (après les rattrapages) |
| A04 | Chaque rattrapage cité existe |
| A05 | Un rattrapage est en `retry_only` |
| A06 | Un rattrapage est placé après son exercice |
| A07 | Pas de rattrapage sur un rattrapage ni sur une récompense |
| A08 | ATTENTION : un rattrapage que personne n'appelle |

## Pédagogie (P)

| Code | Vérifie |
| --- | --- |
| P01 | **5 mots maximum par phrase** dans une consigne (`{name}` compte pour un mot) |
| P02 | **Jamais « No » ni « Wrong »** dans une consigne, sauf quand « no » est le mot enseigné |
| P03 | **Prénom au moins 3 fois** dans la séance |
| P04 | **Montré avant d'être demandé** : un mot nouveau a son `present` avant son `repeat` ou son `touch` |
| P05 | Une image de `touch` montre un mot nouveau ou déjà appris (jamais un mot pas encore vu) |
| P06 | Chaque mot nouveau a un `present` et un `repeat` |
| P07 | Pas de révision dans la toute première séance ; ATTENTION s'il n'y en a pas ensuite |

## Médias (M)

| Code | Vérifie |
| --- | --- |
| M01 | Licence : `--release` exige `cleared` ; en test, ATTENTION |
| M02 | Média à produire (`production: todo`) : ATTENTION en test, ERREUR en `--release` |
| M03 | ATTENTION : fichier absent de `content-db/media/` |

## Versions (F)

| Code | Vérifie |
| --- | --- |
| F01 | Un fichier déjà publié ne change jamais : si le contenu a changé, passe la séance en version suivante |

## Ce qui n'est pas (encore) vérifié

- L'orthographe et le naturel de l'anglais : relecture humaine.
- Que l'image correspond bien au mot : à l'œil.
- La couverture complète du référentiel : visible dans `published/index.json` (`coverage`), pas une erreur.
