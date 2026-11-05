"""Chargeur commun Streamlit/API ; aucune activation implicite."""
from src.final_model_loader import load_final_bundle
from src import project_paths
import json
import joblib
import sklearn
from threadpoolctl import threadpool_limits
from src.final_models import check_reload_fixture
from src.ml_workflow import NUMERIC, CATEGORICAL
from src.preparation_geography import sha256
from src.version_store import VersionStore


def load_model_version(version="final_geo_v1", store=None):
    if version == "final_geo_v1":
        result = load_final_bundle()
        result["version"] = version
        return result
    if version == "final_geo_v2_temperature":
        root = project_paths.ROOT / "MLmodels/final_geo_v2_temperature"
        variables = json.loads((root / "variables.json").read_text(encoding="utf-8"))
        features = variables["numeric"] + variables["categorical"]
        result = {
            "version": version,
            "variables": {},
            "results": json.loads((root / "results.json").read_text(encoding="utf-8")),
            "protocol": {"temperature_source": variables["temperature_source"]},
        }
        for kind, target in [("classification", "etiquette_dpe"),
                             ("regression", "conso_5_usages_ef")]:
            model = joblib.load(root / f"{kind}.joblib")
            if list(model.feature_names_in_) != features:
                raise ValueError("Variables du pipeline température incompatibles")
            result[kind] = model
            result["variables"][kind] = {
                "features": features,
                "quantitative_features": variables["numeric"],
                "qualitative_features": variables["categorical"],
                "reference_year": variables["reference_year"],
                "target": target,
            }
        return result
    store = store or VersionStore()
    folder = store.folder("models", version)
    info = store.manifest("models", version)
    if info["status"] != "ready" or info["sklearn"] != sklearn.__version__:
        raise ValueError("Version non prête ou bibliothèque incompatible")
    for filename, digest in info["hashes"].items():
        if "/" in filename or "\\" in filename or filename in {".",".."}:
            raise ValueError("Nom d'artefact invalide")
        if sha256(folder / filename) != digest:
            raise ValueError("Artefacts de modèle altérés")
    result = {"version":version, "variables":{}, "protocol":json.loads((folder/"protocol.json").read_text(encoding="utf-8"))}
    for kind, target in [("classification","etiquette_dpe"),("regression","conso_5_usages_ef")]:
        variables = json.loads((folder/f"{kind}_variables.json").read_text(encoding="utf-8"))
        if variables["features"] != NUMERIC+CATEGORICAL or variables["reference_year"] != 2026 or variables["target"] != target:
            raise ValueError("Contrat des sept caractéristiques incompatible")
        result[kind] = joblib.load(folder/f"{kind}.joblib")
        if list(result[kind].feature_names_in_) != variables["features"]:
            raise ValueError("Variables du pipeline incompatibles")
        result["variables"][kind] = variables
    fixture = json.loads((folder/"reload_check.json").read_text(encoding="utf-8"))
    with threadpool_limits(limits=2):
        check_reload_fixture(fixture,result["classification"],result["regression"])
    result["results"] = json.loads((folder/"results.json").read_text(encoding="utf-8"))
    return result
