# Application Streamlit locale — 30 octobre 2026

Issue : [#19](https://github.com/Abdoul-Faisal-Ouedraogo/App_Enedis/issues/19),
assignée à mbekkar. Branche : `feat/19-application-streamlit`, créée depuis
`fix/18-coherence-modeles-ml`, sans fusion. `CONTRIBUTING.md` lu avant les
modifications ; la base de branche expressément demandée prime sur sa
recommandation générale de partir de main.

## Préservation du travail du groupe

Au départ, aucun fichier suivi modifié ; sept fichiers locaux non suivis :
`home.py`, `requirements-app.txt`, `scripts/verify_app.py` et les scripts
`finalize_ml_notebooks.py`, `integrate_geography.py`,
`update_ml_data_reference.py`, `update_notebooks.py`.
Ils ont été lus pour les fichiers d'application puis tous sauvegardés avec
leur arborescence dans :
`C:\Users\mouni\AppData\Local\Temp\App_Enedis_avant_streamlit_20261030_153247`.
Les trois fichiers d'application ont été repris ; les quatre autres scripts
locaux et tous les notebooks, données et modèles sont conservés.

L'environnement `.venv-ml`, `requirements.txt`, `pyproject.toml` et `uv.lock`
n'ont pas été modifiés. `.venv-app` existait déjà et contenait les dépendances
application ; les seuls ajouts d'environnement ont servi à exécuter pytest.
Les dépendances directes de l'application sont explicites dans
`requirements-app.txt`, celles des tests dans `requirements-app-test.txt`.

## Fonctionnement

Entrée : `home.py`. Interface : `src/streamlit_app.py`. Services isolés :
`src/app_services.py`. Illustration originale locale : `assets/habitat.svg`.
Configuration : `.streamlit/config.toml` (écoute 127.0.0.1, télémétrie désactivée).

Les quatre pages sont contrôlées par une navigation latérale. Les sélections
département, DPE, bâtiment et chauffage sont en cascade ; les listes vides
signifient toutes les valeurs. Surface par curseur et inclusion des surfaces
absentes par case à cocher. Les filtres se conservent entre Exploration et Carte.
Les mesures et l'affichage en pourcentage sont réglables. Le bouton de remise
à zéro restaure la population complète. La sélection vide est explicitement gérée.

Les indicateurs, quatre graphiques, tableau et exports utilisent la sélection.
Le tableau affiche au plus 500 lignes, le CSV toutes les lignes filtrées et
toutes les colonnes originales (BOM UTF-8, séparateur `;`, virgule décimale).
Le CSV est préparé seulement sur demande. Les PNG utilisent directement
Matplotlib/Agg ; pas de Kaleido, Chrome ou service d'export. Histogramme et
boîtes calculés sur toutes les valeurs filtrées disponibles ; valeurs extrêmes
masquées dans les boîtes, sans les retirer des calculs. Nuage limité à
5 000 lignes renseignées filtrées, graine 42 et effectif dans le titre.

La carte utilise des marqueurs PyDeck/WebGL avec infobulles. Les coordonnées
doivent être finies et dans l'emprise lat. 41–51,5°, lon. −5,5–10° (métropole,
Corse comprise). Sur les données présentes : **613 447 coordonnées admissibles**,
**2 610 écartées**, **5 000 logements représentés par défaut**. Limite réglable
entre 1 000 et 10 000 ; tirage déterministe, nombres affichés. Les adresses
superposées ne sont pas dédoublonnées. Le fond CARTO est une option en ligne
désactivée par défaut ; sans fond, marqueurs sur canevas local navigable.

Les modèles sont exclusivement chargés via `load_final_bundle()` ; contrôles
d'intégrité et exemples de rechargement existants préservés. Cache ressource
des deux modèles et cache des données/graphiques/exports. Catégories extraites
de l'encodeur final. Quatre variables numériques + trois catégorielles, âge
référencé à 2026, zones H1/H2/H3, altitude communale en mètres. Les valeurs
hors du domaine numérique observé déclenchent un avertissement. Les saisies
non finies, surface non positive, niveaux non entiers et catégories inconnues
sont refusées. Données absentes : message clair, modèles utilisables si présents.
Modèles absents ou altérés : message bloquant, aucun repli historique.

Les scores affichés viennent de `results.json` : accuracy 55,41 %, F1 macro
0,4031 et MAE 1 814,68 kWh/an sur le lot réservé interne de 107 666 logements.
Tableaux neuf/existant et détails par classe, limites F/G et avertissement MAE
sans intervalle de confiance individuel. Les différences temporelles, l'imputation
du neuf à l'âge nul, les limites du nettoyage global et de la représentativité
sont exposées. Aucun nouvel entraînement ni nouvelle prédiction sur le lot réservé.

## Vérifications reproductibles

Depuis la racine :

```powershell
uv pip check --python .venv-app/Scripts/python.exe
.\.venv-app\Scripts\python.exe -m pytest -q
.\.venv-app\Scripts\python.exe scripts/verify_final_models.py
.\.venv-app\Scripts\python.exe -m compileall -q home.py src scripts tests
git diff --check
```

Résultat initial : **17 tests réussis** (`17 passed`).

Tests `tests/test_streamlit_app.py` : ouverture des quatre pages sur les
616 057 lignes, quatre filtres combinés et surface, navigation Exploration/Carte,
réglage des marqueurs, radio et cases, export CSV et quatre boutons PNG,
réinitialisation et sélection vide. CSV relu avec vérification des effectifs,
colonnes, département, DPE et surface ; quatre PNG décodés par Pillow, puis
inspectés visuellement. Contrôle du tirage et des bornes de coordonnées, chaîne
de carte sérialisée, infobulles, colonnes absentes. Prédictions
comparées aux résultats exacts de quatre exemples de développement sauvegardés ;
formulaire réel, zone H3, neuf, avertissement hors domaine ; six types de saisies
invalides ; données, modèles, colonnes et fichier vide gérés.

`verify_final_models.py` passe : empreintes du CSV, métadonnées, partitions,
modèles anciens et finaux, protocole, résultats et prédictions sauvegardées.
Les résultats sont recalculés depuis les prédictions figées, sans réévaluation
du réservé. Compilation, compatibilité des dépendances et contrôle des espaces
Git réussis. Le serveur local répond `200 ok` à `/_stcore/health`.

## Limite de la vérification visuelle de l'application

L'accès navigateur intégré était indisponible. Computer Use a ensuite arrêté
l'accès à Chrome car il ne pouvait pas déterminer l'URL courante avec assez
de certitude pour appliquer ses règles. Aucun contournement n'a été tenté.
Les pages ont été testées avec Streamlit AppTest, les PNG inspectés visuellement
et la structure carte vérifiée, mais **le rendu WebGL, les gestes de souris et
le téléchargement par clic dans Chrome n'ont pas pu être confirmés visuellement**.
Les octets PNG/CSV produits et la présence des boutons d'export sont contrôlés.

## Corrections des infobulles et du fond de carte

Après cette première livraison, l'utilisateur a confirmé ses contrôles manuels :
pages, filtre Rhône, export PNG, export CSV de 6 076 lignes, carte et prédiction.
Deux anomalies de carte étaient signalées et sont corrigées :

- Infobulles en `tooltip.text`, avec les libellés originaux, sans pré-échappement
  HTML. Les apostrophes et accents de `Marcy-l'Étoile` sont conservés. Un texte
  contenant des balises reste affiché comme texte, sans interprétation HTML.
- Sans fond, `map_provider=None` et absence d'argument `map_style` produisent
  la sentinelle PyDeck `__MAP_STYLE__`. Streamlit 1.66.1 reconnaît cette valeur
  et ne monte pas son fond de carte. L'ancien `map_style=None` faisait omettre
  la propriété JSON et déclenchait le retour automatique de CARTO.
  Le mode coché conserve l'URL explicite CARTO ; l'identifiant de couche
  `logements` reste stable et les marqueurs sont identiques dans les deux modes.

Contrats vérifiés dans le code de la version installée, également consultable
dans [useDeckGl.tsx](https://github.com/streamlit/streamlit/blob/1.66.1/frontend/lib/src/components/elements/DeckGlJsonChart/useDeckGl.tsx)
et [mapShell.ts](https://github.com/streamlit/streamlit/blob/1.66.1/frontend/lib/src/components/elements/DeckGlJsonChart/utils/mapShell.ts).
Le mode texte est décrit dans la [documentation PyDeck](https://deckgl.readthedocs.io/en/latest/tooltip.html).

Deux tests de régression ajoutés : apostrophes, accents et balises en texte brut ;
cycle décoché → coché → décoché dans Streamlit, contrôle du JSON réellement
transmis et conservation à l'identique des 5 000 marqueurs. Le contrat sans fond
exige la sentinelle explicite : une propriété omise ne suffit plus à passer le test.
L'accès navigateur automatisé reste indisponible : le rendu visuel de ces deux
corrections n'a pas été revérifié dans Chrome par l'agent.

L'utilisateur a ensuite confirmé manuellement dans le navigateur les deux
corrections : apostrophes lisibles dans les infobulles et fond CARTO réellement
retiré lorsque la case est décochée, avec conservation des marqueurs.

Après corrections : **19 tests réussis** (`19 passed`), contrôle d'intégrité des
données et modèles réussi, compilation Python et `git diff --check` réussis.
Aucune dépendance modifiée, aucun entraînement, push ou déploiement.

## Lancement

```powershell
cd C:\Users\mouni\Documents\App_Enedis
.\.venv-app\Scripts\python.exe -m streamlit run home.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Ouvrir http://127.0.0.1:8501. Arrêter avec Ctrl+C. Aucun déploiement, push,
fusion ou fonctionnalité Expert n'a été effectué. Modifications laissées locales.
