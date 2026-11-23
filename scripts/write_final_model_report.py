"""Générer le rapport lisible depuis les résultats figés, sans calcul de prédiction."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "MLmodels/final_geo_v1"
result = json.loads((DIRECTORY / "results.json").read_text(encoding="utf-8"))
comparison = json.loads((DIRECTORY / "comparison_validation.json").read_text(encoding="utf-8"))
partitions = json.loads((DIRECTORY / "partition_distributions.json").read_text(encoding="utf-8"))


def number(value, digits=0):
    return f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")


def percentage(value):
    return number(100 * value, 2) + " %"


lines = ["# Modèles finaux — 29 octobre 2026", "",
    "Les cinq entraînements autorisés sont terminés : trois comparaisons de classification sur 60 000 lignes, puis deux modèles finaux sur 453 680 lignes. Chaque forêt contient 100 arbres. Les calculs sont limités à deux threads, sans grille ni recherche supplémentaire. Les anciens modèles et les travaux de Nouhayla sont conservés. Aucune application développée, aucun push.", "",
    "## Population et protocole", "",
    "| Partition | Lignes | Existant | Neuf | Part du neuf |",
    "|---|---:|---:|---:|---:|"]
for partition, entry in partitions.items():
    lines.append(f"| {partition} | {number(entry['rows'])} | {number(entry['sources'].get('existant', 0))} | {number(entry['sources'].get('neuf', 0))} | {percentage(entry['sources'].get('neuf', 0) / entry['rows'])} |")
lines += ["", "| Partition | A | B | C | D | E | F | G |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
for partition, entry in partitions.items():
    lines.append("| " + partition + " | " + " | ".join(number(entry["classes"].get(label, 0)) for label in "ABCDEFG") + " |")
lines += ["", "Les réceptions avant 2024 servent à l'entraînement, celles de 2024 à la validation, celles depuis 2025 au lot réservé. Les groupes BAN/immeuble/remplacement traversant les périodes sont exclus du protocole, pas supprimés du CSV. Les partitions ne partagent ni groupe ni identifiant vérifié.", "",
    "Pourquoi 91,7 % de neuf en validation ? Les bruts de 2024 contiennent déjà 79 257 DPE neufs contre 6 265 existants (92,7 % de neuf). Après nettoyage : 66 159 contre 5 082 (92,9 %). Après exclusions de groupes/dates : 50 648 contre 4 587 (91,7 %). Le découpage révèle donc surtout la composition temporelle différente des deux extractions. L'extraction historique demandait au maximum 5 000 lignes par département et par source, sans échantillonnage temporel représentatif. Ces taux ne décrivent pas le parc français. Aucune cause réglementaire du pic de janvier 2026 n'est supposée.", "",
    "Les distributions des classes réservées ont été établies après le gel des choix. Elles n'ont pas orienté la comparaison. Les 172 F et 53 G de validation sont peu nombreux ; il faut interpréter leurs résultats avec prudence.", "",
    "## Comparaison de classification — validation seulement", "",
    "| Candidat | Accuracy | F1 macro A–G | Accuracy existant | F1 macro existant | Accuracy neuf | F1 macro neuf |",
    "|---|---:|---:|---:|---:|---:|---:|"]
for model in comparison["models"]:
    lines.append("| " + model["name"] + " | " + " | ".join(percentage(v) for v in [model["accuracy"], model["f1_macro"], model["by_source"]["existant"]["accuracy"], model["by_source"]["existant"]["f1_macro"], model["by_source"]["neuf"]["accuracy"], model["by_source"]["neuf"]["f1_macro"]]) + " |")
lines += ["", f"Référence de validation : toujours prédire {comparison['baseline_class']}, classe majoritaire de l'échantillon d'entraînement. Accuracy {percentage(comparison['baseline_validation']['accuracy'])}, F1 macro {number(comparison['baseline_validation']['f1_macro'], 4)}.", "",
    f"Choix figé : **{comparison['selected_on_validation']}**, selon le F1 macro global de validation. Les modèles plus profonds n'améliorent pas ce critère ; le gain d'accuracy du modèle non pondéré ne justifie pas de changer le critère après coup. À capacité égale, la pondération améliore le F1 macro global. Aucun résultat réservé n'a servi à ce choix.", "",
    "Le F1 macro est calculé sur les sept classes fixes, même dans les sous-populations où certaines sont absentes ou très rares. Cela explique qu'une bonne accuracy du neuf ne corresponde pas forcément à un bon F1 macro.", "",
    "### F1 par classe en validation", "", "| Candidat / population | A | B | C | D | E | F | G |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
for model in comparison["models"]:
    for population, metrics in [("ensemble", model)] + list(model["by_source"].items()):
        lines.append("| " + model["name"] + " / " + population + " | " + " | ".join(percentage(metrics["report"][label]["f1-score"]) for label in "ABCDEFG") + " |")
lines += ["", "Précision, rappel, F1 et effectif pour chaque candidat/classe/population sont conservés dans comparison_validation.json et affichés dans le notebook de classification.", "",
    "## Modèles finaux et évaluation du lot réservé interne", "",
    "Après sélection, la classification est réentraînée sur entraînement + validation (453 680 lignes). La régression utilise sans recherche supplémentaire les réglages précédemment retenus : 100 arbres, profondeur 10, min_samples_split=20, min_samples_leaf=1, graine 42. Les deux pipelines utilisent les mêmes sept caractéristiques et deux threads. Les coûts, consommations détaillées, DPE et identifiants sont exclus des entrées.", "",
    "Les paramètres sont enregistrés dans frozen_protocol.json avant les entraînements finaux. Les modèles et leurs empreintes sont sauvegardés avant l'évaluation. Une seule paire de prédictions sur les 107 666 lignes réservées est produite, puis conservée. Aucune modification de paramètres ni aucun nouvel entraînement ne suit les résultats réservés.", "",
    "**Ce lot reste interne à des données déjà exploitées. Ce n'est pas une évaluation externe indépendante.**", "",
    "| Classification | Accuracy | F1 macro |", "|---|---:|---:|",
    f"| Modèle final | {percentage(result['classification']['accuracy'])} | {number(result['classification']['f1_macro'], 4)} |",
    f"| Toujours {result['baseline']['classification_majority']} | {percentage(result['baseline']['classification']['accuracy'])} | {number(result['baseline']['classification']['f1_macro'], 4)} |", "",
    "| Population réservée | Effectif | Accuracy DPE | F1 macro DPE | MAE kWh/an | RMSE kWh/an | R² |", "|---|---:|---:|---:|---:|---:|---:|"]
for population, values in [("ensemble", result)] + list(result["by_source"].items()):
    c, r = values["classification"], values["regression"]
    lines.append(f"| {population} | {number(c['rows'])} | {percentage(c['accuracy'])} | {number(c['f1_macro'], 4)} | {number(r['mae'], 2)} | {number(r['rmse'], 2)} | {number(r['r2'], 4)} |")
b = result["baseline"]["regression"]
lines += ["", f"Référence de régression : médiane constante des données d'entraînement + validation ({number(result['baseline']['regression_median_kwh'], 2)} kWh/an), MAE {number(b['mae'], 2)}, RMSE {number(b['rmse'], 2)}, R² {number(b['r2'], 4)} sur le réservé.", "",
    "### Classification réservée par classe et population", "", "| Population | DPE | Effectif | Précision | Rappel | F1 |", "|---|---|---:|---:|---:|---:|"]
for population, values in [("ensemble", result)] + list(result["by_source"].items()):
    for label in "ABCDEFG":
        metrics = values["classification"]["report"][label]
        lines.append(f"| {population} | {label} | {number(metrics['support'])} | {percentage(metrics['precision'])} | {percentage(metrics['recall'])} | {percentage(metrics['f1-score'])} |")
lines += ["", "### Régression réservée par classe DPE observée", "", "La classe DPE sert uniquement à décrire les erreurs, jamais de variable d'entrée.", "", "| DPE réel | Effectif | MAE kWh/an | RMSE kWh/an | R² |", "|---|---:|---:|---:|---:|"]
for label, metrics in result["regression_by_dpe"].items():
    lines.append(f"| {label} | {number(metrics['rows'])} | {number(metrics['mae'], 2)} | {number(metrics['rmse'], 2)} | {number(metrics['r2'], 4)} |")
lines += ["", "## Artefacts et contrôles", "",
    "Dans MLmodels/final_geo_v1/ : classification.joblib et regression.joblib ; classification_variables.json et regression_variables.json ; frozen_protocol.json ; split_plan.json ; comparison_validation.json ; results.json ; partition_distributions.json ; reload_check.json. MLmodels/final_models.json désigne cette version. Les anciens fichiers ne sont pas remplacés.", "",
    "Les pipelines, leurs cibles, ordre des variables, paramètres, versions de bibliothèques et empreintes SHA-256 sont conservés. Le rechargement reproduit les prédictions sur 32 exemples d'entraînement/validation. Les prédictions réservées détaillées restent dans output/final_geo_v1/reserved_predictions.csv, ignoré par Git. Les vérifications suivantes recalculent seulement les métriques de ces prédictions figées, sans nouvel appel aux modèles sur le réservé.", "",
    "Les deux notebooks courants affichent maintenant la version finale, sans entraînement. Leurs versions précédentes sont conservées intégralement dans archives/. Le notebook d'enrichissement de Nouhayla et les corrections intégrées dans la préparation sont conservés.", "",
    "## Reproduire sans réentraîner", "", "```powershell",
    ".\\.venv-ml\\Scripts\\python.exe scripts/verify_final_models.py",
    ".\\.venv-ml\\Scripts\\python.exe scripts/verify_notebooks.py",
    ".\\.venv-ml\\Scripts\\python.exe -m src.ml_workflow",
    "```", "",
    "Ces commandes contrôlent les artefacts et résultats sauvegardés, sans fit ni nouvelle prédiction réservée. La vérification complète demande les fichiers locaux CSV/métadonnées/affectations/prédictions dont les empreintes sont enregistrées. Le rechargement simple est disponible via src.final_model_loader.load_final_bundle().", "",
    "## Reproduire les entraînements dans une copie de travail séparée", "",
    "Conserver ce répertoire final et ses résultats. Dans une copie distincte du projet, installer requirements.txt dans .venv-ml et fournir les mêmes données corrigées, métadonnées et affectations. Le répertoire MLmodels/final_geo_v1 et le manifeste MLmodels/final_models.json ne doivent pas déjà exister dans cette copie de reproduction. Il n'est pas nécessaire de supprimer quoi que ce soit dans le projet original. Si nécessaire, régénérer le découpage avec prepare_classification_comparison.py ; son empreinte doit correspondre au split_plan.json conservé.", "", "```powershell",
    ".\\.venv-ml\\Scripts\\python.exe scripts/compare_classification.py --run",
    "# Utiliser le chemin exact du rapport horodaté affiché, sans choisir le meilleur parmi plusieurs relances.",
    ".\\.venv-ml\\Scripts\\python.exe scripts/train_final_models.py --comparison output/classification_comparisons/<rapport>.json --run",
    ".\\.venv-ml\\Scripts\\python.exe scripts/verify_final_models.py",
    "```", "",
    "Le programme refuse de remplacer une version finale existante ou de réévaluer un lot déjà terminé. Les graines sont fixées, les bibliothèques verrouillées et les entrées vérifiées par empreinte. Une nouvelle exécution dans une copie produit de nouveaux horodatages et durées, sans imposer que ces métadonnées soient identiques.", "",
    "## Limites et état avant l'application", "",
    "- Aucun blocage technique constaté pour charger les deux modèles et prédire avec les sept variables documentées.",
    "- La classification est modeste, surtout dans l'existant et sur F/G. Le rappel de G est élevé mais sa précision très faible : nombreuses fausses alertes. Ce modèle pédagogique ne délivre pas un DPE réglementaire.",
    "- La population change fortement entre entraînement, validation et réservé. Les scores globaux masquent des écarts neuf/existant.",
    "- Les filtres IQR et regroupements d'énergies ont été calculés globalement avant la séparation ; ce protocole ne valide pas toute la chaîne brute sans fuite de préparation. Une préparation ajustée uniquement sur l'entraînement et une évaluation externe restent nécessaires.",
    "- BAN est une adresse, pas une garantie d'identité physique du bâtiment. Des liens via les lignes éliminées peuvent manquer. Les logements neufs ont reçu un âge nul par imputation à 2026.",
    "- L'échantillon ADEME local n'est pas représentatif du parc français. Les sous-zones climatiques n'ont pas été inventées et l'enrichissement Rhône complet reste non rejoué sans ses fichiers.",
    "- Les anciens scores aléatoires ne se comparent pas directement aux scores présents : données, populations et découpage diffèrent.",
    "- Aucun réglage supplémentaire n'est recherché après cette évaluation. Aucun développement de l'application n'a été effectué.", ""]
target = ROOT / "doc/annexes/modeles_finaux_2026-10-29.md"
target.write_text("\n".join(lines), encoding="utf-8")
print("Rapport écrit :", target)
