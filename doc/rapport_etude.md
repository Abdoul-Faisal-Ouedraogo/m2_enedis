# Rapport d’étude - Habitat & énergie

**Projet Python / Machine Learning - Master 2 SISE**  
**Équipe :** Nouhayla BOUAOUICH, Abdoul Faisal OUEDRAOGO, Mounir BEKKAR  
**Date :** 20/11/2026  
**Application :** Énergie France - Analyse et prédiction énergétique des logements

## 1. Contexte, problématique et objectifs

La performance énergétique des logements est un sujet important pour comprendre les consommations et repérer les bâtiments les plus énergivores. Dans ce projet, nous avons exploité les diagnostics de performance énergétique (DPE) diffusés par l’ADEME pour répondre à deux questions : comment analyser les caractéristiques énergétiques des logements à partir des données disponibles, et jusqu’où peut-on estimer leur consommation et leur classe DPE avec un nombre limité de caractéristiques ?

Notre application *Énergie France* réunit une exploration statistique, une carte des logements et deux modèles de machine learning. Le premier estime la consommation finale annuelle des cinq usages, en kWh/an ; le second prédit directement la classe DPE, de A à G. Il s’agit de deux prédictions distinctes : la classe DPE n’est pas calculée à partir de la consommation estimée. L’outil est destiné à l’analyse et à la démonstration ; il ne remplace pas un diagnostic réglementaire.

## 2. Données, préparation et indicateurs

### 2.1 Sources et périmètre

Les données proviennent des jeux ADEME concernant les DPE des logements existants et neufs. Après préparation, le fichier utilisé par l’application contient **616 057 logements**, **16 colonnes** et des informations pour **94 départements**. Les métadonnées nécessaires à la traçabilité, notamment les identifiants et les dates, sont conservées dans un fichier séparé et ne sont pas utilisées comme variables de prédiction.

Un référentiel communal complète les données géographiques, notamment pour l’altitude. La seconde version des modèles utilise également des températures obtenues à partir d’Open-Meteo sur la période 2015–2024.

L’extraction initiale était limitée à 5 000 lignes par département et par source. Le jeu obtenu ne constitue donc pas un échantillon représentatif de l’ensemble du parc de logements français. Cette limite doit être prise en compte dans l’interprétation des graphiques comme des performances des modèles.

### 2.2 Préparation des données

La préparation a consisté à sélectionner les champs utiles, harmoniser certaines catégories, compléter les informations géographiques et traiter les valeurs qui ne respectaient pas les règles retenues. Des bornes de nettoyage fondées sur l’écart interquartile (IQR) ont notamment été appliquées à la surface et au coût. Les catégories d’énergie de chauffage peu fréquentes ont été regroupées, et l’âge des bâtiments est calculé avec **2026 comme année de référence**. Pour les logements neufs, l’âge a été fixé à zéro lorsque cette information devait être imputée.

La séparation entre les caractéristiques utilisées par les modèles et les métadonnées de suivi permet d’éviter d’introduire directement des identifiants ou des dates de traçabilité parmi les variables explicatives. Certaines opérations de préparation ayant été effectuées avant le découpage des jeux, le protocole ne garantit toutefois pas l’absence de toute fuite d’information en amont de l’entraînement.

### 2.3 Indicateurs d’exploration

| Indicateur | Valeur | Signification |
|---|---:|---|
| Logements préparés | **616 057** | Nombre d’enregistrements disponibles après préparation |
| Départements couverts | **94** | Couverture géographique du fichier |
| Surface moyenne sans filtre | **74,6 m²** | Surface moyenne affichée dans l’interface |
| Consommation moyenne sans filtre | **7 119 kWh/an** | Moyenne descriptive des consommations enregistrées |
| Part des classes F et G sans filtre | **6,3 %** | Part des logements les moins bien classés dans le jeu affiché |

Les trois derniers indicateurs correspondent à l’affichage de l’application sans filtre restrictif ; ils peuvent varier selon les filtres et la version des données activée. L’interface permet également d’étudier la répartition des classes DPE, la distribution des consommations, leur dispersion selon les classes et le lien entre surface habitable et consommation. Une comparaison des classes énergétiques par type de bâtiment complète ces visualisations.

## 3. Méthodologie de machine learning

### 3.1 Variables et objectifs de prédiction

La première version, **`final_geo_v1`**, utilise sept variables : la surface habitable, le nombre de niveaux, l’âge du bâtiment, l’altitude moyenne, l’énergie principale de chauffage, le type de bâtiment et la zone climatique (H1, H2 ou H3).

La seconde version, **`final_geo_v2_temperature`**, reprend ces sept variables et ajoute la température moyenne annuelle ainsi que la température moyenne hivernale. L’objectif était d’examiner si ces informations climatiques amélioraient les estimations.

Deux cibles sont étudiées séparément : **`conso_5_usages_ef`** pour la consommation finale annuelle et **`etiquette_dpe`** pour la classe énergétique. Les variables qui correspondent aux résultats à prédire ne sont pas réutilisées comme entrées des modèles.

### 3.2 Algorithmes et choix des paramètres

Nous avons retenu deux modèles **Random Forest** de scikit-learn : un régresseur pour la consommation et un classifieur pour les classes A à G. Les modèles finaux documentés utilisent 100 arbres, une profondeur maximale de 10 et une graine aléatoire fixée à 42. Ce choix permet de disposer d’une méthode capable de traiter à la fois des caractéristiques numériques et catégorielles après préparation.

Pour la classification, trois variantes ont été comparées sur le jeu de validation. Le modèle **`rf_depth10_balanced`** a été choisi à partir du **F1 macro**, plutôt que de la seule proportion de prédictions correctes. Ce critère donne une place à chacune des sept classes et évite de juger le modèle uniquement sur les classes les plus fréquentes.

### 3.3 Séparation des données et évaluation

Le protocole prend en compte la date de réception des diagnostics et des regroupements par adresse, immeuble associé et diagnostics remplacés, afin de limiter les recoupements entre les jeux. La séparation initiale est la suivante :

| Ensemble | Période de réception | Nombre de logements |
|---|---|---:|
| Entraînement | Avant 2024 | **398 445** |
| Validation | Année 2024 | **55 235** |
| Lot réservé | Depuis 2025 | **107 666** |
| Exclus du protocole | Dates, groupes ou autres contraintes du découpage | **54 711** |

Après comparaison des variantes sur la validation, les modèles retenus ont été **réentraînés sur les 453 680 logements réunissant l’entraînement initial et la validation** (398 445 + 55 235). Le lot de 107 666 logements a ensuite servi à l’évaluation finale et non au choix des paramètres. Il s’agit néanmoins d’un lot **interne aux données historiquement exploitées**, et non d’une validation externe indépendante.

Pour évaluer la classification, nous utilisons l’**accuracy** (proportion de classes correctement prédites) et le **F1 macro** (moyenne des scores F1 des sept classes). Pour la régression, nous retenons la **MAE** (erreur absolue moyenne), la **RMSE** (qui pénalise davantage les grandes erreurs) et le **R²** (qualité d’ajustement par rapport à une référence constante).

## 4. Résultats et comparaison des modèles

### 4.1 Performances globales

Les valeurs suivantes proviennent des fichiers `results.json` des deux versions et correspondent au **même lot réservé de 107 666 logements**.

| Version | Accuracy DPE | F1 macro | MAE (kWh/an) | RMSE (kWh/an) | R² |
|---|---:|---:|---:|---:|---:|
| `final_geo_v1` | **55,41 %** | **0,4031** | 1 814,68 | 2 957,21 | 0,6531 |
| `final_geo_v2_temperature` | 55,05 % | 0,4013 | **1 813,99** | **2 952,84** | **0,6541** |

Pour situer ces résultats, deux références simples ont été évaluées sur le même lot avec la version v1 : prédire systématiquement la classe **C** conduit à **36,72 %** de bonnes classifications, tandis que prédire une consommation constante égale à la médiane de référence donne une **MAE de 3 505,67 kWh/an**. Les modèles entraînés font donc mieux que ces stratégies élémentaires.

La **v1** obtient les meilleurs résultats en classification, avec 55,41 % de classes correctes contre 55,05 % pour la v2. À l’inverse, l’ajout des températures réduit très légèrement la MAE (de 1 814,68 à 1 813,99 kWh/an) et la RMSE (de 2 957,21 à 2 952,84 kWh/an). Le R² progresse de 0,6531 à 0,6541. Ces écarts sont faibles : les résultats ne permettent pas de conclure à une supériorité générale de la v2. Son intérêt dépend de l’objectif poursuivi et de la disponibilité des températures nécessaires à son utilisation.

### 4.2 Différences entre logements existants et neufs

L’analyse détaillée de la **v1** montre que les résultats globaux masquent des écarts importants entre les populations :

| Population du lot réservé | Logements | Accuracy DPE | MAE consommation |
|---|---:|---:|---:|
| Logements existants | **57 331** | **38,70 %** | **2 802,29 kWh/an** |
| Logements neufs | **50 335** | **74,43 %** | **689,82 kWh/an** |

La classification fonctionne nettement mieux sur les logements neufs que sur les logements existants. La régression présente également une erreur moyenne beaucoup plus élevée sur l’existant. Ces différences sont importantes pour l’utilisation de l’application : une performance moyenne calculée sur l’ensemble des logements ne décrit pas nécessairement la fiabilité de l’estimation pour un logement particulier.

Le **F1 macro** reste pourtant limité dans les deux groupes : **0,3126** pour l’existant et **0,3046** pour le neuf. L’accuracy plus élevée sur le neuf ne signifie donc pas que toutes les classes DPE y sont bien reconnues. Certaines classes sont rares ou absentes dans cette population.

Sur les logements existants, l'accuracy du modèle (38,70 %) reste même inférieure à celle d'une prédiction systématique de la classe C (45,68 %). Son F1 macro est toutefois supérieur, ce qui montre l'intérêt d'évaluer les différentes classes plutôt que de considérer uniquement le taux de bonnes prédictions.

### 4.3 Difficultés sur les classes énergétiques F et G

Les résultats par classe de la **v1** confirment une limite importante : sur le lot réservé, le score F1 est de **0,1234** pour la classe **F** et de **0,1066** pour la classe **G**. La précision atteint seulement **8,77 %** pour F et **5,82 %** pour G. Autrement dit, une grande partie des logements prédits dans ces classes n’appartient pas réellement à la classe annoncée.

Ces résultats imposent une interprétation prudente, en particulier lorsqu’il s’agit d’identifier des logements potentiellement très énergivores. La prédiction d’une classe ne peut pas être considérée comme une preuve de la performance énergétique réelle du bâtiment.

## 5. Interprétation, limites et pistes d’amélioration

Les deux versions montrent qu’il est possible d’extraire des tendances utiles à partir de caractéristiques relativement simples des logements. Toutefois, une accuracy proche de **55 %** signifie qu’environ 45 % des classes DPE du lot réservé ne sont pas correctement prédites. Le F1 macro voisin de **0,40** confirme que la qualité de classification est inégale selon les classes.

En régression, une MAE d’environ **1 814 kWh/an** représente une erreur absolue moyenne calculée sur le lot, et non une marge d’erreur garantie pour chaque estimation. Le modèle ne fournit pas d’intervalle de prédiction individuel calibré. De plus, les écarts entre logements neufs et existants montrent qu’une seule métrique globale ne suffit pas pour juger la fiabilité des résultats.

Plusieurs limites méthodologiques doivent être conservées à l’esprit. L’extraction ADEME est plafonnée et ne représente pas nécessairement le parc national. Les périodes de réception ont des compositions différentes, notamment en matière de logements neufs et existants. Les regroupements par adresse réduisent certains risques de recoupement sans identifier parfaitement chaque bâtiment physique. Enfin, certaines étapes de préparation ont été réalisées avant la séparation chronologique, ce qui ne permet pas d’exclure toute fuite d’information dans la chaîne initiale.

Pour aller plus loin, il serait pertinent de revoir la préparation afin d’ajuster les transformations uniquement sur l’entraînement, de tester les modèles sur un jeu externe et d’étudier plus précisément les erreurs par classe DPE et par type de logement. Une analyse de l’incertitude des estimations serait également utile avant d’envisager des usages plus exigeants. Ces pistes constituent des améliorations possibles ; elles ne sont pas présentées comme des validations déjà réalisées.

## 6. Bilan et conclusion

Le projet a permis de construire une application qui relie plusieurs étapes du travail sur les données : préparation, exploration, visualisation géographique, entraînement de modèles et consultation des prédictions. L’interface Streamlit facilite l’analyse des logements et la comparaison de leurs caractéristiques. L’API FastAPI, la gestion des versions et l’exécution locale avec Docker complètent le dispositif ; leur fonctionnement est décrit dans le rapport technique.

Les résultats obtenus sont encourageants par rapport aux références simples, mais ils montrent aussi les limites d’une estimation fondée sur un nombre restreint de variables. L’ajout des températures en v2 n’apporte qu’un gain marginal pour la consommation et ne permet pas d’améliorer la classification. Les différences entre logements neufs et existants, ainsi que les difficultés sur les classes F et G, restent les principaux points de vigilance.

L’intérêt de ce travail ne se limite donc pas aux scores : il réside aussi dans la construction d’une chaîne de traitement documentée et dans la possibilité d’examiner concrètement ce que les modèles peuvent — ou ne peuvent pas — déduire des données DPE. L’application constitue un support d’analyse et de démonstration, et non un outil de diagnostic réglementaire.

---

### Références internes

- **Documentation fonctionnelle** - navigation, fonctionnalités et parcours utilisateur (`documentation_fonctionnelle.md`).
- **Rapport technique** - architecture, préparation, modèles, API et Docker (`rapport_technique_final.md`).
- [Rapport ML détaillé](rapport_ml_final.md) - protocole, résultats par classe et limites.
- [Matrice des exigences](exigences_rendu.md) - exigences couvertes et vérifications restantes.
- [Résultats du modèle v1](../MLmodels/final_geo_v1/results.json) et [résultats du modèle v2](../MLmodels/final_geo_v2_temperature/results.json) - métriques utilisées dans ce rapport.
- [Plan de séparation des données](../MLmodels/final_geo_v1/split_plan.json) - effectifs et règles du protocole.
