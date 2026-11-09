# Fiches mémo

Pour réviser avant une réunion : cache la réponse, lis la question, réponds, vérifie. Le lien renvoie à la fiche détaillée.

## Le système

**Q. Qui fait quoi ?**
R. Emna décide quoi enseigner (contenu). Viven décide comment le jouer (moteur). Montassar l'affiche (app), sans rien décider. → [01](01-vue-d-ensemble.md)

**Q. Combien de bases de données, et lesquelles ?**
R. Deux : la base de contenu (ce qu'on enseigne, pareil pour tous, change rarement) et la base de progression (ce que chaque enfant a fait, change tout le temps). → [01](01-vue-d-ensemble.md)

**Q. Pourquoi le contenu n'est pas relationnel ?**
R. Une séance est imbriquée (activités > images > paroles minutées). La découper en dizaines de tables est lourd. On la stocke entière, en un document JSON. → [09](09-base-de-donnees.md)

**Q. Mais Supabase est relationnel ?**
R. Oui, mais Postgres a le type JSONB : une case qui contient un document JSON entier, qu'on peut chercher et vérifier. Pas besoin de MongoDB. → [09](09-base-de-donnees.md)

**Q. Où vont les images et les chansons ?**
R. Dans Supabase Storage (un dossier dans le cloud). La base garde seulement leur chemin. → [09](09-base-de-donnees.md)

## Les deux versions d'une séance

**Q. « J'ai une version, Viven a une version » : pourquoi ?**
R. C'est la même séance sous deux formes, comme un Word et son PDF. Le document d'édition cite les mots par id ; le fichier livré, fabriqué à la publication, recopie tout et suit le format de Viven. → [03](03-edition-et-livraison.md)

**Q. Que fait la publication ?**
R. Elle vérifie tout, puis recopie dans la séance les mots (avec variantes et image), les titres des objectifs et les médias (chemin, paroles minutées). Elle écrit `published/<séance>.v<version>.json`. → [03](03-edition-et-livraison.md)

**Q. Pourquoi des versions figées ?**
R. Un enfant ne voit pas la séance changer en plein milieu, la progression sait exactement quelle version l'enfant a vue, et on peut revenir en arrière. Corriger = publier la version suivante. → [03](03-edition-et-livraison.md)

**Q. Pourquoi JSON ?**
R. Format d'échange standard, lu directement par Python et Kotlin, lisible à la main, adapté aux données imbriquées, vérifiable par un schéma. → [03](03-edition-et-livraison.md)

**Q. C'est quoi un schéma JSON ?**
R. Un fichier qui décrit la forme obligatoire d'un document (champs, types, valeurs permises). L'outil compare chaque document à son schéma. → [04](04-schema-seance.md)

**Q. C'est quoi un id ? Pourquoi il ne change jamais ?**
R. Le nom permanent d'un élément (`w_hello`, `u1-s1`). Les documents se citent par id : s'il changeait, tous les renvois casseraient. → [04](04-schema-seance.md)

**Q. C'est quoi l'index ?**
R. Un résumé fabriqué à la publication (`published/index.json`) : quelle séance enseigne quel mot, quelles séances visent quel objectif, quel média sert où. Il répond sans ouvrir 100 fichiers. → [03](03-edition-et-livraison.md)

## Le contenu

**Q. Quels référentiels, et pourquoi trois ?**
R. CECRL pour les niveaux, GSE Young Learners pour les objectifs, Cambridge Starters pour la liste de mots. Ils se complètent. → [02](02-programme-et-referentiels.md)

**Q. Le programme en chiffres ?**
R. Pixo English Pré-A1 : 4 modules, 24 unités, 100 séances (96 + 4 bilans), 384 items, 4 mots nouveaux par séance, 8 à 10 minutes. A1 et A2 en plan. → [02](02-programme-et-referentiels.md)

**Q. Pourquoi seulement 4 mots par séance ?**
R. À 5-8 ans, au-delà les enfants mélangent. Chaque mot est montré, répété, joué et révisé ensuite. → [02](02-programme-et-referentiels.md)

**Q. Les règles pédagogiques ?**
R. 5 mots max par phrase, jamais « No » ni « Wrong », montrer avant de demander, prénom au moins 3 fois, variantes = erreurs de reconnaissance seulement. Vérifiées par l'outil. → [07](07-verifications.md)

**Q. Pourquoi « hi » n'est pas accepté pour « hello » ?**
R. Les variantes servent aux erreurs de reconnaissance, pas aux synonymes, et « hi » est un mot du programme (u1-s2). → [05](05-schemas-mot-objectif-media-programme.md)

**Q. Pourquoi un objectif est un document à part ?**
R. Plusieurs séances visent le même objectif ; partagé, il permet de prouver que le programme couvre le référentiel GSE. → [05](05-schemas-mot-objectif-media-programme.md)

**Q. Pourquoi une fiche média avec licence ?**
R. Pour garder la trace des droits. Un média non autorisé est refusé en publication pour vrais enfants. → [05](05-schemas-mot-objectif-media-programme.md)

## Une séance

**Q. Les 7 étapes d'une séance ?**
R. Bonjour, chanson, révision, les 4 mots (montrer + répéter), petits jeux (toucher), rattrapages, au revoir. → [04](04-schema-seance.md)

**Q. Les 8 types d'activités ?**
R. greeting, present, repeat, touch, visual_description, review, sing_with_me, watch_video. 6 proposés en plus : match_pairs, dialogue, find_in_scene, memory, trace, build_word. → [06](06-activites.md)

**Q. Comment marchent les rattrapages ?**
R. Exercice raté après 3 essais → noté. Avant l'au revoir, le moteur rejoue une version plus facile (`retry_only`, 2 essais, 0 point). Tout réussi → pas de rattrapage. → [06](06-activites.md)

**Q. Comment sont choisis les mots de révision ?**
R. Par le moteur, pour chaque enfant : d'abord les mots ratés, puis ceux dont la boîte dit « à revoir aujourd'hui », puis les plus anciens. Jamais au hasard. → [08](08-revision-boites-et-rythme.md)

**Q. Les boîtes de Leitner ?**
R. 5 boîtes par enfant. Réussi = boîte suivante, raté = boîte 1. Retour après 1, 2, 4, 7, 14 jours. → [08](08-revision-boites-et-rythme.md)

**Q. Le rythme conseillé ?**
R. 3 séances par semaine, maximum 1 nouvelle par jour, jeu libre entre les séances, limite de temps par jour réglée par le parent (20 min). → [08](08-revision-boites-et-rythme.md)

**Q. Le mode « jouer avec Pixo » ?**
R. Proposition : entre les séances, jeux et révisions avec les mots déjà vus seulement. Compte dans la limite de temps, ne débloque pas de séance. → [06](06-activites.md)

## L'avenir

**Q. Et si on ajoute les maths ?**
R. Même modèle : champ `subject`, nouveaux types d'activités, items `n_3` à côté des mots. Côté progression, « item » au lieu de « mot ». Rien à reconstruire. → [05](05-schemas-mot-objectif-media-programme.md)

**Q. Quel éditeur de contenu ?**
R. Pas encore choisi : Directus (gratuit, se branche sur Supabase) ou le Lesson Manager (idée). Proposition : un test Directus d'une demi-journée. En attendant, JSON à la main + outil de vérification. → [01](01-vue-d-ensemble.md)

**Q. Qu'est-ce qui reste à caler avec Viven et Montassar ?**
R. Qui choisit les mots de révision, le modèle de score, l'échec d'un rattrapage, « My name's {name} », les animations, le mélange des images. → [06](06-activites.md)

**Q. Qu'est-ce qui n'est pas prêt ?**
R. 12 images de l'unité 1 à produire ; chanson et images actuelles en test seulement (licences) ; base pas encore installée dans Supabase. → [11](11-medias-a-produire.md), [09](09-base-de-donnees.md)
