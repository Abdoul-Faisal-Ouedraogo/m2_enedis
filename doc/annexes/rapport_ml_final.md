# Rapport ML final - Périmètre et données

Projet Habitat & énergie, 30 octobre 2026. Ce rapport décrit les modèles réels
de référence `final_geo_v1`, et distingue les fonctions Expert ajoutées des
entraînements de test. Sources : manifestes et résultats enregistrés dans le
dépôt, rapport de préparation et audit des partitions. Aucun score expérimental
nouveau n'est présenté comme une performance obtenue sur les données complètes.

## Deux objectifs distincts

La régression estime `conso_5_usages_ef`, énergie finale annuelle totale des cinq
usages en kWh/an. La classification prédit directement la lettre DPE A-G.
La lettre n'est jamais déduite de la consommation de la régression : les notions
réglementaires de DPE ne se réduisent pas à cette consommation finale totale.
Une estimation n'est ni un diagnostic réglementaire ni une facture.

## Population disponible

Le CSV préparé contient 616 057 logements et 94 départements renseignés.
Il provient des extractions ADEME de logements existants et neufs. Les requêtes
historiques étaient plafonnées à 5 000 lignes par département et par source,
sans tirage temporel représentatif : ce n'est pas un recensement du parc français.
La composition change entre périodes ; les scores globaux dépendent de ce mélange.

Les sept entrées sont surface habitable, nombre de niveaux, âge du bâtiment,
altitude moyenne, énergie principale de chauffage, type de bâtiment et zone
climatique. Les coûts, consommations détaillées, étiquettes et identifiants ne
sont pas des variables d'entrée. Coût et consommation ne doivent pas servir
indirectement de substituts de la cible dans le formulaire.

## Préparation et géographie

L'âge est fixé à la référence 2026 ; les logements neufs ont reçu un âge nul par
imputation. Les règles IQR de coût et surface limitent les valeurs extrêmes,
les niveaux admissibles vont de 1 à 10 dans la préparation, et les énergies
secondaires sont regroupées sous Autre. Ces transformations limitent le domaine
auquel les modèles peuvent être raisonnablement appliqués.

L'altitude est rapprochée du référentiel communes-france-2025. Les codes de Lyon
et Pierre-Bénite sont corrigés sur une clé de jointure séparée. Sans correspondance
communale, la moyenne départementale des communes sert de remplacement. Les zones
H1/H2/H3 du notebook sont conservées, sans inventer des sous-zones. Les identifiants
et dates sont conservés séparément pour la traçabilité, sans entrer dans les modèles.

<!-- pagebreak -->
# Protocole et sélection

## Séparation temporelle et groupes

Les réceptions avant 2024 forment l'entraînement ; celles de 2024, la validation ;
celles depuis 2025, le lot réservé. Des composantes connexes rapprochent adresse
BAN, immeuble associé et diagnostic remplacé. Les groupes qui traversent les
périodes sont exclus plutôt que répartis des deux côtés. Une adresse BAN n'est
toutefois pas une identité physique parfaite d'un bâtiment.

| Partition | Lignes | Part du neuf |
|---|---|---|
| Entraînement | 398 445 | 38,91 % |
| Validation | 55 235 | 91,70 % |
| Réservé | 107 666 | 46,75 % |
| Exclues du protocole | 54 711 | 76,81 % |

La validation est fortement dominée par le neuf. L'audit montre déjà une part
de neuf élevée dans les bruts de 2024 : 79 257 contre 6 265 existants. Le protocole
révèle surtout une extraction hétérogène ; aucune explication réglementaire du
pic observé ne peut être inférée de ces seules données.

## Comparaison sur la validation uniquement

Trois forêts de classification ont été comparées sur au plus 60 000 lignes
d'entraînement. Cent arbres, graine 42 et deux threads. Le F1 macro sur les
sept classes est le critère fixé ; une tolérance de 0,001 départage les candidats
dans l'ordre déclaré. Le lot réservé n'a pas servi à choisir les réglages.

| Candidat | DPE corrects | F1 macro A-G |
|---|---|---|
| Profondeur 10, pondéré | 74,66 % | 0,4508 |
| Profondeur 20, pondéré | 74,70 % | 0,4426 |
| Profondeur 20, non pondéré | 76,05 % | 0,4307 |

Le candidat de profondeur 10 pondéré est retenu selon le F1 macro, malgré la
meilleure accuracy du candidat non pondéré. Prédire systématiquement C donne
30,92 % de DPE corrects et un F1 macro de 0,0675 en validation.

Après sélection, les deux forêts finales sont ajustées sur entraînement et
validation, soit 453 680 lignes. La régression conserve les réglages déjà retenus :
100 arbres, profondeur 10, minimum de séparation 20, feuille minimale 1.
Les choix, empreintes et modèles sont sauvegardés avant l'évaluation réservée.

<!-- pagebreak -->
# Résultats réels du lot réservé

Ce lot de 107 666 logements est interne à des données historiquement exploitées.
Il ne constitue pas une validation externe indépendante. Les résultats ont été
vérifiés depuis les prédictions sauvegardées, sans nouvelle prédiction sur ce lot.

| Indicateur global | Modèle final | Référence constante |
|---|---|---|
| DPE corrects | 55,41 % | 36,72 % (toujours C) |
| F1 macro A-G | 0,4031 | 0,0767 |
| MAE consommation | 1 814,68 kWh/an | 3 505,67 kWh/an |
| RMSE consommation | 2 957,21 kWh/an | 5 142,88 kWh/an |
| R² consommation | 0,6531 | -0,0493 |

La référence de régression est la médiane d'entraînement et validation,
4 754 kWh/an. Les modèles améliorent ces références simples, sans atteindre
une précision suffisante pour un usage réglementaire ou une décision isolée.

## Écarts entre existant et neuf

| Population | Lignes | DPE corrects | MAE kWh/an |
|---|---|---|---|
| Existant | 57 331 | 38,70 % | 2 802,29 |
| Neuf | 50 335 | 74,43 % | 689,82 |

Le F1 macro vaut 0,3126 sur l'existant et 0,3046 sur le neuf. Une bonne accuracy
du neuf n'assure pas un bon F1 macro : certaines classes y sont très rares ou
absentes, alors que le calcul conserve les sept classes fixes. L'erreur moyenne
du neuf, beaucoup plus basse, masque les difficultés des logements existants.

Le R² de régression est 0,4673 sur l'existant et 0,5024 sur le neuf. Les RMSE
correspondantes sont 3 934,16 et 1 037,68 kWh/an. La dispersion des erreurs reste
significative même lorsque l'erreur moyenne globale paraît acceptable.

## Interprétation pour une estimation

La MAE est une moyenne de groupe, pas un intervalle de confiance individuel.
Le modèle ne fournit pas d'intervalle calibré. Afficher une prévision suivie de
« plus ou moins la MAE » donnerait une garantie statistique qui n'a pas été établie.
L'interface et les PDF rappellent cette limite et distinguent explicitement
consommation finale annuelle, lettre de classification et unités.

<!-- pagebreak -->
# Classes F/G et limites méthodologiques

## Classification par classe sur le réservé

| Classe | Effectif | Précision | Rappel | F1 |
|---|---|---|---|---|
| A | 29 227 | 93,99 % | 74,59 % | 83,18 % |
| B | 13 666 | 39,42 % | 54,20 % | 45,64 % |
| C | 39 536 | 80,36 % | 47,34 % | 59,58 % |
| D | 16 846 | 35,63 % | 54,14 % | 42,98 % |
| E | 6 334 | 24,94 % | 31,32 % | 27,77 % |
| F | 1 590 | 8,77 % | 20,82 % | 12,34 % |
| G | 467 | 5,82 % | 63,17 % | 10,66 % |

Le rappel de G relativement élevé ne doit pas masquer sa précision très faible :
beaucoup de logements prédits G ne le sont pas réellement. F et G sont peu
représentés ; la performance sur les logements anciens reste modeste. Dans le neuf,
une seule ligne F et aucune G dans le réservé interdisent toute conclusion solide
sur ces classes. La classe sert à décrire les erreurs, jamais d'entrée du modèle.

| DPE observé | MAE kWh/an | RMSE kWh/an |
|---|---|---|
| A | 829,52 | 1 423,45 |
| C | 2 143,48 | 3 283,93 |
| F | 4 264,70 | 5 563,18 |
| G | 6 668,23 | 9 114,94 |

## Portée des conclusions

- Les filtres IQR et regroupements ont été calculés globalement avant séparation.
  Ce protocole ne valide donc pas toute la préparation brute sans fuite.
- L'imputation d'un âge nul au neuf, les caractéristiques limitées et l'absence de
  description fine de l'enveloppe ou des équipements expliquent une part des limites.
- Les liens transitifs via des lignes éliminées peuvent manquer dans les groupes.
  BAN n'est pas un identifiant physique complet de bâtiment.
- Les populations temporelles diffèrent fortement ; les scores aléatoires historiques
  ne se comparent pas directement aux scores temporels finaux.

Ces résultats sont adaptés à une démonstration d'exploration et de versionnement,
avec avertissements. Une évaluation externe, géographique et temporelle, et une
préparation ajustée sur le seul entraînement restent nécessaires avant un usage
plus exigeant. Aucun score ne justifie une décision de rénovation à lui seul.

<!-- pagebreak -->
# Reproductibilité et prolongements Expert

## Artefacts et vérification

Les modèles `classification.joblib` et `regression.joblib`, leurs contrats de
variables, le protocole figé, les résultats, le plan et la fixture de rechargement
sont conservés dans `MLmodels/final_geo_v1`. Le manifeste désigne cette référence.
Les empreintes relient données, métadonnées, partitions, modèles et résultats.
Le rechargement reproduit les exemples de développement ; les métriques réservées
sont recalculées à partir des prédictions déjà figées.

```powershell
.\.venv-app\Scripts\python.exe scripts/verify_final_models.py
.\.venv-app\Scripts\python.exe -X utf8 scripts/verify_app.py
```

Les notebooks et anciens modèles restent conservés. Les environnements ML et
application sont distincts. Les versions de bibliothèques, paramètres, graines et
limites de ressources sont enregistrés ; aucune recherche supplémentaire n'a suivi
l'évaluation réservée de la référence.

## Nouveaux parcours, sans prétendre à de nouveaux scores globaux

La collecte Expert est volontaire et bornée par département, réception et volume.
Elle prépare une copie avec bilan des rejets, doublons et remplacements. L'activation
nécessite validation explicite. L'aide géographique utilise les communes, pas une
moyenne des seuls logements. Le nettoyage incrémental utilise maintenant un profil
IQR figé à partir des sources initiales et sauvegarde les motifs de rejet. Cette
stabilité ne corrige pas la limite du nettoyage global avant séparation. L'audit
du lot réel Rhône attribue ses 15 rejets à des champs manquants, sans rejet IQR.

Le réentraînement reprend les coupures 2024/2025, les groupes et les réglages finaux
figés. Les réceptions récentes depuis 2025 restent donc réservées, non apprises.
Deux forêts sont ajustées sur train+validation, puis évaluées sans modifier les
réglages. Les versions ne remplacent pas automatiquement les modèles actifs ; une
activation compatible et un retour arrière sont proposés. Streamlit et l'API locale
partagent le chargeur et les mêmes règles, avec invalidation des résultats périmés.

## Ce qui a été exécuté et ce qui reste ouvert

Les tests d'apprentissage utilisent seulement 36 lignes et deux arbres par forêt,
dans des dossiers temporaires. Ils ne produisent pas de score de projet et ne
remplacent aucun modèle final. Les tests réseau sont simulés ; seules les métadonnées
officielles ont été consultées, sans collecte de diagnostics. Une requête locale
réelle à l'API a renvoyé 9 101 kWh/an et D pour l'exemple fourni, avec version.

Docker a été construit et testé : deux services sains, pages et prédiction vérifiées
dans l'image. Les ports nominaux occupés ont été préservés ; les essais ont utilisé
18501/18000 en local. Les guides Markdown sont rendus pour contrôler leur pagination.
Le petit écran et la page Exploration après refonte restent non confirmés
visuellement, ainsi que le dernier cadrage/maintien du zoom en navigateur. Le sujet
complet n'étant pas présent, la conformité formelle exhaustive reste à contrôler.
La vidéo est scénarisée, pas enregistrée ni publiée. Aucun déploiement n'est réalisé.
