# Scénario vidéo - durée cible 4 min 50

Préparer les CSV locaux et ouvrir l'application avant l'enregistrement. Ne pas
lancer un entraînement complet pour filmer ; utiliser une version de démonstration
sur petit jeu, clairement étiquetée, ou montrer le parcours sans déclencher le fit.
Ne pas afficher de secrets ou de chemins personnels. Aucune vidéo n'est publiée ici.

| Temps | Écran et action | Commentaire proposé |
|---|---|---|
| 0:00-0:30 | Terminal, fichiers requis et commande locale | Projet DPE ADEME, données locales et modèles contrôlés. Installation séparée du ML. Image Docker construite et testée ; expliquer les ports de test si les ports nominaux sont occupés. |
| 0:30-0:55 | Accueil, chiffres clés et sources | Un échantillon de 616 057 logements, sans représentativité nationale garantie. |
| 0:55-1:30 | Exploration, Rhône, surface, graphiques et CSV/PNG | Tous les indicateurs et exports suivent la sélection ; le tableau et le nuage affichent un nombre limité de lignes. |
| 1:30-2:00 | Carte, légende, infobulle, CARTO, recentrage | Les effectifs sont explicites. La carte suit les filtres et le zoom manuel est conservé entre les réglages d'affichage. Vérifier ce geste avant d'enregistrer. |
| 2:00-2:45 | Prédiction, commune Lyon, comparaison, PDF | Sept entrées, référence 2026, deux prédictions indépendantes. Modifier une saisie retire le résultat périmé. La différence ne prouve pas l'effet d'une rénovation. |
| 2:45-3:40 | Gestion : période, limite, bilan, validation et versions | Aucune collecte automatique. Une préparation n'active rien. L'entraînement est confirmé séparément, limité à deux threads ; les versions et erreurs sont conservées et le retour arrière est possible. Montrer des réponses simulées si la collecte réelle n'est pas vérifiée. |
| 3:40-4:15 | Terminal : /health et /predict, réponse JSON | Même chargeur que Streamlit, unités et version, refus des entrées invalides. Accès local uniquement. |
| 4:15-4:50 | Rapport et matrice des limites | Accuracy 55,41 %, MAE 1 814,68 kWh/an, difficultés sur l'ancien et F/G. Pas d'intervalle individuel. Indiquer les vérifications visuelles encore ouvertes et l'absence du sujet complet. |

Avant captation : vérifier les petits écrans et Exploration après refonte,
confirmer le cadrage final, lancer Docker si souhaité et tester sa construction.
Le scénario ne vaut pas preuve que ces contrôles ou la vidéo sont réalisés.
