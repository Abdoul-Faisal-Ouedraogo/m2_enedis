"""Versions locales immuables et pointeur actif atomique, partagé UI/API."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import uuid

from src.project_paths import ROOT
from src.preparation_geography import sha256


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class VersionStore:
    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("ENEDIS_RUNTIME", ROOT / "runtime")).resolve()

    @contextmanager
    def lock(self, name="registry"):
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / (name + ".lock")
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ValueError("Une opération est déjà en cours (verrou local). Après un arrêt brutal, vérifier le processus avant de retirer le verrou.") from exc
        try:
            with os.fdopen(fd, "w") as stream:
                stream.write(str(os.getpid()))
            yield
        finally:
            path.unlink(missing_ok=True)

    def folder(self, kind, version):
        if kind not in {"datasets", "models"} or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", version):
            raise ValueError("Identifiant de version invalide")
        return self.root / kind / version

    def manifest(self, kind, version):
        return json.loads((self.folder(kind, version) / "manifest.json").read_text(encoding="utf-8"))

    def list_versions(self, kind):
        entries = []
        for path in sorted((self.root / kind).glob("*/manifest.json")):
            try:
                entries.append(json.loads(path.read_text(encoding="utf-8")))
            except (ValueError, OSError):
                continue
        return entries

    def active(self):
        path = self.root / "active.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
            "data": "initial",
            "model": os.environ.get("ENEDIS_DEFAULT_MODEL", "final_geo_v1"),
            "revision": "initial",
            "previous": None}

    def data_paths(self, version=None, check=True):
        version = version or self.active()["data"]
        if version == "initial":
            paths = ROOT / "output/cleaned_data.csv", ROOT / "output/cleaned_data_metadata.csv"
            if check:
                if not all(path.is_file() for path in paths):
                    raise ValueError("Entrées initiales absentes : fournir CSV préparé et métadonnées")
                protocol=json.loads((ROOT/"MLmodels/final_geo_v1/frozen_protocol.json").read_text(encoding="utf-8"))
                if sha256(paths[0])!=protocol["data_sha256"] or sha256(paths[1])!=protocol["metadata_sha256"]:
                    raise ValueError("Entrées initiales différentes de la référence validée")
            return paths
        folder = self.folder("datasets", version)
        info = self.manifest("datasets", version)
        if info["status"] != "validated":
            raise ValueError("Version de données non validée")
        if check:
            for filename in ["data.csv", "metadata.csv"]:
                if sha256(folder / filename) != info["hashes"][filename]:
                    raise ValueError("Données de version altérées")
        return folder / "data.csv", folder / "metadata.csv"

    def validate_data(self, version):
        with self.lock():
            info = self.manifest("datasets", version)
            if info["status"] not in {"prepared", "validated"} or not info["rows"]:
                raise ValueError("Aucune donnée préparée validable")
            for name, digest in info["hashes"].items():
                if sha256(self.folder("datasets", version) / name) != digest:
                    raise ValueError("Version altérée depuis sa préparation")
            info.update(status="validated", validated_at=now())
            atomic_json(self.folder("datasets", version) / "manifest.json", info)

    def activate(self, data=None, model=None):
        with self.lock():
            current = self.active()
            selected = {"data": data or current["data"], "model": model or current["model"]}
            self.data_paths(selected["data"])
            from src.model_registry import load_model_version
            load_model_version(selected["model"], self)
            selected.update(revision=uuid.uuid4().hex, previous={k: current[k] for k in ["data", "model"]}, changed_at=now())
            atomic_json(self.root / "active.json", selected)
            return selected

    def rollback(self):
        previous = self.active().get("previous")
        if not previous:
            raise ValueError("Aucune version précédente")
        return self.activate(**previous)
