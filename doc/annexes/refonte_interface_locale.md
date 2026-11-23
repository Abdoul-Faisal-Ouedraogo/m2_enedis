# Refonte locale — 30 octobre 2026

Issue [#20](https://github.com/Abdoul-Faisal-Ouedraogo/App_Enedis/issues/20),
assignée à mbekkar. Branche `feat/20-refonte-interface` créée à partir de
`feat/19-application-streamlit`, sans fusion ni modification d'historique.
`CONTRIBUTING.md` lu avant les changements. À l'ouverture, les fichiers suivis
étaient propres ; les quatre scripts locaux non suivis restent préservés.

## Présentation

- Thème blanc cassé et vert profond, base typographique 18 px, palette DPE A-G,
  indicateurs agrandis, cartes et groupes de saisie natifs. CSS limité aux
  couleurs, espaces, indicateurs et échelle DPE ; aucun ciblage de classes générées.
  Les colonnes Streamlit s'empilent sur petit écran ; la carte utilise la largeur
  disponible. Le rendu sur petit écran n'a pas pu être confirmé visuellement.
- Navigation latérale avec icônes et sélection native visible. Accueil court,
  deux accès directs, illustration, chiffres clés et cartes de parcours. Sources,
  méthode, colonnes techniques et crédits restent dans les sections dépliables.
- Exploration : bandeau des filtres actifs, remise à zéro, titres français pour
  toutes les colonnes, graphiques agrandis. Les quatre types de graphiques et
  leurs exports PNG, le tableau et l'export CSV complet filtré sont conservés.
- Carte de 700 px avec légende A-G, infobulles en texte brut, effectifs et exclusion
  des coordonnées invalides. Cadrage Web Mercator calculé sur toutes les coordonnées
  admissibles de la sélection, avant échantillonnage, avec marge pour les petits
  écrans ; zoom borné pour une seule position. Activation/désactivation CARTO
  conservée avec la sentinelle explicite sans fond, et couche de marqueurs stable.
- Prédiction : trois groupes (localisation, logement, environnement), aides courtes,
  résultat à côté du profil, échelle DPE marquant la lettre et limites visibles.
  Métriques et limites détaillées dans une section dépliable.

## Comparaison et gestion des résultats

Deux groupes de saisie indépendants et deux boutons de calcul, avec résultats
côte à côte. Les champs sont des composants natifs réactifs hors `st.form` :
une saisie validée déclenche un rerun et invalide le résultat et l'export concernés.
Cette organisation évite les champs modifiés côté navigateur mais non encore
transmis, qui laisseraient un ancien résultat visible dans un formulaire différé.

Chaque résultat conserve ses valeurs exactes, la localisation/provenance, la date
du calcul Europe/Paris et la version des modèles. La signature inclut les entrées,
la sélection géographique et la version. Une modification retire le résultat et
invite à recalculer ; revenir aux anciennes valeurs ne ressuscite pas un résultat
déjà invalidé. Le second logement reste indépendant. L'écart B moins A et le PDF
commun n'apparaissent que lorsque les deux résultats sont à jour. Avertissement
explicite : l'écart estimé ne prouve pas l'effet d'une rénovation.

## Références géographiques

`src/app_geography.py` lit uniquement le référentiel communal local existant
(34 935 lignes), sans téléchargement. Les listes H1/H2/H3 réellement utilisées
dans le notebook de préparation sont extraites par AST/littéraux : aucune cellule
n'est exécutée, aucune sous-zone inventée. Une liste ambiguë ou absente bloque
l'aide, sans bloquer la saisie manuelle.

La règle d'altitude est celle de la préparation : jointure communale après
correction du code (69381–69389 → 69123 pour Lyon ; 69152 → 69149 pour
Pierre-Bénite). Lyon donne 237 m, Oullins-Pierre-Bénite 194 m, zone H1. Sans
altitude communale finie, remplacement par la moyenne des altitudes des communes
du département dans le référentiel, sans pondération par logements ou population.
La provenance de chaque proposition et du PDF est explicite. La sélection de
commune n'utilise que des codes présents dans le référentiel ; les anciens codes
de jointure restent pris en charge par le service et ses tests de régression.

La Corse est codée 2A/2B dans le référentiel mais 20 dans les listes du notebook :
l'aide ne fait aucune conversion supposée. Une zone absente reste indisponible
dans la proposition ; la saisie manuelle H1/H2/H3 reste possible.

## PDF

`src/app_pdf.py` utilise ReportLab, en mémoire, sans service ni navigateur : une
page pour un logement et deux pages pour une comparaison (une par logement).
Sept caractéristiques, unités, consommation finale en kWh/an, lettre provenant
du classificateur distinct, échelle A-G, date du calcul, version `final_geo_v1`,
localisation et origine de l'altitude, limites et pagination. Les données textuelles
sont échappées pour le moteur de paragraphes. L'export utilise le résultat figé
et n'appelle pas les modèles.

Seule dépendance application ajoutée : `reportlab==5.1.0`. Dépendance de test :
`pypdf==6.21.4`. Installation uniquement dans `.venv-app`, environnement ML et
verrouillage ML inchangés. Exemples de contrôle dans `output/pdf/`, ignorés par Git.

## Contrôles

```powershell
.\.venv-app\Scripts\python.exe -X utf8 -m pytest -q
.\.venv-app\Scripts\python.exe -m compileall -q home.py src scripts tests
.\.venv-app\Scripts\python.exe scripts/verify_final_models.py
uv pip check --python .venv-app/Scripts/python.exe
git diff --check
```

Résultat avant correction du cadrage : **27 tests réussis**. Le script `scripts/verify_app.py` exécute
désormais tout le dossier de tests, y compris la refonte.

La suite contient 27 tests, incluant les 19 contrôles précédents. Les nouveaux
cas couvrent les accès depuis l'accueil, les résultats et PDF retirés après une
modification, la comparaison indépendante et l'écart, la sélection d'une commune,
l'application de son altitude et zone, la reprise manuelle, le changement de
département, la référence absente, les corrections Lyon/Pierre-Bénite, le repli
départemental, l'absence de zone non inventée, le cadrage et le contenu des PDF.
Les tests existants conservent les filtres, les exports PNG/CSV, les quatre pages,
les prédictions réelles, les coordonnées et le cycle de bascule CARTO.

Intégrité contrôlée : CSV préparé, métadonnées, partitions, prédictions figées,
modèles finaux et anciens inchangés. Les empreintes des trois CSV sources, dont
le référentiel communal, correspondent également au manifeste existant. Aucun
entraînement, aucune nouvelle prédiction sur le lot réservé.

Les deux PDF exemples ont été rendus avec Poppler et leurs trois pages inspectées
visuellement après le dernier ajustement typographique : titres, unités, accents,
tableaux, échelle et limites lisibles, sans chevauchement ni débordement.
Le navigateur automatisé reste indisponible (`browser access host is unavailable`).
Les pages et interactions sont testées par Streamlit AppTest. Ces tests ne
remplacent pas les vérifications visuelles manuelles ci-dessous.

### Vérifications manuelles réalisées

- Avant la refonte, l'utilisateur a confirmé dans le navigateur les quatre pages,
  le filtre Rhône, un export PNG, un export CSV de 6 076 lignes, la carte et la
  prédiction. Il a aussi confirmé les corrections des apostrophes et de la
  désactivation du fond CARTO. Ces validations portent sur la version précédente,
  pas sur la présentation remaniée de la page Exploration.
- Après la refonte, l'utilisateur a inspecté la carte et signalé le cadrage trop
  éloigné sur le Rhône. Ce constat a conduit à la correction décrite ci-dessous ;
  il ne constitue pas une validation visuelle du cadrage corrigé.
- Les PDF de la refonte ont été rendus et leurs trois pages inspectées par l'agent,
  avec vérification de la lisibilité et de l'absence de débordement.

### Vérifications manuelles restant à faire

- **Petit écran** : vérifier l'empilement des colonnes, la navigation, la lisibilité,
  les formulaires, l'échelle DPE et la carte sur les quatre pages. Les calculs sur
  des dimensions mobiles sont testés automatiquement, sans validation visuelle.
- **Page Exploration après refonte** : vérifier le rendu des indicateurs, le
  bandeau de filtres, les quatre graphiques, le tableau, la remise à zéro et les
  téléchargements PNG/CSV. Les tests automatisés réussissent ; les contrôles
  manuels antérieurs ne valident pas cette nouvelle présentation.
- **Carte après la dernière correction** : confirmer le cadrage France/Rhône/
  plusieurs départements, le bouton de recentrage et la conservation du zoom
  manuel lors des changements de fond et de limite des marqueurs.
- Les nouveaux parcours d'estimation, comparaison, aide communale et export PDF
  sont couverts par les tests ; aucune confirmation manuelle supplémentaire de
  ces parcours dans le navigateur n'est consignée dans cette conversation.

## Correction du cadrage et conservation de la caméra

Le cadrage précédent utilisait un carré fixe de 320 pixels pour les deux axes,
ce qui laissait beaucoup d'espace autour du Rhône dans une carte de 700 pixels
de haut. Le calcul utilise maintenant séparément la largeur réellement mesurée
dans le navigateur et la hauteur de 700 pixels : zoom horizontal et vertical
en projection Web Mercator, puis minimum des deux. Marge de 8 % de chaque côté.
Toutes les coordonnées admissibles de la sélection sont prises en compte avant
l'échantillonnage. Une position unique est centrée avec un zoom borné à 14 ; une
sélection vide ne crée pas de carte.

Un petit composant local Streamlit v2 mesure uniquement sa propre largeur avec
ResizeObserver, sans dépendance ni ressource distante. Première passe serveur :
1 000 pixels provisoires, corrigés une fois par la première mesure réelle.
Les mesures sont dédupliquées et temporisées pour éviter une boucle de reruns.
Voir [la documentation du dimensionnement Streamlit v2](https://docs.streamlit.io/develop/concepts/custom-components/components-v2/mount).

Le cadrage initial et la clé de la carte native restent stables si la sélection
est inchangée, même si le nombre de marqueurs ou le fond CARTO change : la vue
manuelle du navigateur est conservée. L'identité de sélection dépend des lignes
et coordonnées filtrées, indépendamment de leur ordre, jamais de l'échantillon
affiché. Une nouvelle sélection ou le bouton **Recentrer sur la sélection**
renouvelle la clé et le cadrage, même si l'emprise calculée est identique.
Un redimensionnement seul conserve aussi le zoom manuel ; ses dimensions à jour
servent au prochain recentrage ou changement de sélection. La carte utilise une
clé native stable avec gestion de sélection Streamlit, ce qui permet de conserver
son état entre reruns et d'identifier explicitement une demande de recentrage.
Ce comportement de remontage par clé est confirmé dans le
[rendu natif Streamlit 1.66.1](https://github.com/streamlit/streamlit/blob/1.66.1/frontend/lib/src/components/core/Block/ElementNodeRenderer.tsx).

Les 15 tests ajoutés couvrent France entière, Rhône seul et plusieurs départements
sur trois dimensions (ordinateur, mobile, carte moins haute), présence de tous
les points dans la marge, occupation de 84 % d'au moins un axe, point unique et
sélection vide. Ils vérifient les clés/cadrages transmis par Streamlit lorsque
les filtres, le fond et la limite de marqueurs changent, le bouton de recentrage,
la première mesure, le redimensionnement et le fonctionnement dédupliqué du
composant JavaScript. Sur les données locales, pour 1 200 × 700 pixels : France
zoom 5,02 ; Rhône zoom 8,57, centré vers 45,84349° N / 4,70444° E.
L'état émis et la logique de conservation sont testés ; faute d'accès navigateur,
les gestes réels de zoom/déplacement et leur conservation restent à confirmer
visuellement après cette correction.

Résultat après correction : **42 tests réussis** (27 précédents + 15 de cadrage),
compilation et contrôles Git réussis, intégrité des données et modèles vérifiée.
Aucune dépendance ajoutée.

## Lancement

```powershell
cd C:\Users\mouni\Documents\App_Enedis
.\.venv-app\Scripts\python.exe -m streamlit run home.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Ouvrir http://127.0.0.1:8501. Installation des dépendances mises à jour si besoin :
`uv pip install --python .venv-app/Scripts/python.exe -r requirements-app.txt`.
La livraison est enregistrée sur `feat/20-refonte-interface` et sa sauvegarde sur
`origin` est autorisée, sans force. Aucune fusion dans `main`, aucun déploiement
et aucune nouvelle fonctionnalité Expert. Les données, PDF générés et environnements
locaux restent hors du commit ; les autres travaux locaux sont préservés.
