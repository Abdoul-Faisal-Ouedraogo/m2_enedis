# Lot Rhône : causes des 15 rejets et préparation stable

Issue #26, 30 octobre 2026. Lot `d-a95f417758754e52b8da4c41a89b7100`,
reçu le 30/10/2026 à 16:34 UTC et conservé dans le volume Docker local.
Analyse exclusivement en lecture seule ; aucune nouvelle collecte, activation
ou exécution d'entraînement. Statut inchangé : préparé, données actives initiales,
modèles actifs `final_geo_v1`. Les empreintes de tous les fichiers du volume ont
été comparées avant/après l'audit et sont identiques.

## Motifs précis et effectifs

Le bilan est reproduit sur les réponses reçues, avec les règles historiques et
l'instant de préparation de la version. Les identifiants des cinq diagnostics
admis sont comparés à ceux de ses métadonnées, pas seulement leur nombre.

| Motif principal, sans double comptage | Effectif |
|---|---|
| Année de construction absente : âge 2026 non calculable | 14 |
| Surface habitable du logement absente, sur une ligne dont l'année est connue | 1 |
| Rejets par IQR coût ou surface | 0 |
| Autres rejets, doublons ou diagnostics remplacés | 0 |
| Total rejeté | 15 |

La ligne du deuxième groupe est un immeuble : son nombre de niveaux est aussi
absent. Une autre ligne, déjà comptée parmi les 14 années absentes, manque également
de surface et de niveaux. Les contrôles non exclusifs trouvent donc 14 années,
2 surfaces et 2 nombres de niveaux manquants ; **ces nombres ne s'additionnent pas**.
L'audit garde les motifs secondaires, mais le tableau principal ne compte chaque
ligne qu'une fois, selon l'ordre des contrôles.

Les cinq autres diagnostics passent tous les contrôles. Pour l'existant, aucune
année n'est inventée à partir d'une période de construction. La surface d'un
immeuble entier ne remplace pas la surface du logement attendue par le modèle.
Le bilan reste : 20 reçus, 5 conservés, 0 doublon, 0 remplacé et 15 rejetés.

## Pourquoi changer les IQR malgré zéro rejet IQR dans ce lot ?

Après les champs obligatoires, les anciens IQR ne portent plus que sur **5 lignes**.
Les bornes obtenues sont 531,25 à 1 635,65 pour le coût des cinq usages et 14,85
à 100,85 m² pour la surface. Une même observation peut être admise seule et rejetée
si elle est accompagnée d'autres observations. Par exemple, un coût de 2 000 est
accepté seul ; avec quatre coûts de 1 000, Q1 = Q3 = 1 000 et l'IQR nul le rejette.
Le résultat dépend alors du volume demandé, de la pagination ou du découpage du lot.

## Profil fixe, issu des sources initiales

`config/preparation_initial_geo_v1.json` fige les bornes après reproduction de
l'ordre du notebook initial : année connue et âge non négatif, coût connu,
IQR coût, puis IQR surface. Les deux CSV bruts et le CSV préparé ont été vérifiés
par leurs empreintes. Ils ont seulement été lus. Aucun quantile n'est recalculé
sur les 20 nouvelles lignes ni sur un jeu préparé déjà tronqué.

| Champ | Q1 initial | Q3 initial | Borne basse | Borne haute |
|---|---|---|---|---|
| Coût des cinq usages | 455,20 | 1 481,00 | -1 083,50 | 3 019,70 |
| Surface habitable (m²) | 49,00 | 95,00 | -20,00 | 164,00 |

Les bornes statistiques sont inclusives ; les contrôles métier continuent de
refuser notamment une surface nulle ou négative. Les 616 057 lignes initiales
respectent ces bornes. Les futurs lots utilisent le même profil, quel que soit
leur nombre ou leur composition. Le profil et les motifs sont consignés dans
chaque nouvelle version ; le détail par ligne est sauvegardé dans `audit.json`.

Appliquée en simulation au lot Rhône enregistré, cette politique conserve
également 5 lignes et en rejette 15, pour les mêmes champs manquants. Elle ne
répare pas des informations absentes. Le lot existant et son manifeste ne sont
pas réécrits. L'interface explique ses rejets en rejouant ses anciennes règles
en mémoire et affiche séparément cette comparaison avec le profil fixe.

Limites : les seuils initiaux étaient calculés globalement, pas sur l'entraînement
seul. Le correctif stabilise l'admission des nouveaux lots ; il n'efface pas cette
limite méthodologique et ne change aucun score ML. Les coûts et tarifs peuvent
évoluer : une future révision nécessitera un nouveau profil explicite et une
validation dédiée, jamais une adaptation automatique à chaque lot.

## Interface et contrôle

Cinq indicateurs lisibles : reçus, conservés, doublons, remplacés et rejetés.
Reçus = conservés + doublons + rejetés ; les doublons ne sont pas recomptés dans
les rejets. Remplacés concerne les anciens diagnostics écartés de la copie de
base, sans suppression des originaux. Le tableau donne les raisons et effectifs ;
le JSON est dépliable. Même un lot intégralement rejeté expose son bilan sans
créer de version. Le menu indique désormais « collecte et entraînement sur
confirmation », sans prétendre que ces fonctions sont absentes.

Reproduire l'audit sans écriture du volume :

```powershell
.\.venv-app\Scripts\python.exe -X utf8 scripts/audit_prepared_batch.py d-a95f417758754e52b8da4c41a89b7100 --docker-volume habitat-energie-local_expert-runtime
```

Le script monte volume, sources et références en lecture seule et vérifie que le
volume est inchangé. Le script de fabrication du profil refuse d'écraser un profil
déjà figé ; il n'est jamais appelé au lancement ou à la collecte. Les validations
visuelles petit écran et Exploration après refonte restent non confirmées.

Contrôles du correctif : 86 tests ciblés réussis, compilation, empreintes des
modèles et données de référence, construction Docker et bilan réel via AppTest
dans l'image reconstruite, volume monté en lecture seule. Les services déjà
lancés n'ont pas été redémarrés. Pour charger le correctif avec les ports de test
actuellement utilisés :

```powershell
docker compose -f compose.yaml -f compose.test.yaml up -d --no-deps application
```

Cette commande recrée seulement le service application avec l'image reconstruite,
sans activer de données ni entraîner de modèle. Elle reste à exécuter par
l'utilisateur ; la vérification actuelle a utilisé un conteneur éphémère séparé.
