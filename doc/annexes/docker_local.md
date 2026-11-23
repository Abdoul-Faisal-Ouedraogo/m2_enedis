# Docker local

Depuis PowerShell à la racine du dépôt :

```powershell
.\scripts\check_docker_inputs.ps1
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail 50
docker compose run --rm --no-deps application python scripts/smoke_container.py --api-url http://api:8000
docker compose down
```

Application : http://127.0.0.1:8501. API : http://127.0.0.1:8000/health et
http://127.0.0.1:8000/docs. Les fichiers de données sont des montages
en lecture seule ; les nouveaux travaux Expert seront conservés dans un volume
distinct, jamais dans les originaux. `down` conserve ce volume ; ne pas utiliser
`down -v` pour un arrêt normal. `create_host_path: false` empêche Compose de créer
un dossier vide à la place d'un CSV absent. Le script Windows vérifie les entrées.

Sur un autre ordinateur : installer Docker Desktop avec moteur Linux/WSL2,
copier le dépôt avec les modèles finaux et les trois fichiers locaux suivants,
en conservant leurs chemins : `output/cleaned_data.csv`,
`output/cleaned_data_metadata.csv`, `data/communes-france-2025.csv`.
Les autres CSV bruts et sauvegardes ne sont pas nécessaires au démarrage.
Le contexte utilise une liste d'autorisation et n'incorpore ni CSV, ni secrets,
ni environnements, ni PDF générés. L'installation des paquets et de l'image de
base nécessite Internet à la construction ; aucune collecte ni entraînement au
démarrage. Les modèles sont chargés depuis les artefacts finaux contrôlés.

État du 30/10/2026 : moteur initialement inaccessible, puis disponible pendant
le travail. **Image construite et deux conteneurs réellement lancés et sains.**
Les ports nominaux étaient occupés (Streamlit existant et autre service local),
conservés sans arrêt. Une surcouche locale de test a permis la vérification :

```powershell
docker compose -f compose.yaml -f compose.test.yaml up -d --wait
docker compose -f compose.yaml -f compose.test.yaml run --rm --no-deps application python scripts/smoke_container.py --api-url http://api:8000
docker compose -f compose.yaml -f compose.test.yaml down
```

Adresses de cette surcouche : http://127.0.0.1:18501 et
http://127.0.0.1:18000/health. Compose >= 2.24.4 requis pour `!override`.
Le Compose principal reste strictement sur 127.0.0.1:8501 et 127.0.0.1:8000.
Pour le lancement nominal, libérer ses propres terminaux utilisant ces ports,
sans arrêter un service tiers. Si le moteur est arrêté, ouvrir Docker Desktop,
activer Linux/WSL2 si nécessaire et attendre « Engine running ».

Le smoke-test a réussi DANS l'image : quatre pages initiales et Gestion,
prédiction, application de la commune de Lyon, quatre PNG, CSV et génération
du résumé PDF. L'API conteneur a répondu réellement aux endpoints santé et
prédiction (9 101,147 kWh/an, D, version final_geo_v1 pour l'exemple). L'utilisateur
du conteneur est non root ; les trois montages sont `RW=false`. Le volume des
versions est accessible en écriture. Empreintes comparées avant/après le test.
Ces tests AppTest/HTTP ne remplacent pas une inspection visuelle dans le navigateur.

Les contrôles visuels **petit écran** et **Exploration après refonte** restent
non confirmés ; voir `refonte_interface_locale.md`.
