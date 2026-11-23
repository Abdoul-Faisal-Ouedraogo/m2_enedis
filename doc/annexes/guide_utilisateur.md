# Habitat & énergie - Guide utilisateur

Application pédagogique locale, version Expert du 30 octobre 2026. Les estimations
ne remplacent pas un diagnostic DPE réglementaire. Les données et modèles
d'origine restent conservés. Aucune collecte ni aucun entraînement au démarrage.

## Installer et ouvrir sous Windows

Depuis la racine du dépôt, avec Python 3.13 et l'environnement application :

```powershell
uv pip install --python .venv-app/Scripts/python.exe -r requirements-app.txt
.\.venv-app\Scripts\python.exe -m streamlit run home.py --server.address 127.0.0.1
```

Ouvrir http://127.0.0.1:8501. Pour créer l'environnement s'il est absent :
`py -3.13 -m venv .venv-app`. Ne pas réinstaller les paquets dans l'environnement ML.
Arrêter avec Ctrl+C. Les fichiers locaux nécessaires sont le CSV préparé, ses
métadonnées et le référentiel communal, aux chemins indiqués dans le README.

## Explorer, situer, estimer

- Accueil : chiffres de l'étude, accès rapides, sources et crédits dépliables.
- Exploration : choisir département, classe DPE, bâtiment, chauffage et surface.
  Une liste vide signifie toutes les valeurs. Le bandeau rappelle les filtres ;
  la remise à zéro les efface. Le CSV exporte toute la sélection ; chaque graphique
  dispose de son PNG. Le tableau est limité à 500 lignes, le nuage à 5 000 points.
- Carte : coordonnées contrôlées, légende A-G, infobulles et effectifs représentés.
  Le fond CARTO est facultatif et nécessite Internet. Le cadrage suit les filtres ;
  les autres réglages préservent le zoom manuel. Le bouton de recentrage le restaure.
- Prédiction : sept caractéristiques, avec âge égal à 2026 moins l'année de
  construction (neuf imputé à zéro), altitude en mètres et zone H1/H2/H3. L'aide
  département/commune propose des valeurs locales ; cliquer Utiliser ces valeurs
  pour les appliquer. La provenance de l'altitude est indiquée ; la saisie reste libre.

La consommation est l'énergie finale totale des cinq usages en kWh/an, ni une
facture ni un chiffre par m². La lettre vient d'un autre modèle, pas d'un seuil
appliqué à cette consommation. Prudence sur l'existant et F/G : les erreurs
moyennes ne sont pas une confiance individuelle.

<!-- pagebreak -->
# Comparer et gérer les versions

## Deux logements et un résumé PDF

Dans Prédiction, choisir Comparer deux logements. Chaque profil possède son
bouton de calcul et son résultat. L'écart B moins A ne prouve pas l'effet d'une
rénovation. Modifier une saisie retire son ancien résultat et son export jusqu'au
recalcul ; l'autre logement reste indépendant. Le PDF reprend les sept entrées,
les unités, les résultats, la date, la version et les limites. La comparaison
exporte deux pages, une par logement.

## Gestion des données et modèles

1. Choisir source ADEME, département, période de réception et volume (maximum
5 000). Cocher la confirmation et lancer la collecte. Aucun appel n'est automatique.
2. Lire les cinq compteurs : reçus, conservés, doublons, remplacés et rejetés,
puis les raisons précises. Le JSON technique est dépliable. Les bornes sont fixées
sur la référence initiale, jamais recalculées sur un petit lot. La copie reste
préparée, non active ; les originaux et la réponse reçue sont conservés.
3. Examiner les limites, cocher l'accord et valider la version. Une seconde
confirmation permet de l'activer. Il est possible de garder les données initiales.
4. Pour entraîner, choisir des données validées et confirmer explicitement. Deux
forêts utilisent deux threads et affichent les étapes. Attendre la fin ; un échec
est journalisé sans modifier les modèles actifs. Ne pas lancer un calcul complet
uniquement pour une démonstration.
5. Examiner la nouvelle version, puis confirmer son activation. Le retour à la
sélection précédente est disponible. Les résultats antérieurs sont invalidés.

Avec le protocole fixe, les réceptions depuis 2025 restent réservées au test :
elles ne sont pas apprises. Une actualisation récente peut donc modifier surtout
l'évaluation. Changer les coupures demanderait une nouvelle décision méthodologique.

## Docker et incidents

Ouvrir Docker Desktop et attendre le moteur Linux, puis lancer :

```powershell
.\scripts\check_docker_inputs.ps1
docker compose build
docker compose up -d
docker compose down
```

L'arrêt conserve les versions dans le volume ; ne pas ajouter `-v`. Si un fichier
est absent, récupérer la copie préparée auprès du groupe. En cas de problème réseau,
réessayer plus tard ; une réponse incomplète n'est pas activée. Un verrou après arrêt
brutal doit être examiné avant suppression. Petit écran et Exploration après refonte
restent non confirmés visuellement. Docker a été construit et testé avec succès.
Les ports nominaux étant déjà occupés, le test a utilisé la surcouche locale :
`docker compose -f compose.yaml -f compose.test.yaml up -d`, puis `down` avec les
mêmes fichiers pour arrêter. Elle ouvre l'application sur 18501 et l'API sur 18000,
sans arrêter les services existants sur 8501/8000.
