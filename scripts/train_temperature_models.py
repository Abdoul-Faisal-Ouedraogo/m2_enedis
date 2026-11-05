"""Entraîner des modèles v2 avec température sans toucher aux modèles v1."""
import argparse
from pathlib import Path
import json
import platform
import sys

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.expert_training import temporal_partitions
from src.final_models import classification_metrics, regression_metrics
from src.ml_workflow import CATEGORICAL, NUMERIC
from src.preparation_geography import sha256

NUMERIC_V2 = NUMERIC + ["temperature_moyenne_annuelle", "temperature_moyenne_hiver"]
OUTPUT = ROOT / "MLmodels/final_geo_v2_temperature"


def pipeline(estimator, categories, parameters):
    return Pipeline([("preprocessor", ColumnTransformer([
        ("numeric", "passthrough", NUMERIC_V2),
        ("encoder", OneHotEncoder(categories=[categories[column] for column in CATEGORICAL],
                                   handle_unknown="ignore"), CATEGORICAL),
    ])), ("model", estimator(**parameters))])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "output/temperature_v2/cleaned_data.csv")
    parser.add_argument("--metadata", type=Path, default=ROOT / "output/cleaned_data_metadata.csv")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--run", action="store_true", help="Autoriser l'entraînement v2")
    args = parser.parse_args()
    if not args.run:
        print("Préparation uniquement : ajouter --run pour entraîner les modèles v2.")
        return
    data = pd.read_csv(args.data, dtype={"code_departement_ban": "string"}, low_memory=False)
    metadata = pd.read_csv(args.metadata, dtype="string").replace(r"^\s*$", pd.NA, regex=True)
    required = NUMERIC_V2 + CATEGORICAL + ["etiquette_dpe", "conso_5_usages_ef"]
    missing = sorted(set(required) - set(data.columns))
    if missing or data[required].isna().any().any():
        raise ValueError(f"Dataset v2 incomplet : {missing}")
    if len(data) != len(metadata):
        raise ValueError("Dataset v2 et métadonnées désalignés.")
    assignments = temporal_partitions(metadata)
    fit = assignments.partition.isin(["train", "validation"]).to_numpy()
    reserved = assignments.partition.eq("reserved").to_numpy()
    categories = {column: sorted(data[column].dropna().unique().tolist()) for column in CATEGORICAL}
    args.output.mkdir(parents=True, exist_ok=True)
    assignments.to_csv(args.output / "assignments.csv", index=False)
    parameters = {
        "classification": {"n_estimators": 100, "max_depth": 10, "min_samples_split": 20,
                            "class_weight": "balanced", "random_state": 42, "n_jobs": 2},
        "regression": {"n_estimators": 100, "max_depth": 10, "min_samples_split": 20,
                       "min_samples_leaf": 1, "random_state": 42, "n_jobs": 2},
    }
    bundles = {}
    with threadpool_limits(limits=2):
        for kind, estimator, target in [("classification", RandomForestClassifier, "etiquette_dpe"),
                                        ("regression", RandomForestRegressor, "conso_5_usages_ef")]:
            model = pipeline(estimator, categories, parameters[kind])
            model.fit(data.loc[fit, NUMERIC_V2 + CATEGORICAL], data.loc[fit, target])
            joblib.dump(model, args.output / f"{kind}.joblib", compress=3)
            bundles[kind] = model
    actual = data.loc[reserved].reset_index(drop=True)
    with threadpool_limits(limits=2):
        labels = bundles["classification"].predict(data.loc[reserved, NUMERIC_V2 + CATEGORICAL])
        consumption = bundles["regression"].predict(data.loc[reserved, NUMERIC_V2 + CATEGORICAL])
    results = {
        "version": "final_geo_v2_temperature",
        "features": NUMERIC_V2 + CATEGORICAL,
        "fit_rows": int(fit.sum()),
        "reserved_rows": int(reserved.sum()),
        "classification": classification_metrics(actual.etiquette_dpe, labels),
        "regression": regression_metrics(actual.conso_5_usages_ef, consumption),
        "python": platform.python_version(),
        "sklearn": sklearn.__version__,
        "data_sha256": sha256(args.data),
    }
    (args.output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "variables.json").write_text(json.dumps({
        "numeric": NUMERIC_V2, "categorical": CATEGORICAL,
        "reference_year": 2026, "temperature_source": "Open-Meteo Historical Weather API",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
