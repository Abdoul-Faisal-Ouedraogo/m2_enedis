# Audit local du 29 octobre 2026

**Dernier état :** les modèles finaux corrigés sont entraînés, sauvegardés et
vérifiés. Le [rapport final](modeles_finaux_2026-10-29.md) remplace les états de
préparation ci-dessous pour les modèles et résultats courants.

État initial et premières corrections. **Mise à jour :** les corrections
géographiques de Nouhayla sont maintenant intégrées, le CSV initial est
sauvegardé, et un découpage chronologique par groupes est préparé sans
entraînement. Les scores ci-dessous concernent uniquement l'ancienne version.
Consulter le [rapport à jour](preparation_validation_2026-10-29.md) pour les
changements de données et le plan de comparaison.

Branche : `fix/coherence-modeles-ml`. Consignes lues : `CONTRIBUTING.md` et README.
Aucun AGENTS.md trouvé dans le dépôt ou ses parents. Les quatre modifications
présentes au démarrage ont été conservées : notebooks 1 et 3, pipeline et
métadonnées de consommation. Aucun reset, commit ou push.

## Ce qui fonctionne

- Le CSV préparé compte réellement 616 057 lignes, 16 colonnes, 94 départements.
- Les sept caractéristiques ML et les deux cibles sont complètes. Deux codes
  postaux manquent, sans incidence sur les entrées ML.
- Le pipeline de régression sauvegardé reproduit les résultats annoncés sur le
  découpage graine 42, 70/30 : MAE 2121,4521188838185 ; RMSE
  3954,6997277004607 ; R² 0,6932078583487365. Aucun entraînement de régression.
- Le coût, le DPE et les consommations détaillées ne sont pas des entrées de
  la régression. Sa cible est la consommation finale totale annuelle.

## Corrections réalisées

- Détection de la racine depuis la racine du dépôt ou le dossier des notebooks.
- Suppression des chemins PC personnels des notebooks courants.
- Régression : commentaire de cible corrigé ; recherches MLflow et sauvegardes
  désactivées par défaut ; modèle rechargé au lieu d'être réentraîné.
  La lecture du CSV passe par les mêmes contrôles que la classification.
  Les comparaisons MLflow facultatives sont isolées par exécution, cible et
  empreinte du CSV pour ne plus mélanger les anciens essais avec les nouveaux.
- Préparation : année de référence fixée à 2026, table des communes réutilisée
  localement, agrégations API finales protégées par `EXTRACTION`.
- Classification : ancien notebook archivé intégralement. La version courante
  utilise le CSV commun et un pipeline unique. Elle ne dépend plus du CSV Rhône
  absent, ni des résultats XGBoost/KNN, ni de la variable ambiguë `y_pred`.
- Un seul entraînement de classification commune, borné et sans recherche de
  paramètres, a produit accuracy 0,5795809932 et F1 macro 0,4759462742.
  Le coût a été retiré des entrées, pour permettre une estimation à partir des
  caractéristiques du logement et éviter ce proxy énergétique.
- Modèle commun sauvegardé sous un nouveau nom ; vérification de toutes les
  prédictions du test après rechargement. Ancien modèle du Rhône inchangé.
- Installation ML/notebooks alignée entre `pyproject.toml`, `uv.lock` et son
  export `requirements.txt`, dans `.venv-ml` sans modifier `.venv`.
  `requirements-notebooks.txt` est un alias du même export.
- `setup_env.ps1` prépare uniquement l'environnement ML et s'arrête. Il ne
  lance plus Streamlit. Les dépendances des expériences historiques sont
  conservées comme option, séparées du parcours courant.
- L'enrichissement Rhône s'arrête avec une liste explicite des fichiers absents
  au lieu de substituer un autre périmètre ou d'afficher une erreur CSV ambiguë.

## Source commune et enrichissement

`output/cleaned_data.csv` est la seule source commune immédiatement disponible.
Elle contient déjà les sept caractéristiques, l'altitude et les zones H1/H2/H3.
Le notebook de Nouhayla travaille sur 13 481 lignes du Rhône d'après ses sorties
historiques. Les CSV nettoyé/enrichi du Rhône et `climate_zones.csv` sont absents.
Il serait incorrect de substituer silencieusement ce petit périmètre au CSV
commun ou de mélanger H1 et H1c avec les encodeurs actuels.

Ses corrections des communes de Lyon et Pierre-Bénite sont pertinentes à étudier
pour une prochaine version de la préparation. Elles n'ont pas été appliquées
au CSV actuel : changer les altitudes invaliderait la reproduction exacte des
scores et imposerait de revalider les deux modèles. Aucun brut n'a été retéléchargé.

## Points à améliorer ensuite

- Classification : F1 macro modeste et résultats par classe à examiner avant
  toute optimisation. Aucune promesse de performance fondée sur les anciens
  scores du Rhône.
- Régression : le test a servi à la comparaison des modèles. Prévoir un nouveau
  test final, idéalement séparé par période ou territoire.
- L'âge des logements neufs a été imputé à zéro dans la préparation historique.
  Le CSV ne contient plus de numéro DPE ni date de réception : impossible de
  vérifier complètement les doublons de bâtiments et la fuite entre périodes.
- Les filtres IQR sur coût/surface et le regroupement des énergies sont calculés
  en amont de la séparation train/test. L'évaluation est donc conditionnelle au
  CSV nettoyé et ne valide pas toute la chaîne sur des données brutes nouvelles.
- L'altitude manquante est remplacée par la moyenne départementale ; la zone
  climatique est simplifiée. Ces conventions font partie du contrat des modèles.
- `src/processing/data_cleaner.py` est une autre chaîne, distincte du notebook 1.
  Elle attend une table climatique absente et certaines colonnes absentes du
  CSV commun. Elle n'est pas utilisée par les modèles courants. Son unification
  complète nécessiterait les références géographiques manquantes et une nouvelle
  version des données ; elle ne doit pas être présentée comme une alternative
  interchangeable au notebook 1.
- Les notebooks historiques gardent leurs sorties et chemins anciens dans
  l'archive pour préserver le travail du groupe ; ils ne sont pas le parcours
  d'exécution courant.

## Vérifications effectuées

- Les deux notebooks ML exécutés jusqu'au bout avec appels réseau, `Pipeline.fit`
  et `joblib.dump` explicitement interdits pendant le contrôle.
- Vérification des prédictions rechargées et des métriques de classification.
- Installation des dépendances verrouillées dans un environnement neuf
  `.venv-ml`, dédié aux notebooks et modèles.
- Vérification des modèles sauvegardés et exécution des deux notebooks ML dans
  cet environnement. Aucun nouvel entraînement à la finalisation des prérequis.
- Syntaxe Python des quatre notebooks courants vérifiée, compilation des modules
  et `git diff --check` réussis.
- Préparation rejouée depuis les deux bruts locaux et la table des communes.
  Pour limiter la mémoire, seules les colonnes réellement utilisées par le
  nettoyage sont lues ; les tableaux exploratoires sur les colonnes exclues
  ne sont pas reproduits. Le calcul de nettoyage et d'enrichissement du notebook
  est exécuté. L'export est intercepté et ses 616 057 lignes/16 colonnes sont
  comparées au CSV existant, sans réseau et sans l'écraser. Égalité des valeurs
  avec tolérance numérique rtol 1e-12 / atol 1e-9 pour l'aller-retour CSV.
- L'enrichissement Rhône n'a pas été exécuté faute de ses entrées ; ses sorties
  historiques ne sont donc pas présentées comme vérifiées sur ce poste.
- Pas de suite pytest préexistante ; les scripts de vérification sont conservés
  dans `scripts/verify_notebooks.py` et `scripts/verify_preparation.py`.

## Périmètre arrêté avant l'application

Des fichiers Streamlit ont été créés lors du tour précédent, avant la précision
de l'utilisateur. Ils sont conservés sans développement, lancement ou nouveau
test pendant la finalisation des prérequis. Le README et le script d'installation
sont recentrés sur les notebooks ML. Le début de l'application attend une
autorisation séparée.

Un instantané des notebooks, instructions et dépendances avant cette
finalisation est conservé localement dans `output/audit_avant_finalisation_ml/`.
Les modèles, le CSV commun et le travail de Nouhayla ont été préservés.
