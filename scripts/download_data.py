"""Télécharge les données publiques de la release data-v1 et vérifie leur SHA-256."""
import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.enrich_temperature import main as enrich_temperature

BASE_URL = "https://github.com/Abdoul-Faisal-Ouedraogo/App_Enedis/releases/download/data-v1/"
FILES = {
    "data/communes-france-2025.csv": (
        "communes-france-2025.csv",
        "1924778edf5cc9f92da85cb3ddd69476c526727d88d6140e9a7ef60f6d507b5e",
    ),
    "output/cleaned_data.csv": (
        "cleaned_data.csv",
        "e99209359b823f107ae2023a3ab300b6f052cfd71cb484ebbf84415e6d3b8be7",
    ),
    "output/cleaned_data_metadata.csv": (
        "cleaned_data_metadata.csv",
        "41d1fc1594774100f537da3568c8dd5b22e939dcfff15011e7425e7eb24c5b75",
    ),
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch(target, asset, expected):
    if target.is_file() and sha256(target) == expected:
        print(f"Déjà présent et vérifié : {target.relative_to(ROOT)}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".part")
    print(f"Téléchargement de {asset}…")
    try:
        with urllib.request.urlopen(BASE_URL + asset, timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        if sha256(temporary) != expected:
            raise ValueError(f"Empreinte SHA-256 inattendue pour {asset}")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Vérifié : {target.relative_to(ROOT)}")


def main():
    for relative, (asset, expected) in FILES.items():
        fetch(ROOT / relative, asset, expected)
    print("Préparation des températures v2…")
    enrich_temperature([])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        sys.exit(f"Échec du téléchargement des données : {exc}")
