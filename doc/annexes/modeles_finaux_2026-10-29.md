# Modèles finaux — 29 octobre 2026

Les cinq entraînements autorisés sont terminés : trois comparaisons de classification sur 60 000 lignes, puis deux modèles finaux sur 453 680 lignes. Chaque forêt contient 100 arbres. Les calculs sont limités à deux threads, sans grille ni recherche supplémentaire. Les anciens modèles et les travaux de Nouhayla sont conservés. Aucune application développée, aucun push.

## Population et protocole

| Partition | Lignes | Existant | Neuf | Part du neuf |
|---|---:|---:|---:|---:|
| train | 398 445 | 243 410 | 155 035 | 38,91 % |
| validation | 55 235 | 4 587 | 50 648 | 91,70 % |
| reserved | 107 666 | 57 331 | 50 335 | 46,75 % |
| excluded | 54 711 | 12 690 | 42 021 | 76,81 % |

| Partition | A | B | C | D | E | F | G |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 75 108 | 37 459 | 116 835 | 81 069 | 52 418 | 21 764 | 13 792 |
| validation | 26 067 | 9 491 | 17 081 | 1 643 | 728 | 172 | 53 |
| reserved | 29 227 | 13 666 | 39 536 | 16 846 | 6 334 | 1 590 | 467 |
| excluded | 25 767 | 7 390 | 14 484 | 4 200 | 2 034 | 558 | 278 |

Les réceptions avant 2024 servent à l'entraînement, celles de 2024 à la validation, celles depuis 2025 au lot réservé. Les groupes BAN/immeuble/remplacement traversant les périodes sont exclus du protocole, pas supprimés du CSV. Les partitions ne partagent ni groupe ni identifiant vérifié.

Pourquoi 91,7 % de neuf en validation ? Les bruts de 2024 contiennent déjà 79 257 DPE neufs contre 6 265 existants (92,7 % de neuf). Après nettoyage : 66 159 contre 5 082 (92,9 %). Après exclusions de groupes/dates : 50 648 contre 4 587 (91,7 %). Le découpage révèle donc surtout la composition temporelle différente des deux extractions. L'extraction historique demandait au maximum 5 000 lignes par département et par source, sans échantillonnage temporel représentatif. Ces taux ne décrivent pas le parc français. Aucune cause réglementaire du pic de janvier 2026 n'est supposée.

Les distributions des classes réservées ont été établies après le gel des choix. Elles n'ont pas orienté la comparaison. Les 172 F et 53 G de validation sont peu nombreux ; il faut interpréter leurs résultats avec prudence.

## Comparaison de classification — validation seulement

| Candidat | Accuracy | F1 macro A–G | Accuracy existant | F1 macro existant | Accuracy neuf | F1 macro neuf |
|---|---:|---:|---:|---:|---:|---:|
| rf_depth10_balanced | 74,66 % | 45,08 % | 33,49 % | 24,36 % | 78,39 % | 31,68 % |
| rf_depth20_balanced | 74,70 % | 44,26 % | 33,75 % | 24,79 % | 78,41 % | 31,43 % |
| rf_depth20_unweighted | 76,05 % | 43,07 % | 38,89 % | 23,25 % | 79,41 % | 30,96 % |

Référence de validation : toujours prédire C, classe majoritaire de l'échantillon d'entraînement. Accuracy 30,92 %, F1 macro 0,0675.

Choix figé : **rf_depth10_balanced**, selon le F1 macro global de validation. Les modèles plus profonds n'améliorent pas ce critère ; le gain d'accuracy du modèle non pondéré ne justifie pas de changer le critère après coup. À capacité égale, la pondération améliore le F1 macro global. Aucun résultat réservé n'a servi à ce choix.

Le F1 macro est calculé sur les sept classes fixes, même dans les sous-populations où certaines sont absentes ou très rares. Cela explique qu'une bonne accuracy du neuf ne corresponde pas forcément à un bon F1 macro.

### F1 par classe en validation

| Candidat / population | A | B | C | D | E | F | G |
|---|---:|---:|---:|---:|---:|---:|---:|
| rf_depth10_balanced / ensemble | 89,39 % | 54,28 % | 74,07 % | 43,10 % | 30,83 % | 14,51 % | 9,36 % |
| rf_depth10_balanced / existant | 22,50 % | 10,74 % | 37,47 % | 44,60 % | 30,86 % | 14,86 % | 9,45 % |
| rf_depth10_balanced / neuf | 89,50 % | 55,15 % | 77,13 % | 0,00 % | 0,00 % | 0,00 % | 0,00 % |
| rf_depth20_balanced / ensemble | 88,88 % | 52,66 % | 74,45 % | 40,33 % | 30,09 % | 12,44 % | 10,95 % |
| rf_depth20_balanced / existant | 24,69 % | 12,47 % | 39,72 % | 42,72 % | 30,12 % | 12,68 % | 11,13 % |
| rf_depth20_balanced / neuf | 88,98 % | 53,52 % | 77,48 % | 0,00 % | 0,00 % | 0,00 % | 0,00 % |
| rf_depth20_unweighted / ensemble | 89,30 % | 46,48 % | 76,70 % | 43,09 % | 31,05 % | 3,00 % | 11,86 % |
| rf_depth20_unweighted / existant | 26,51 % | 1,13 % | 43,00 % | 45,07 % | 31,09 % | 3,24 % | 12,73 % |
| rf_depth20_unweighted / neuf | 89,40 % | 47,45 % | 79,84 % | 0,00 % | 0,00 % | 0,00 % | 0,00 % |

Précision, rappel, F1 et effectif pour chaque candidat/classe/population sont conservés dans comparison_validation.json et affichés dans le notebook de classification.

## Modèles finaux et évaluation du lot réservé interne

Après sélection, la classification est réentraînée sur entraînement + validation (453 680 lignes). La régression utilise sans recherche supplémentaire les réglages précédemment retenus : 100 arbres, profondeur 10, min_samples_split=20, min_samples_leaf=1, graine 42. Les deux pipelines utilisent les mêmes sept caractéristiques et deux threads. Les coûts, consommations détaillées, DPE et identifiants sont exclus des entrées.

Les paramètres sont enregistrés dans frozen_protocol.json avant les entraînements finaux. Les modèles et leurs empreintes sont sauvegardés avant l'évaluation. Une seule paire de prédictions sur les 107 666 lignes réservées est produite, puis conservée. Aucune modification de paramètres ni aucun nouvel entraînement ne suit les résultats réservés.

**Ce lot reste interne à des données déjà exploitées. Ce n'est pas une évaluation externe indépendante.**

| Classification | Accuracy | F1 macro |
|---|---:|---:|
| Modèle final | 55,41 % | 0,4031 |
| Toujours C | 36,72 % | 0,0767 |

| Population réservée | Effectif | Accuracy DPE | F1 macro DPE | MAE kWh/an | RMSE kWh/an | R² |
|---|---:|---:|---:|---:|---:|---:|
| ensemble | 107 666 | 55,41 % | 0,4031 | 1 814,68 | 2 957,21 | 0,6531 |
| existant | 57 331 | 38,70 % | 0,3126 | 2 802,29 | 3 934,16 | 0,4673 |
| neuf | 50 335 | 74,43 % | 0,3046 | 689,82 | 1 037,68 | 0,5024 |

Référence de régression : médiane constante des données d'entraînement + validation (4 754,00 kWh/an), MAE 3 505,67, RMSE 5 142,88, R² -0,0493 sur le réservé.

### Classification réservée par classe et population

| Population | DPE | Effectif | Précision | Rappel | F1 |
|---|---|---:|---:|---:|---:|
| ensemble | A | 29 227 | 93,99 % | 74,59 % | 83,18 % |
| ensemble | B | 13 666 | 39,42 % | 54,20 % | 45,64 % |
| ensemble | C | 39 536 | 80,36 % | 47,34 % | 59,58 % |
| ensemble | D | 16 846 | 35,63 % | 54,14 % | 42,98 % |
| ensemble | E | 6 334 | 24,94 % | 31,32 % | 27,77 % |
| ensemble | F | 1 590 | 8,77 % | 20,82 % | 12,34 % |
| ensemble | G | 467 | 5,82 % | 63,17 % | 10,66 % |
| existant | A | 1 598 | 71,51 % | 39,74 % | 51,09 % |
| existant | B | 4 338 | 33,19 % | 22,06 % | 26,51 % |
| existant | C | 26 187 | 79,38 % | 33,86 % | 47,47 % |
| existant | D | 16 825 | 35,63 % | 54,21 % | 43,00 % |
| existant | E | 6 327 | 24,94 % | 31,36 % | 27,79 % |
| existant | F | 1 589 | 8,77 % | 20,83 % | 12,35 % |
| existant | G | 467 | 5,82 % | 63,17 % | 10,66 % |
| neuf | A | 27 629 | 94,89 % | 76,61 % | 84,77 % |
| neuf | B | 9 328 | 40,55 % | 69,15 % | 51,12 % |
| neuf | C | 13 349 | 81,26 % | 73,79 % | 77,35 % |
| neuf | D | 21 | 0,00 % | 0,00 % | 0,00 % |
| neuf | E | 7 | 0,00 % | 0,00 % | 0,00 % |
| neuf | F | 1 | 0,00 % | 0,00 % | 0,00 % |
| neuf | G | 0 | 0,00 % | 0,00 % | 0,00 % |

### Régression réservée par classe DPE observée

La classe DPE sert uniquement à décrire les erreurs, jamais de variable d'entrée.

| DPE réel | Effectif | MAE kWh/an | RMSE kWh/an | R² |
|---|---:|---:|---:|---:|
| A | 29 227 | 829,52 | 1 423,45 | -1,3609 |
| B | 13 666 | 1 952,84 | 3 402,26 | -2,7091 |
| C | 39 536 | 2 143,48 | 3 283,93 | -0,0962 |
| D | 16 846 | 1 956,20 | 2 708,08 | 0,7343 |
| E | 6 334 | 2 660,94 | 3 689,51 | 0,6755 |
| F | 1 590 | 4 264,70 | 5 563,18 | 0,4493 |
| G | 467 | 6 668,23 | 9 114,94 | 0,3388 |

## Artefacts et contrôles

Dans MLmodels/final_geo_v1/ : classification.joblib et regression.joblib ; classification_variables.json et regression_variables.json ; frozen_protocol.json ; split_plan.json ; comparison_validation.json ; results.json ; partition_distributions.json ; reload_check.json. MLmodels/final_models.json désigne cette version. Les anciens fichiers ne sont pas remplacés.

Les pipelines, leurs cibles, ordre des variables, paramètres, versions de bibliothèques et empreintes SHA-256 sont conservés. Le rechargement reproduit les prédictions sur 32 exemples d'entraînement/validation. Les prédictions réservées détaillées restent dans output/final_geo_v1/reserved_predictions.csv, ignoré par Git. Les vérifications suivantes recalculent seulement les métriques de ces prédictions figées, sans nouvel appel aux modèles sur le réservé.

Les deux notebooks courants affichent maintenant la version finale, sans entraînement. Leurs versions précédentes sont conservées intégralement dans archives/. Le notebook d'enrichissement de Nouhayla et les corrections intégrées dans la préparation sont conservés.

## Reproduire sans réentraîner

```powershell
.\.venv-ml\Scripts\python.exe scripts/verify_final_models.py
.\.venv-ml\Scripts\python.exe scripts/verify_notebooks.py
.\.venv-ml\Scripts\python.exe -m src.ml_workflow
```

Ces commandes contrôlent les artefacts et résultats sauvegardés, sans fit ni nouvelle prédiction réservée. La vérification complète demande les fichiers locaux CSV/métadonnées/affectations/prédictions dont les empreintes sont enregistrées. Le rechargement simple est disponible via src.final_model_loader.load_final_bundle().

## Reproduire les entraînements dans une copie de travail séparée

Conserver ce répertoire final et ses résultats. Dans une copie distincte du projet, installer requirements.txt dans .venv-ml et fournir les mêmes données corrigées, métadonnées et affectations. Le répertoire MLmodels/final_geo_v1 et le manifeste MLmodels/final_models.json ne doivent pas déjà exister dans cette copie de reproduction. Il n'est pas nécessaire de supprimer quoi que ce soit dans le projet original. Si nécessaire, régénérer le découpage avec prepare_classification_comparison.py ; son empreinte doit correspondre au split_plan.json conservé.

```powershell
.\.venv-ml\Scripts\python.exe scripts/compare_classification.py --run
# Utiliser le chemin exact du rapport horodaté affiché, sans choisir le meilleur parmi plusieurs relances.
.\.venv-ml\Scripts\python.exe scripts/train_final_models.py --comparison output/classification_comparisons/<rapport>.json --run
.\.venv-ml\Scripts\python.exe scripts/verify_final_models.py
```

Le programme refuse de remplacer une version finale existante ou de réévaluer un lot déjà terminé. Les graines sont fixées, les bibliothèques verrouillées et les entrées vérifiées par empreinte. Une nouvelle exécution dans une copie produit de nouveaux horodatages et durées, sans imposer que ces métadonnées soient identiques.

## Limites et état avant l'application

- Aucun blocage technique constaté pour charger les deux modèles et prédire avec les sept variables documentées.
- La classification est modeste, surtout dans l'existant et sur F/G. Le rappel de G est élevé mais sa précision très faible : nombreuses fausses alertes. Ce modèle pédagogique ne délivre pas un DPE réglementaire.
- La population change fortement entre entraînement, validation et réservé. Les scores globaux masquent des écarts neuf/existant.
- Les filtres IQR et regroupements d'énergies ont été calculés globalement avant la séparation ; ce protocole ne valide pas toute la chaîne brute sans fuite de préparation. Une préparation ajustée uniquement sur l'entraînement et une évaluation externe restent nécessaires.
- BAN est une adresse, pas une garantie d'identité physique du bâtiment. Des liens via les lignes éliminées peuvent manquer. Les logements neufs ont reçu un âge nul par imputation à 2026.
- L'échantillon ADEME local n'est pas représentatif du parc français. Les sous-zones climatiques n'ont pas été inventées et l'enrichissement Rhône complet reste non rejoué sans ses fichiers.
- Les anciens scores aléatoires ne se comparent pas directement aux scores présents : données, populations et découpage diffèrent.
- Aucun réglage supplémentaire n'est recherché après cette évaluation. Aucun développement de l'application n'a été effectué.
