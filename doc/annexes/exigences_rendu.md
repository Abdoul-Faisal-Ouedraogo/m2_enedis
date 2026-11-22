# Exigences connues et points ouverts

Le seul PDF du dépôt est un référentiel de zones climatiques. Aucun document
contenant le sujet complet ou sa grille officielle n'a été trouvé. Cette matrice
couvre donc les exigences exprimées dans la conversation, sans certifier une
conformité exhaustive à un sujet non fourni.

Traçabilité : Issues [#21](https://github.com/Abdoul-Faisal-Ouedraogo/App_Enedis/issues/21)
(Docker), [#22](https://github.com/Abdoul-Faisal-Ouedraogo/App_Enedis/issues/22)
(données), [#23](https://github.com/Abdoul-Faisal-Ouedraogo/App_Enedis/issues/23)
(modèles), [#24](https://github.com/Abdoul-Faisal-Ouedraogo/App_Enedis/issues/24)
(API), [#25](https://github.com/Abdoul-Faisal-Ouedraogo/App_Enedis/issues/25)
(rendu). Branches locales empilées, sans fusion ; la version cumulative est sur
`feat/25-rendu-final-expert`.

| Exigence | Réalisé et vérifié localement | Restant ou limite |
|---|---|---|
| Standard/Intermédiaire | Quatre pages, filtres, indicateurs, quatre graphiques, carte, prédictions et exports testés | Petit écran et Exploration après refonte non confirmés visuellement |
| Refonte/carte | Design, marge selon dimensions, recentrage et caméra stable testés | Derniers gestes caméra à confirmer en navigateur |
| Docker | Image construite ; deux services sains ; pages, prédiction, commune, exports et empreintes testés dans l'image ; montages RO et utilisateur non root vérifiés | Ports nominaux occupés préservés ; essais réels sur 18501/18000 via compose.test.yaml |
| Actualisation | Client ADEME réutilisé, tests simulés ; collecte réelle de 20 DPE confirmée par l'utilisateur et auditée en lecture seule : 5 conservés, 15 rejets expliqués | Version réelle préparée, non activée ; aucune nouvelle collecte pendant le correctif #26 |
| Réentraînement | Deux modèles, protocole temporel/groupes, paramètres figés, deux threads, journal, versions, activation et retour arrière testés | Tests seulement 36 lignes/deux arbres ; aucun entraînement complet de test. Réservé depuis 2025 non appris |
| API | Santé, validation sept champs, unités/version, même prédiction ; tests et HTTP local/conteneur réels | Accès distant non configuré, volontairement |
| Préservation | Empreintes originales vérifiées ; nouveaux fichiers dans runtime ignoré ; autres scripts conservés | Sauvegarder séparément le volume des versions avant toute migration |
| Documentation | Guides utilisateur/technique de deux pages et rapport ML de cinq pages après rendu ; schéma Draw.io XML éditable | Ouverture du schéma dans Draw.io non confirmée visuellement |
| Vidéo | Scénario chronométré 4 min 50 | Captation, montage et publication non réalisés ; publication non autorisée |
| Futur déploiement | Image, services, variables, santé, dépendances et notes de préparation | Déploiement interdit dans ce travail ; authentification et exposition distante à étudier avant autorisation |
| Sujet complet | Exigences de cette demande couvertes par sources/tests et matrice | Obtenir le sujet/grille pour vérifier les critères non disponibles |

Les validations manuelles de l'application antérieure (pages, Rhône, exports,
carte, prédiction et correction des apostrophes/fond) sont consignées dans les
bilans existants ; elles ne confirment pas les nouveaux parcours Expert ni la
présentation remaniée d'Exploration. Les PDF de contrôle sont inspectés par l'agent.

Bilan Expert avant le correctif #26 : **81 tests réussis**, compatibilité des dépendances et compilation
vérifiées ; smoke-test hors Docker puis dans l'image, requêtes HTTP réelles aux
deux API locales de test. L'image sans volumes ne contient aucun CSV, secret ou
environnement ; 46 fichiers code/références/modèles comparés à l'hôte sont identiques.
Les empreintes des CSV bruts/préparés, métadonnées, références et modèles initiaux
sont inchangées. Aucune collecte réelle et aucun entraînement complet de test.
Un avertissement de dépréciation du client HTTP de test est non bloquant.

Correctif #26 : audit en lecture seule du lot réel Rhône, motifs de rejet et profil
IQR initial figé, sans modifier la version préparée, les fichiers initiaux ou les
modèles. Les vérifications ciblées de ce correctif excluent les tests qui lancent
un entraînement ou une activation ; aucun nouveau fit n'est exécuté. **86 tests
réussis** (huit fichiers de tests ciblés), compilation et empreintes modèles
vérifiées. Image reconstruite et bilan réel testé par AppTest dans un conteneur
éphémère, volume en lecture seule : 20 / 5 / 0 / 0 / 15, motifs 14 + 1 et JSON
replié. Les services utilisateur existants n'ont pas été recréés ; ils utilisent
encore leur image précédente. Guides 2 + 2 pages et rapport 5 pages rendus ;
pages modifiées inspectées. Cette vérification automatisée ne remplace pas un
contrôle visuel de l'interface dans un navigateur.
