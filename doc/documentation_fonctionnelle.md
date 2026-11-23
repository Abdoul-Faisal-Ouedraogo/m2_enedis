# Documentation fonctionnelle — App Énergie France

*Application d'analyse des DPE et de prédiction de la consommation énergétique des logements*


## 1. Objectif et public cible

**Énergie France** est une application web interactive dédiée à l'analyse et à l'estimation de la performance énergétique des logements en France. Elle exploite des données issues des diagnostics de performance énergétique (DPE) afin de visualiser les caractéristiques du parc immobilier, d'identifier les tendances de consommation et de comparer différents types de bâtiments.

L'application permet également d'estimer la consommation énergétique et la classe DPE d'un logement à partir de ses caractéristiques. Elle s'adresse aux particuliers, étudiants et utilisateurs souhaitant explorer les données énergétiques et mieux comprendre les facteurs associés à la performance des logements. Les estimations sont indicatives et ne remplacent pas un diagnostic réglementaire.


## 2. Navigation et fonctionnalités

L'application propose une interface interactive organisée en six rubriques, accessibles depuis le menu latéral.

### Accueil
Présente l'objectif de l'application, les principales données disponibles et trois parcours : **Explorer**, **Situer** et **Estimer**. Un tableau de bord synthétique affiche le nombre de logements étudiés et leur couverture géographique.

### Contexte
Permet d'analyser les données DPE à travers des filtres combinables : département, classe énergétique, type de bâtiment et énergie de chauffage. Quatre indicateurs résument les logements sélectionnés : effectif, surface moyenne, consommation moyenne et proportion de classes F et G.

Les visualisations comprennent la répartition des classes DPE, un histogramme des consommations, des boîtes à moustaches présentant leur dispersion selon la classe énergétique et un nuage de points mettant en relation la surface habitable et la consommation. Un graphique comparatif présente également la distribution des classes énergétiques pour les appartements, immeubles et maisons. Les graphiques peuvent être exportés au format PNG et les données sélectionnées au format CSV.

### Cartographie des logements
Cette rubrique permet de visualiser les logements sur une carte interactive, avec des marqueurs colorés selon leur classe DPE (A à G). L'utilisateur peut appliquer des filtres, zoomer, consulter les informations des logements et ajuster le nombre de marqueurs affichés pour faciliter l'exploration.

### Prédiction énergétique
Permet d'estimer la performance d'un logement à partir de sa localisation, sa surface habitable, son année de construction, son énergie de chauffage, son type de bâtiment, son altitude et sa zone climatique.

L'utilisateur lance le calcul avec **« Calculer les estimations »**. Un second mode permet de comparer deux logements selon leurs caractéristiques.

### Interprétation IA des résultats
Rubrique destinée à faciliter la compréhension des estimations énergétiques grâce à des explications générées par intelligence artificielle, lorsque ce service est disponible.

### Gestion des données et modèles
Permet de préparer de nouvelles versions des données, de les valider et de gérer leur activation. La rubrique propose également le réentraînement et la gestion des versions des modèles, avec des confirmations pour certaines opérations.

## 3. Parcours utilisateur type

1. **Découvrir l'application :** consulter la page Accueil pour comprendre les objectifs et les données disponibles.
2. **Explorer les logements :** accéder à Contexte, sélectionner un département ou une classe DPE, puis analyser les indicateurs et graphiques. Exporter les résultats si nécessaire.
3. **Estimer une performance énergétique :** ouvrir Prédiction énergétique, renseigner les caractéristiques du logement et lancer le calcul.
4. **Comparer des profils :** utiliser le mode de comparaison pour étudier les différences entre deux logements.
5. **Comprendre les résultats :** consulter les explications de la rubrique Interprétation IA lorsqu'elles sont disponibles.

## 4. Conditions d'utilisation et limites

La fiabilité des résultats dépend de la qualité des données disponibles et des caractéristiques renseignées par l'utilisateur. Les indicateurs et visualisations évoluent selon les filtres appliqués, tandis que certaines valeurs extrêmes peuvent être masquées dans les graphiques pour améliorer leur lisibilité.

Les prédictions reposent sur des modèles statistiques entraînés à partir de données historiques. Elles représentent des estimations et ne constituent ni une certification énergétique officielle ni un remplacement du DPE réglementaire. Les fonctionnalités d'intelligence artificielle peuvent également dépendre de la disponibilité des services associés.

