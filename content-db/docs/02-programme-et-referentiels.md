# 02 · Programme et référentiels

## Les 3 références

| Référence | Ce qu'elle donne | Exemple |
| --- | --- | --- |
| **CECRL** (Cadre européen, CEFR en anglais) | Les **niveaux** : Pré-A1, A1, A2… | Pixo commence au Pré-A1 |
| **GSE Young Learners** (Pearson) | Les **objectifs**, notés de 10 à 90, plus fins que le CECRL | « Saluer et prendre congé » = GSE 10 |
| **Cambridge Pre A1 Starters** | La **liste officielle de mots** pour enfants débutants | hello, red, cat… |

Pourquoi ces trois : ce sont les références reconnues pour les enfants, elles se complètent (niveau + objectifs + mots), et elles permettent de prouver aux parents et aux écoles ce que l'enfant apprend.

Adaptation : Pixo est **oral seulement** au Pré-A1 (les enfants de 5-8 ans ne lisent pas encore l'anglais).

## Le programme : Pixo English

| Niveau | Cambridge | GSE | Détail |
| --- | --- | --- | --- |
| Pré-A1 | Starters | 10-21 | **Complet** : 4 modules, 24 unités, 100 séances |
| A1 | Movers | 22-29 | Plan seulement (5 modules) |
| A2 | Flyers | 30-42 | Plan seulement (3 modules) |

Pré-A1 en chiffres :

- 4 modules → 24 unités → 96 séances + 4 bilans (un par module) = **100 séances**.
- 16 mots ou expressions par unité, **4 nouveaux par séance**.
- **384 items** : 359 de la liste Cambridge, 25 hors liste mais utiles (marqués `*` dans le CSV).
- Séances de 8 à 10 minutes.

La liste complète, séance par séance : [`reference/curriculum-pre-a1.csv`](../reference/curriculum-pre-a1.csv).
La carte en JSON (ids de toutes les unités et séances) : [`library/program.json`](../library/program.json).

## L'arborescence

**Programme > Niveau > Module > Unité > Séance > Activité**

| Niveau | Exemple | id |
| --- | --- | --- |
| Programme | Pixo English | `pixo-english` |
| Niveau | Pré-A1 | `pre-a1` |
| Module | Bonjour Pixo ! (moi et les autres) | `m1` |
| Unité | Hello! | `u1-hello` |
| Séance | Hello and bye | `u1-s1` |
| Activité | « Say hello, {name}! » | `a_repeat_hello` |

## L'unité 1 « Hello! » (écrite)

| Séance | Titre | Mots nouveaux | Objectifs |
| --- | --- | --- | --- |
| u1-s1 | Hello and bye | hello, bye, yes, no | saluer (GSE 10) |
| u1-s2 | Please and thank you | hi, goodbye, please, thank you | saluer (GSE 10), politesse (GSE 11) |
| u1-s3 | My name's… | my name's…, what's your name?, OK, sorry | se présenter (GSE 11), demander le prénom (GSE 12), politesse (GSE 11) |
| u1-s4 | Well done! | well done, wow, see you!, me too | saluer (GSE 10) |

Les documents : `library/sessions/u1-s*.json`, `library/words/`, `library/objectives/`.

## Les règles pédagogiques (vérifiées par l'outil)

1. Consignes de Pixo de **5 mots maximum par phrase**.
2. **Jamais « No » ni « Wrong »** quand l'enfant se trompe (sauf quand « no » est le mot enseigné).
3. **On montre un mot avant de le demander** (`present` avant `repeat` ou `touch`).
4. **Le prénom de l'enfant au moins 3 fois** par séance.
5. **Variantes acceptées = erreurs de reconnaissance seulement** (« know » pour « no »), jamais un synonyme, jamais un autre mot du programme.

Détail des vérifications : [07-verifications](07-verifications.md).

## À savoir

- Le programme suit les listes Cambridge, donc l'orthographe **britannique** (colour, grey, favourite). La mission parle d'anglais américain : à trancher avec l'équipe.
- Les codes officiels GSE (`official_code`) sont à recopier depuis le référentiel Pearson avant tout usage officiel ; nos titres sont des paraphrases.
