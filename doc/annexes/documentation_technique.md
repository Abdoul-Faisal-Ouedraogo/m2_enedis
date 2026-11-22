# Architecture et exécution locale

Version Expert, 30 octobre 2026. Sources éditables : modules Python, Markdown et
`architecture.drawio`. Les branches numérotées sont empilées sans fusion ; aucune
publication. Python 3.13, dépendances application séparées du ML historique.

## Services et stockage

Streamlit (127.0.0.1:8501) et FastAPI (127.0.0.1:8000) partagent le chargeur
`model_registry` et `app_services.predict`. Le modèle initial passe par
`load_final_bundle`, avec empreintes et fixture de développement. Les nouvelles
versions sont contrôlées avant chargement. Sept caractéristiques, référence 2026,
zones H1/H2/H3 ; consommation et lettre produites indépendamment.

`VersionStore` lit un pointeur actif atomique dans `runtime/` (variable
`ENEDIS_RUNTIME` possible). Chaque version possède un manifeste, des empreintes
et un statut. Les écritures du pointeur sont protégées par verrou exclusif.
Les données reçues et les modèles entraînés vont dans de nouveaux dossiers,
jamais dans `output/cleaned_data.csv` ni `MLmodels/final_geo_v1`.
L'activation exige des données validées et des modèles prêts/compatibles.
La révision invalide les résultats UI ; chemins et empreintes horodatées
renouvellent les caches. L'API observe le pointeur à chaque requête.

## Docker Compose

L'image non privilégiée inclut code, dépendances, notebook de règles et seuls
modèles finaux. La liste d'autorisation `.dockerignore` exclut CSV, secrets,
environnements, bruts, sauvegardes et PDF. Trois fichiers hôtes sont montés en
lecture seule : `output/cleaned_data.csv`, `output/cleaned_data_metadata.csv`,
`data/communes-france-2025.csv`. Les deux services partagent un volume de versions
distinct du `runtime/` utilisé hors Docker. Racine conteneur en lecture seule,
zone temporaire limitée et deux CPU par service. Les ports publiés sont locaux.

```powershell
docker compose config --quiet
docker compose build
docker compose up -d
docker compose run --rm --no-deps application python scripts/smoke_container.py
docker compose down
```

Autre PC : copier dépôt, modèles finaux et trois entrées ci-dessus, installer
Docker Desktop Linux/WSL2. La construction télécharge des paquets, pas des données.
Le moteur était initialement arrêté, puis l'image a été construite et les deux
services testés avec succès. Les ports nominaux étant occupés, `compose.test.yaml`
utilise seulement 127.0.0.1:18501/18000. Montages RO et volume writable vérifiés.
Les services existants ont été préservés. Voir `docker_local.md`.

<!-- pagebreak -->
# Chaînes Expert et contrôles

## Collecte et apprentissage

Le client ADEME existant possède un parcours borné : filtrage réception/département,
pages de 500, trois tentatives, timeout connexion/lecture 5/30 s, pauses et contrôle
du domaine des liens suivants. Les filtres sont revérifiés dans les réponses.
La préparation réutilise les méthodes IQR coût/surface et le regroupement des
énergies du projet, avec jointure communale corrigée et repli départemental.
Les bornes IQR sont figées à partir des sources initiales : coût jusqu'à 3 019,70,
surface jusqu'à 164 m². Le profil versionné et les motifs de rejet sont consignés ;
aucun quantile n'est recalculé sur les petits lots. Les audits des anciens bilans
restent en lecture seule, selon leurs règles d'origine.
Les doublons de numéro sont éliminés ; seuls les remplaçants admis retirent un ancien
diagnostic de la nouvelle copie. Les lots portent une provenance distincte.

L'apprentissage reprend les groupes BAN/immeuble/remplacement et les coupures
2024/2025. Groupes transverses, dates invalides et groupes inconnus sont exclus.
Réglages finaux figés avant fit ; deux forêts entraînées sur train+validation,
puis test réservé une fois, sans sélection sur ses résultats. Paramètres, contrats,
versions, partitions, prédictions et résultats sont sauvegardés ; échec journalisé.
Les défauts de représentativité et de préparation amont restent présents.

## API

```powershell
.\.venv-app\Scripts\python.exe -m uvicorn src.prediction_api:app --host 127.0.0.1 --port 8000
curl.exe http://127.0.0.1:8000/health
curl.exe -H "Content-Type: application/json" --data-binary "@examples/prediction.json" http://127.0.0.1:8000/predict
```

`POST /predict` valide les sept champs, refuse les supplémentaires, les catégories
inconnues et valeurs non finies. Réponse : consommation, lettre, unités, versions
des données/modèles et limites. Codes 422 (saisie), 503 (service/modèles).
`GET /health` vérifie les modèles actifs ; `/openapi.json` décrit le contrat.
`/docs` fournit Swagger (ses ressources peuvent nécessiter Internet).
Aucune route d'entraînement ni d'activation publique n'est exposée.

## Vérifier et poursuivre

```powershell
uv pip install --python .venv-app/Scripts/python.exe -r requirements-app-test.txt
.\.venv-app\Scripts\python.exe -X utf8 scripts/verify_app.py
.\.venv-app\Scripts\python.exe scripts/verify_final_models.py
.\.venv-app\Scripts\python.exe scripts/render_submission_docs.py
```

Tests réseau simulés, forêts de deux arbres sur 36 lignes en répertoires temporaires,
contrats API, changement de version et régressions UI. Pas de collecte ni fit complet
de test. Le serveur API a aussi été interrogé réellement sur un port local de test.
Petit écran, Exploration après refonte et dernière correction de caméra restent à
confirmer dans le navigateur. Le sujet complet n'est pas fourni : matrice dans
`exigences_rendu.md`. Le futur déploiement est préparé mais non exécuté ; avant toute
exposition distante, revoir authentification, accès aux actions Expert et persistance.
