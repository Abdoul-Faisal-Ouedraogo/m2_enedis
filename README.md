# App Enedis — Analyse et prédiction énergétique

Application Streamlit d’analyse des diagnostics de performance énergétique
(DPE) et de la consommation énergétique des logements en France.

Le projet permet de :

- explorer les données ADEME avec des filtres, KPI, graphiques et exports ;
- visualiser les logements sur une carte interactive ;
- prédire une classe DPE et une consommation annuelle ;
- enrichir les prédictions avec des températures OpenData ;
- interpréter les résultats avec Gemini, si une clé API est configurée ;
- recevoir de nouvelles données ADEME ;
- créer, valider, activer et réentraîner des versions de modèles ;
- exposer les prédictions via une API FastAPI.

> **Important** : les prédictions sont pédagogiques et ne constituent pas un
> diagnostic DPE réglementaire.

## 1. Prérequis

### Installation locale

- Windows 10/11, Linux ou macOS ;
- Python 3.13 ;
- accès Internet pour installer les dépendances et télécharger les données ;
- environ 4 Go d’espace libre pour les dépendances et les artefacts.

### Installation Docker

- Docker Desktop démarré ;
- moteur Linux/WSL2 actif sous Windows ;
- Docker Compose disponible.

## 2. Récupérer le projet

```powershell
git clone https://github.com/Abdoul-Faisal-Ouedraogo/App_Enedis.git
cd App_Enedis
```

Le dépôt contient les sources, l’application, les artefacts de modèles et la
configuration Docker. Les fichiers de données volumineux sont téléchargés
séparément et vérifiés par empreinte SHA-256.

## 3. Lancement local sous Windows

### 3.1 Créer l’environnement Python

Depuis la racine du projet :

```powershell
py -3.13 -m venv .venv-app
.\.venv-app\Scripts\python.exe -m pip install --upgrade pip
.\.venv-app\Scripts\python.exe -m pip install -r requirements-app.txt
```

Si la commande `py -3.13` n’existe pas, installer Python 3.13 depuis
[python.org](https://www.python.org/downloads/), puis relancer les commandes.

### 3.2 Télécharger les données de base

```powershell
.\.venv-app\Scripts\python.exe scripts/download_data.py
```

Cette commande récupère et vérifie :

- `data/communes-france-2025.csv` ;
- `output/cleaned_data.csv` ;
- `output/cleaned_data_metadata.csv`.

### 3.3 Vérifier les fichiers nécessaires

Pour utiliser la version v2 avec température, les fichiers suivants doivent
également être présents :

```text
output/temperature_v2/temperatures_communes.csv
MLmodels/final_geo_v2_temperature/classification.joblib
MLmodels/final_geo_v2_temperature/regression.joblib
MLmodels/final_geo_v2_temperature/results.json
MLmodels/final_geo_v2_temperature/variables.json
```

Ces artefacts sont générés par l’équipe lors de l’enrichissement et de
l’entraînement v2. La version v1 reste conservée dans
`MLmodels/final_geo_v1/` pour permettre un retour arrière.

### 3.4 Démarrer Streamlit

```powershell
.\.venv-app\Scripts\python.exe -m streamlit run home.py `
  --server.address 127.0.0.1 `
  --server.port 8501 `
  --browser.gatherUsageStats false
```

Ouvrir ensuite :

```text
http://127.0.0.1:8501
```

Arrêter l’application avec `Ctrl+C`.

## 4. Utiliser l’application

### Contexte

Présente les données disponibles, les indicateurs principaux, les tableaux,
les filtres et les visualisations.

### Exploration

Permet de filtrer les logements par département, classe DPE, type de bâtiment,
énergie et surface. Les données filtrées peuvent être exportées en CSV et les
graphiques en PNG.

### Carte

Affiche les logements sous forme de marqueurs interactifs avec des infobulles.
Le fond cartographique nécessite une connexion Internet ; les marqueurs
restent disponibles sans fond de carte.

### Prédiction

Deux modes sont disponibles :

- saisie manuelle de toutes les caractéristiques ;
- sélection d’une commune avec proposition de l’altitude, de la zone
  climatique et des températures OpenData.

La version v2 active utilise neuf variables, dont :

- température moyenne annuelle ;
- température moyenne hivernale.

### Interprétation IA

Cette page est facultative. Pour l’activer, créer une clé Gemini puis la
définir dans la session PowerShell :

```powershell
$env:GEMINI_API_KEY = "votre_cle_gemini"
```

Ou créer le fichier local `.streamlit/secrets.toml` :

```toml
GEMINI_API_KEY = "votre_cle_gemini"
```

Ne jamais publier cette clé dans Git ou dans une capture d’écran. Une clé
exposée doit être révoquée et remplacée.

## 5. Démarrer l’API FastAPI localement

Dans un second terminal, depuis la racine :

```powershell
.\.venv-app\Scripts\python.exe -m uvicorn src.prediction_api:app `
  --host 127.0.0.1 `
  --port 8000
```

Vérifier l’état de l’API :

```powershell
curl.exe http://127.0.0.1:8000/health
```

Documentation interactive :

```text
http://127.0.0.1:8000/docs
```

Contrats OpenAPI :

```text
http://127.0.0.1:8000/openapi.json
```

L’endpoint de prédiction est :

```text
POST http://127.0.0.1:8000/predict
```

Il utilise les mêmes modèles et les mêmes règles de validation que Streamlit.

## 6. Lancement avec Docker Compose

### 6.1 Vérifier Docker et les fichiers locaux

Démarrer Docker Desktop, puis exécuter :

```powershell
.\scripts\check_docker_inputs.ps1
```

### 6.2 Construire et démarrer les services

```powershell
docker compose build
docker compose up -d
```

Les services sont disponibles uniquement en local :

| Service | Adresse |
|---|---|
| Streamlit | http://127.0.0.1:8501 |
| API | http://127.0.0.1:8000/health |
| Documentation API | http://127.0.0.1:8000/docs |

### 6.3 Vérifier les conteneurs

```powershell
docker compose ps
docker compose logs -f application
docker compose logs -f api
```

Le contrôle fonctionnel complet se lance avec :

```powershell
docker compose run --rm --no-deps application `
  python scripts/smoke_container.py --api-url http://api:8000
```

Résultat attendu :

```text
OK smoke : pages initiales + gestion, prediction, commune, exports et empreintes.
```

### 6.4 Arrêter les services

```powershell
docker compose down
```

Ne pas utiliser `docker compose down -v` sauf si la suppression du volume de
versions est volontaire. Ce volume contient les versions de données et de
modèles créées par le niveau Expert.

Si les ports 8501 ou 8000 sont déjà utilisés, utiliser :

```powershell
docker compose -f compose.yaml -f compose.test.yaml up -d
```

Les ports alternatifs sont alors 18501 pour Streamlit et 18000 pour l’API.

## 7. Fonctionnalités du niveau Expert

La page **Gestion des données et modèles** permet de :

1. collecter un lot ADEME selon un département, une source et une période de
   réception ;
2. préparer et auditer une nouvelle version de données ;
3. valider cette version avant toute activation ;
4. entraîner une nouvelle version de modèles ;
5. activer la version choisie ;
6. revenir à la version précédente.

Les modèles et données existants ne sont jamais écrasés. Les versions sont
stockées dans `runtime/`, ou dans le chemin défini par `ENEDIS_RUNTIME`.

Le réentraînement est volontaire et ne démarre jamais automatiquement au
lancement de l’application.

## 8. Températures OpenData et modèle v2

L’enrichissement utilise l’API historique Open-Meteo sur la période
2015–2024. Deux variables sont ajoutées :

- `temperature_moyenne_annuelle` ;
- `temperature_moyenne_hiver`.

Pour régénérer le dataset enrichi :

```powershell
.\.venv-app\Scripts\python.exe scripts/enrich_temperature.py
```

Pour entraîner les modèles v2 :

```powershell
.\.venv-app\Scripts\python.exe scripts/train_temperature_models.py --run
```

La v2 est versionnée séparément et la v1 n’est pas supprimée. La température
affectée à une commune est une approximation issue des points météorologiques
représentatifs documentés dans `output/temperature_v2/manifest.json`.

## 9. Tests

Exécuter les tests de l’application :

```powershell
.\.venv-app\Scripts\python.exe -m pytest -q
```

Tester uniquement l’intégration Docker :

```powershell
.\.venv-app\Scripts\python.exe -m pytest -q tests/test_docker_config.py
```

Tester le niveau Expert et l’API :

```powershell
.\.venv-app\Scripts\python.exe -m pytest -q `
  tests/test_expert_data.py `
  tests/test_expert_models.py `
  tests/test_prediction_api.py
```

Les tests utilisent des données simulées pour éviter une collecte ADEME ou un
entraînement complet involontaire.

## 10. Dépannage rapide

### `COPY MLmodels/final_geo_v2_temperature ... not found`

Vérifier que le dossier existe, puis reconstruire l’image :

```powershell
Test-Path MLmodels/final_geo_v2_temperature
docker compose build --no-cache
```

### Données absentes

Relancer :

```powershell
.\.venv-app\Scripts\python.exe scripts/download_data.py
```

### Port déjà utilisé

Utiliser la configuration de test sur les ports 18501 et 18000, ou arrêter le
processus qui utilise le port concerné.

### API non disponible juste après `docker compose up -d`

L’API peut prendre quelques secondes pour charger les modèles. Vérifier :

```powershell
docker compose ps
curl.exe http://127.0.0.1:8000/health
```

### Erreur Gemini 429 ou 503

Il s’agit généralement d’une limite temporaire ou d’une indisponibilité du
service. Vérifier la clé, attendre quelques secondes et réessayer.

## 11. Limites et interprétation des résultats

- Les prédictions ne remplacent pas un DPE réglementaire.
- La classification DPE reste moins fiable pour les classes F et G.
- Les métriques sont calculées sur un lot réservé interne, pas sur une
  validation externe indépendante.
- L’API et Docker sont configurés pour un usage local ; aucun déploiement
  Internet public n’est inclus.
- Les clés API doivent être fournies par variables d’environnement ou secrets
  locaux, jamais par le code source.

## 12. Documentation complémentaire

- [Guide utilisateur](doc/guide_utilisateur.md)
- [Documentation technique](doc/documentation_technique.md)
- [Rapport ML final](doc/rapport_ml_final.md)
- [Architecture](doc/architecture.drawio)
- [Scénario de démonstration](doc/scenario_video.md)
- [Matrice des exigences](doc/exigences_rendu.md)
- [Audit des rejets ADEME](doc/audit_rejets_rhone.md)

## Contribution

Pour contribuer, créer une issue ou une branche dédiée, effectuer les tests,
puis proposer une Pull Request décrivant les changements et les commandes de
validation exécutées.
