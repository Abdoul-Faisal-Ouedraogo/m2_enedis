# Rapport technique — Habitat & énergie

> Projet M2 SISE — Analyse et prédiction énergétique des logements à partir des données ADEME.
> Auteurs : [À compléter]. Date : [À compléter].
>
> Ce rapport présente l'architecture de l'application et renvoie, pour chaque partie,
> vers la documentation détaillée du dossier `doc/`.

---

## 1. Contexte et objectif du projet

L'application exploite les diagnostics de performance énergétique (DPE) publiés par
l'ADEME pour estimer, à partir de quelques caractéristiques d'un logement :

- sa **consommation d'énergie finale annuelle** (`conso_5_usages_ef`, en kWh/an, cinq usages), par régression ;
- sa **classe DPE de A à G** (`etiquette_dpe`), par classification.

Les deux estimations proviennent de modèles distincts : la classe n'est pas déduite de
la consommation. Elles ont une visée pédagogique et ne remplacent pas un DPE réglementaire.

L'application couvre trois niveaux d'usage :

- **Standard et Intermédiaire** : exploration filtrée des données, carte, prédiction, comparaison de deux logements, exports CSV, PNG et PDF ;
- **Expert** : collecte d'un lot ADEME, préparation et validation d'une version de données, réentraînement, activation et retour à une version antérieure ;
- **API** : service FastAPI local exposant la même prédiction que l'interface.

La couverture des exigences est détaillée dans la [matrice des exigences](exigences_rendu.md).
Voir aussi le [README](../README.md) et le [guide utilisateur](guide_utilisateur.md).

---

## 2. Architecture de l'application

### Vue d'ensemble

L'interface Streamlit et l'API FastAPI partagent le même code de chargement des modèles
et de prédiction :

```
Utilisateur ─▶ Streamlit (home.py → src/streamlit_app.py)   :8501 ─┐
                                                                    ├─▶ src/model_registry.py + src/app_services.predict
Client HTTP ─▶ FastAPI   (src/prediction_api.py)             :8000 ─┘          │
                                                                               ▼
                          src/version_store.py (registre runtime/, pointeur active.json + verrou)
                                                                               │
              Entrées en lecture seule : output/cleaned_data.csv, métadonnées, référentiel communal,
              MLmodels/final_geo_v1, MLmodels/final_geo_v2_temperature
```

- **Versions immuables** : les données et modèles d'origine ne sont jamais écrasés. Chaque nouvelle version (données reçues, modèles réentraînés) est écrite dans `runtime/` (ou le chemin défini par `ENEDIS_RUNTIME`), avec un manifeste, des empreintes SHA-256 et un statut.
- **Version active** : le pointeur `active.json` désigne les données et modèles actifs. Streamlit et l'API le relisent, ce qui invalide les résultats devenus obsolètes.
- **Aucune action automatique** : ni collecte ni entraînement ne démarre au lancement.

Schéma éditable : [architecture.drawio](architecture.drawio).
Détails : [Architecture et exécution locale](documentation_technique.md).

### 2.1 Frontend (Streamlit)

- **Point d'entrée** : [`home.py`](../home.py), qui appelle `src/streamlit_app.py`. La configuration `.streamlit/config.toml` limite l'écoute à 127.0.0.1 et désactive la télémétrie.
- **Pages** (`src/app_design.py`) : Accueil, Exploration, Carte, Prédiction, Interprétation IA, Gestion des données et modèles.
- **Exploration** : filtres en cascade (département, classe DPE, type de bâtiment, chauffage, surface), indicateurs, quatre graphiques, comparaison de la répartition des classes DPE par type de bâtiment, tableau de 500 lignes au plus, export CSV de la sélection et de la comparaison, export PNG de chaque graphique.
- **Carte** (`src/app_map.py`) : marqueurs PyDeck avec légende A–G et infobulles ; 5 000 logements affichés par défaut, réglable de 1 000 à 10 000 ; fond de carte CARTO facultatif.
- **Prédiction** (`src/app_prediction_ui.py`, `src/app_geography.py`) : saisie manuelle ou choix d'une commune, qui renseigne automatiquement l'altitude, la zone climatique et les températures disponibles (valeurs modifiables ensuite), comparaison de deux logements et résumé PDF (`src/app_pdf.py`).
- **Interprétation IA** (`src/ai_interpretation.py`) : page facultative qui commente les résultats avec Google Gemini lorsque la clé `GEMINI_API_KEY` est configurée. Le modèle par défaut, `gemini-3.5-flash-lite`, peut être remplacé par la variable `GEMINI_MODEL`.
- **Gestion** (`src/expert_ui.py`) : chaque action Expert exige un clic et une confirmation explicite.

Détails : [Application Streamlit locale](application_streamlit_locale.md),
[Refonte de l'interface](refonte_interface_locale.md).

### 2.2 Backend (FastAPI)

L'API est définie dans [`src/prediction_api.py`](../src/prediction_api.py) et servie par
Uvicorn sur 127.0.0.1:8000.

| Endpoint | Rôle |
|---|---|
| `GET /health` | Vérifie que les modèles actifs sont chargés ; renvoie les versions des modèles et des données, et l'année de référence (2026). |
| `POST /predict` | Valide la saisie (modèle Pydantic `Housing` : champs inconnus et valeurs non finies refusés) et renvoie la consommation en kWh/an, la classe DPE, les unités, les versions et un avertissement. |
| `GET /docs`, `GET /openapi.json` | Documentation interactive Swagger et contrat OpenAPI. |

- **Erreurs** : 422 pour une saisie invalide, 503 lorsque les modèles sont indisponibles, altérés ou incompatibles.
- **Températures** : les champs `temperature_moyenne_annuelle` et `temperature_moyenne_hiver` sont facultatifs et utilisés par le modèle v2.
- **Périmètre** : aucune route d'entraînement ni d'activation, pas d'authentification ; l'API est prévue pour un usage local.
- **Exemple de requête** : [`examples/prediction.json`](../examples/prediction.json).

Détails : [Architecture et exécution locale](documentation_technique.md), section 5 du [README](../README.md).

### 2.3 Modèles de machine learning

Les modèles sont des forêts aléatoires scikit-learn (100 arbres, profondeur 10, graine 42,
deux threads). Ils sont entraînés sur 453 680 logements et évalués une seule fois sur un
lot réservé interne de 107 666 logements.

- **Protocole** (`src/validation_plan.py`) : découpage chronologique (réceptions antérieures à 2024 pour l'entraînement, 2024 pour la validation, depuis 2025 pour le lot réservé) et par groupes d'adresse, d'immeuble et de diagnostic remplacé.
- **Sélection** : trois variantes de classification ont été comparées sur la seule validation ; `rf_depth10_balanced` a été retenue pour son F1 macro.

| Version | Variables | Accuracy DPE | F1 macro | MAE (kWh/an) | RMSE (kWh/an) | R² |
|---|---|---|---|---|---|---|
| `final_geo_v1` | 7 | 55,41 % | 0,4031 | 1 814,68 | 2 957,21 | 0,6531 |
| `final_geo_v2_temperature` | 9 | 55,05 % | 0,4013 | 1 813,99 | 2 952,84 | 0,6541 |

Ces résultats proviennent des fichiers `results.json` de chaque dossier de `MLmodels/`.
Sur le même lot, prédire toujours la classe C donne 36,72 % de DPE corrects, et prédire
la médiane donne une MAE de 3 505,67 kWh/an.

- **Variables v1** : surface habitable, nombre de niveaux, âge du bâtiment (référence 2026), altitude moyenne, énergie de chauffage principale, type de bâtiment et zone climatique (H1, H2, H3).
- **Variables v2** : celles de la v1, plus les températures moyennes annuelle et hivernale.
- **Version active par défaut** : définie par la variable `ENEDIS_DEFAULT_MODEL`, fixée à `final_geo_v2_temperature` dans Docker ; sans cette variable, l'exécution locale utilise `final_geo_v1`. La page Gestion permet de changer de version.
- **Limites** : les performances sont faibles sur les classes F et G et sur les logements existants. Le lot réservé est interne, ce n'est pas une validation externe. Aucun intervalle de confiance individuel n'est fourni.
- **Comparaison détaillée v1 / v2** (par classe et par population neuf/existant) : [À compléter].

Détails : [Rapport ML final](rapport_ml_final.md),
[Modèles finaux](modeles_finaux_2026-10-29.md),
[Audit des modèles](audit_modeles_2026-10-29.md), section 8 du [README](../README.md).

### 2.4 Scripts

Les scripts du dossier [`scripts/`](../scripts/) se lancent manuellement ; ceux qui
entraînent un modèle exigent l'option `--run`.

| Famille | Scripts |
|---|---|
| Données | `download_data.py` (téléchargement depuis la release GitHub `data-v1` avec contrôle SHA-256, puis génération des températures), `enrich_temperature.py` (températures Open-Meteo 2015–2024), `freeze_initial_preparation.py` |
| Entraînement | `prepare_classification_comparison.py`, `compare_classification.py`, `train_final_models.py` (v1), `train_temperature_models.py` (v2) |
| Vérification | `verify_final_models.py`, `verify_app.py`, `verify_notebooks.py`, `verify_preparation.py`, `verify_geography.py`, `verify_validation_groups.py` |
| Audit | `audit_raw_metadata.py`, `audit_partition_composition.py`, `audit_prepared_batch.py` |
| Docker | `check_docker_inputs.ps1`, `smoke_container.py`, `verify_container_sources.py` |
| Documentation | `render_submission_docs.py`, `write_final_model_report.py`, `update_final_notebooks.py` |

Les notebooks du dossier [`Notebooks_Api_Traitement/`](../Notebooks_Api_Traitement/) couvrent
la préparation (`1_data_preparation.ipynb`), l'enrichissement (`1a_enrichissement_donnees.ipynb`),
la classification (`2_classification_dpe.ipynb`) et la régression (`3_regression_consommation.ipynb`).

Détails : [Modèles finaux](modeles_finaux_2026-10-29.md), section « Reproduire ».

### 2.5 Jeux de données

| Jeu | Origine | Usage |
|---|---|---|
| DPE des logements existants et neufs | API ADEME data-fair (`dpe03existant`, `dpe02neuf`) | Données d'apprentissage ; extraction plafonnée à 5 000 lignes par département et par source |
| `output/cleaned_data.csv` | Notebook de préparation | 616 057 logements, 16 colonnes, 94 départements |
| `output/cleaned_data_metadata.csv` | Notebook de préparation | Traçabilité (source, numéros DPE, dates, identifiants BAN), jamais utilisée comme variable |
| `data/communes-france-2025.csv` | Référentiel communal | Altitude et aide géographique, avec corrections pour Lyon et Pierre-Bénite |
| `output/temperature_v2/temperatures_communes.csv` | API Open-Meteo, 2015–2024 | Températures annuelle et hivernale du modèle v2 |

- **Distribution** : `scripts/download_data.py` télécharge les trois fichiers préparés, puis génère le fichier de températures via `scripts/enrich_temperature.py`. Aucun n'est suivi par Git.
- **Nettoyage** : la préparation applique des bornes IQR figées sur le coût et la surface, définies dans [`config/preparation_initial_geo_v1.json`](../config/preparation_initial_geo_v1.json).
- **Client Enedis** (`src/data_requesters/enedis.py`) : rôle dans la chaîne de traitement [À compléter].
- **Représentativité** : l'échantillon n'est pas représentatif du parc de logements français.

Détails : [Préparation et validation](preparation_validation_2026-10-29.md),
[Audit des rejets Rhône](audit_rejets_rhone.md),
[Zones climatiques par département](<La répartition des départements par zone climatique.pdf>).

### 2.6 Environnement (Docker)

- **Image** ([`Dockerfile`](../Dockerfile)) : base `python:3.13.18-slim-bookworm`, dépendances de `requirements-app.txt` et utilisateur non root. Elle contient le code, la configuration et les modèles v1 et v2, sans données ni secret.
- **Services** ([`compose.yaml`](../compose.yaml)), construits à partir de la même image :

| Service | Adresse | Rôle |
|---|---|---|
| `application` | 127.0.0.1:8501 | Interface Streamlit |
| `api` | 127.0.0.1:8000 | API FastAPI, avec contrôle de santé sur `/health` |

- **Stockage** : les fichiers de données, y compris les températures, sont montés en lecture seule ; le volume `expert-runtime`, partagé par les deux services, conserve les versions Expert.
- **Configuration** : le fichier local `.env`, créé à partir de [`.env.example`](../.env.example), fournit `GEMINI_API_KEY` et éventuellement `GEMINI_MODEL`. La politique `restart: unless-stopped` relance les services au redémarrage de Docker.
- **Sécurité** : système de fichiers en lecture seule, `cap_drop: ALL`, `no-new-privileges` et deux CPU par service.
- **Ports alternatifs** : [`compose.test.yaml`](../compose.test.yaml) publie l'application sur 18501 et l'API sur 18000.
- **Déploiement** : l'application est prévue pour un usage local ; les prérequis d'une mise en ligne sont décrits dans [deploy/README.md](../deploy/README.md).

Détails : [Docker local](docker_local.md), section 6 du [README](../README.md).

---

## 3. Technologies utilisées

| Technologie | Rôle dans le projet |
|---|---|
| Python 3.13 | Langage de l'application, de l'API, des scripts et des notebooks |
| Streamlit 1.66 | Interface web : pages, filtres et formulaires |
| PyDeck | Carte interactive des logements |
| Matplotlib | Graphiques et exports PNG |
| Altair | Graphique de comparaison des classes DPE par type de bâtiment |
| ReportLab | Résumés PDF des estimations |
| FastAPI et Pydantic | API REST locale et validation des entrées |
| Uvicorn | Serveur ASGI de l'API |
| pandas, NumPy, SciPy | Manipulation et préparation des données |
| scikit-learn 1.7 | Forêts aléatoires de classification et de régression |
| joblib | Sauvegarde et chargement des modèles |
| requests | Appels aux API ADEME, Enedis, Open-Meteo et Gemini |
| MLflow | Suivi des expériences de modélisation (dossier `mlruns/`) |
| Jupyter | Notebooks de préparation et de modélisation |
| Google Gemini | Interprétation facultative des résultats |
| Docker et Docker Compose | Image locale et services application et API |
| pytest | Tests automatisés |
| uv | Verrouillage des dépendances (`uv.lock`) |
| GitHub | Suivi des tâches et distribution des données (release `data-v1`) |

Versions exactes : [`requirements-app.txt`](../requirements-app.txt) et [`pyproject.toml`](../pyproject.toml).

---

## 4. Installation et lancement

Les commandes ci-dessous concernent Windows ; le [README](../README.md) détaille
l'ensemble des étapes et le dépannage.

1. **Environnement** : après avoir cloné le dépôt, créer l'environnement avec `py -3.13 -m venv .venv-app`, puis installer `requirements-app.txt`.
2. **Données** : `python scripts/download_data.py`. La première exécution génère aussi les températures du modèle v2 ; elle nécessite Internet et peut prendre quelques minutes.
3. **Interface** : `python -m streamlit run home.py`, puis ouvrir http://127.0.0.1:8501.
4. **API** : dans un second terminal, `python -m uvicorn src.prediction_api:app --host 127.0.0.1 --port 8000`, puis ouvrir http://127.0.0.1:8000/docs.
5. **Docker** (alternative) : créer `.env` à partir de `.env.example`, puis lancer `.\scripts\check_docker_inputs.ps1`, `docker compose build` et `docker compose up -d`. Arrêter avec `docker compose down`, sans l'option `-v`, pour conserver les versions Expert.

### Tests

Les tests automatisés couvrent :

- les pages Streamlit, leurs filtres et leurs exports ;
- la carte et le formulaire de prédiction ;
- l'API ;
- la configuration Docker ;
- l'interprétation Gemini, avec des réponses simulées ;
- la préparation des données ;
- le versionnement Expert, avec des réponses ADEME simulées et des entraînements réduits ;
- la mise en page de la documentation.

Ils se lancent avec `python -m pytest -q`, après `scripts/download_data.py`. Les 93 tests de la
suite réussissent.

Détails : [Guide utilisateur](guide_utilisateur.md), [Docker local](docker_local.md),
[guide de contribution](../CONTRIBUTING.md).

---

## 5. Annexes — documents de `doc/`

| Document | Description |
|---|---|
| [application_streamlit_locale.md](application_streamlit_locale.md) | Fonctionnement de l'application Streamlit : pages, filtres, carte, exports et vérifications. |
| [architecture.drawio](architecture.drawio) | Schéma d'architecture éditable : Streamlit, API, registre de versions et chaînes Expert. |
| [audit_modeles_2026-10-29.md](audit_modeles_2026-10-29.md) | Audit des notebooks et des modèles précédant les modèles finaux. |
| [audit_rejets_rhone.md](audit_rejets_rhone.md) | Analyse des rejets d'un lot réel du Rhône et justification des bornes IQR figées. |
| [docker_local.md](docker_local.md) | Commandes Docker, montages, ports et contrôle de fonctionnement dans l'image. |
| [documentation_technique.md](documentation_technique.md) | Documentation technique : services, stockage, Docker, chaînes Expert et API. |
| [exigences_rendu.md](exigences_rendu.md) | Matrice des exigences, de leur vérification et des limites connues. |
| [guide_utilisateur.md](guide_utilisateur.md) | Mode d'emploi de l'application, de la gestion des versions et de Docker. |
| [La répartition des départements par zone climatique.pdf](<La répartition des départements par zone climatique.pdf>) | Référentiel des zones climatiques H1, H2 et H3 par département. |
| [modeles_finaux_2026-10-29.md](modeles_finaux_2026-10-29.md) | Protocole, comparaison des variantes et résultats détaillés des modèles `final_geo_v1`. |
| [preparation_validation_2026-10-29.md](preparation_validation_2026-10-29.md) | Corrections géographiques et préparation du découpage de validation. |
| [rapport_ml_final.md](rapport_ml_final.md) | Synthèse de la modélisation : données, protocole, résultats et limites. |
| [refonte_interface_locale.md](refonte_interface_locale.md) | Conception de l'interface : présentation, carte, comparaison de deux logements. |
| [scenario_video.md](scenario_video.md) | Scénario chronométré de la vidéo de démonstration. |
