# Corrections géographiques et préparation de la validation

État de préparation conservé pour l'historique. **Mise à jour :** les trois
comparaisons et les deux entraînements finaux ont depuis été autorisés et
exécutés, puis le lot réservé évalué après gel. Consulter le
[rapport final](modeles_finaux_2026-10-29.md) pour les résultats et artefacts à utiliser.

Travail local uniquement, sans entraînement, téléchargement de données,
développement de l'application ou push.

## Données et sauvegarde

Le CSV antérieur est conservé octet pour octet dans :

`output/backups/cleaned_data_4ac7b5d2b0a4f3ba.csv`

Son SHA-256 est
`4ac7b5d2b0a4f3ba7ff936d28c348512fcbf368391d8008dded0240a7b1ffc24`.
Le CSV corrigé reste `output/cleaned_data.csv`, avec le SHA-256
`e99209359b823f107ae2023a3ab300b6f052cfd71cb484ebbf84415e6d3b8be7`.
Les deux versions ont 616 057 lignes et 16 colonnes, dans le même ordre.

Seule l'altitude change :

| Communes concernées | Logements | Avant | Après |
|---|---:|---:|---:|
| Arrondissements de Lyon, codes 69381 à 69389 | 2 091 | 383,93 m | 237 m |
| Pierre-Bénite, code 69152 | 12 | 383,93 m | 194 m |

Ces règles proviennent du notebook de Nouhayla : 69381–69389 sont utilisés
comme 69123 uniquement pour la jointure, et 69152 comme 69149. Les codes
originaux des logements ne sont pas remplacés. Le fichier de communes local
contient les altitudes cibles. Les zones H1/H2/H3 sont inchangées : aucune
sous-zone n'est déduite ou inventée sans `data/climate_zones.csv`.

La jointure impose une référence communale sans clé manquante ni dupliquée,
une relation n:1 et la conservation du nombre/ordre des logements. Le repli
sur la moyenne départementale est conservé pour les autres communes non trouvées.
Les tests rejettent également une référence dupliquée ou privée de Lyon.
L'égalité des quinze autres colonnes a été vérifiée.

Le calcul est intégré dans le notebook 1 ; la nouvelle exportation a été
produite depuis les fichiers bruts locaux. La traçabilité est séparée dans
`output/cleaned_data_metadata.csv`, alignée par `cleaned_row`, avec la source,
le numéro de ligne brute, les numéros DPE, les dates et identifiants BAN/immeuble.
Aucune de ces colonnes n'entre dans les sept caractéristiques ML.
Le manifeste `output/preparation_manifest.json` contient les empreintes des
données, métadonnées et sources. Ces fichiers locaux sont ignorés par Git.

Contrôles exécutés : reproduction du notebook de préparation sans écriture
après migration, contrôle indépendant des 2 103 changements d'altitude et des
quinze colonnes inchangées, tests des jointures invalides, tests transitifs des
groupes, vérification de la chronologie et de l'absence de chevauchement des
identifiants entre partitions, reproduction des deux notebooks ML historiques
avec réseau/entraînement/sauvegarde de modèles interdits, compilation et
`git diff --check`. Les dépendances verrouillées restent compatibles.

## Audit des dates et identifiants bruts

834 959 lignes : 470 000 dans l'existant et 364 959 dans le neuf.

- `numero_dpe` : aucun absent, aucun doublon, aucun numéro commun aux deux sources.
- `date_reception_dpe` et `date_etablissement_dpe` : aucune absente ou illisible.
- Réceptions du 1er juillet 2021 au 19 octobre 2026 ; aucune future au jour de l'audit.
- 89 dates d'établissement sont postérieures à la réception. Parmi les lignes
  nettoyées, 79 sont concernées et mises à l'écart du protocole proposé.
- Deux dates de visite sont illisibles ; cette date n'est pas la clé de séparation.
- 2 812 identifiants BAN manquent dans les bruts. Les adresses répétées sont
  nombreuses : le numéro DPE unique ne garantit pas un bâtiment distinct.
- L'identifiant DPE d'immeuble associé est absent sur 701 091 lignes ; il ne
  suffit donc pas, à lui seul, à grouper tout le jeu.
- Deux liens de remplacement désignent un numéro DPE présent dans les bruts.
- 151 893 réceptions sont concentrées en janvier 2026. Ce pic impose de vérifier
  la distribution temporelle ; aucune cause n'est supposée ici.

Le détail agrégé est dans `output/raw_metadata_audit.json`. Les identifiants
individuels restent dans les fichiers locaux, pas dans ce rapport.

## Séparation proposée, sans scores sur le lot réservé

Les limites calendaires sont fixées sans optimisation sur les étiquettes :

| Partition | Réception | Lignes retenues |
|---|---|---:|
| Entraînement | Avant 2024 | 398 445 |
| Validation | Année 2024 | 55 235 |
| Lot réservé interne | À partir de 2025 | 107 666 |

Les adresses BAN, DPE d'immeubles associés et liens de remplacement sont reliés
transitivement. Un groupe qui apparaît dans plusieurs périodes est écarté
du protocole ; on ne déplace pas de ligne future dans l'entraînement.
Les dates incohérentes et les groupes sans référence BAN/immeuble sont également
écartés. Cela représente 54 711 lignes : 79 dates incohérentes, 2 597 lignes sans
groupe géographique identifié et 52 035 dans des groupes traversant les périodes.
Ces lignes restent dans le CSV ; elles ne sont pas supprimées.

Les contrôles vérifient l'absence de groupe ou identifiant partagé et l'ordre
chronologique entre partitions. Les affectations sont conservées dans
`output/classification_split.csv`. Les cibles du lot réservé ne sont ni
résumées par classe, ni utilisées pour choisir les paramètres ou calculer un score.

Ce protocole est plus exigeant que le découpage aléatoire, mais reste **interne** :
les données avaient déjà été exploitées. Il ne constitue pas un test externe neuf.
Les filtres IQR et regroupements d'énergies de la préparation historique ont
encore été calculés globalement. Pour une évaluation stricte de toute la chaîne,
il faudra les apprendre sur l'entraînement seulement et conserver les autres
partitions sans filtrage opportuniste à partir de leurs cibles/coûts.

BAN décrit une adresse, pas toujours un bâtiment physique ; certains liens via
des lignes brutes éliminées peuvent aussi manquer. Les regroupements rendent
la séparation plus prudente sans garantir l'identification exhaustive des bâtiments.

## Comparaison de classification préparée, non lancée

Ampleur prévue : **3 entraînements, 100 arbres chacun, 2 threads**, sur le même
échantillon stratifié de **60 000 lignes de l'entraînement**, graine 42.
Évaluation sur les **55 235 lignes de validation**, sans entraînement sur elles.
Il n'y a ni grille exhaustive ni validation croisée supplémentaire.

1. Random Forest profondeur 10, pondération balanced : contrôle proche du modèle actuel.
2. Random Forest profondeur 20, pondération balanced : effet d'une capacité supérieure.
3. Random Forest profondeur 20, sans pondération : effet de la pondération à capacité égale.

Les autres paramètres restent fixes : min_samples_split=20, min_samples_leaf=1.
Le critère de choix est le F1 macro des sept classes sur validation. À 0,001 près,
le premier candidat déclaré est préféré. Une référence « classe majoritaire »
est calculée depuis l'échantillon d'entraînement. Les rapports par classe et
par source neuf/existant sont prévus sur validation.

La validation est composée de 50 648 logements neufs et 4 587 existants :
environ 91,7 % de neuf, contre 38,9 % dans l'entraînement complet.
Elle ne contient que 172 F et 53 G. Un gain de F1 sur ces classes sera donc
fragile ; il faudra regarder les effectifs et le changement de population,
sans retoucher le lot réservé pour obtenir un résultat plus favorable.

Le script fonctionne en préparation seule par défaut :

```powershell
.\.venv-ml\Scripts\python.exe scripts/compare_classification.py
```

L'option `--run` est la seule qui lance les trois entraînements. Elle n'a pas
été exécutée. Elle écrira un rapport horodaté dans
`output/classification_comparisons/`, sans remplacer les modèles existants
et sans évaluer le lot réservé. Aucun réentraînement final automatique n'est prévu.

## Anciens modèles et régression

Les modèles existants sont inchangés. Leurs scores de régression
(MAE 2 121,45 ; RMSE 3 954,70 ; R² 0,6932) et de classification
(accuracy 0,5796 ; F1 macro 0,4759) concernent **la sauvegarde antérieure**.
Ils ne doivent pas être attribués au CSV corrigé.
`MLmodels/data_reference.json` rattache les anciens modèles à cette sauvegarde.
Les notebooks chargent cette référence historique par défaut et l'indiquent.

La même séparation chronologique/par groupes peut servir à une comparaison
limitée ultérieure de régression. Aucune n'est lancée ici. Pour un test externe
du pipeline figé, il faudra des diagnostics jamais exploités, postérieurs au
19 octobre 2026 et contrôlés contre les anciens numéros, remplacements et groupes.
