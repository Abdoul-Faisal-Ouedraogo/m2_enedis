"""Enrichir le dataset préparé avec une température OpenData versionnée.

La source est Open-Meteo Historical Weather API. Le script ne modifie jamais
output/cleaned_data.csv : il écrit uniquement dans output/temperature_v2/.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2015-01-01"
END_DATE = "2024-12-31"
BATCH_SIZE = 3
REPRESENTATIVE_LIMIT = 12


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_communes(path):
    columns = ["code_insee", "latitude_centre", "longitude_centre"]
    communes = pd.read_csv(path, usecols=columns, dtype={"code_insee": "string"})
    communes["code_insee"] = communes["code_insee"].str.zfill(5)
    for column in columns[1:]:
        communes[column] = pd.to_numeric(communes[column], errors="coerce")
    communes = communes.dropna().drop_duplicates("code_insee")
    if communes.empty:
        raise ValueError("Aucune commune avec coordonnées valides.")
    if not np.isfinite(communes[columns[1:]].to_numpy()).all():
        raise ValueError("Coordonnées communales non finies.")
    return communes


def fetch_batch(session, batch):
    params = {
        "latitude": ",".join(f"{value:.5f}" for value in batch.latitude_centre),
        "longitude": ",".join(f"{value:.5f}" for value in batch.longitude_centre),
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": "temperature_2m_mean",
        "timezone": "UTC",
    }
    for attempt in range(4):
        try:
            response = session.get(ARCHIVE_URL, params=params, timeout=120)
            if response.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 15 * (attempt + 1)
                time.sleep(delay)
                continue
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, list) else [payload]
        except (requests.RequestException, ValueError):
            if attempt == 3:
                raise
            time.sleep(15 * (attempt + 1))
    raise RuntimeError("Réponse Open-Meteo absente.")


def batch_temperature(session, batch):
    responses = fetch_batch(session, batch)
    if len(responses) != len(batch):
        raise ValueError("Open-Meteo a renvoyé un nombre de communes inattendu.")
    rows = []
    for code, payload in zip(batch.code_insee, responses):
        daily = payload.get("daily") or {}
        values = pd.to_numeric(pd.Series(daily.get("temperature_2m_mean", [])), errors="coerce")
        if values.empty or values.notna().sum() < 3000:
            raise ValueError(f"Données de température insuffisantes pour {code}.")
        rows.append({
            "code_insee": code,
            "temperature_moyenne_annuelle": round(float(values.mean()), 3),
            "temperature_moyenne_hiver": round(float(values.iloc[:90].mean()), 3),
            "temperature_source": "Open-Meteo ERA5-Land",
            "temperature_start": START_DATE,
            "temperature_end": END_DATE,
        })
    return rows


def representatives(communes):
    """Choose a stable geographic grid to keep API calls bounded."""
    work = communes.copy()
    work["lat_grid"] = work.latitude_centre.round(1)
    work["lon_grid"] = work.longitude_centre.round(1)
    selected = work.drop_duplicates(["lat_grid", "lon_grid"])
    return selected.sample(min(REPRESENTATIVE_LIMIT, len(selected)), random_state=42).drop(
        columns=["lat_grid", "lon_grid"]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Recalculer les fichiers v2 existants")
    args = parser.parse_args(argv)
    communes_path = ROOT / "data/communes-france-2025.csv"
    source_path = ROOT / "output/cleaned_data.csv"
    target = ROOT / "output/temperature_v2"
    target.mkdir(parents=True, exist_ok=True)
    enriched_path = target / "cleaned_data.csv"
    temperature_path = target / "temperatures_communes.csv"
    manifest_path = target / "manifest.json"
    if enriched_path.exists() and temperature_path.exists() and not args.force:
        print(f"Version déjà présente : {target.relative_to(ROOT)}")
        return
    communes = load_communes(communes_path)
    data = pd.read_csv(source_path, dtype={"code_insee_ban": "string"}, low_memory=False)
    data["code_insee_ban"] = data["code_insee_ban"].str.zfill(5)
    representatives_frame = representatives(communes)
    session = requests.Session()
    rows = []
    for start in range(0, len(representatives_frame), BATCH_SIZE):
        batch = representatives_frame.iloc[start:start + BATCH_SIZE]
        rows.extend(batch_temperature(session, batch))
        print(f"Températures : {min(start + len(batch), len(representatives_frame))}/{len(representatives_frame)}", flush=True)
        time.sleep(3)
    temperatures = pd.DataFrame(rows)
    source_points = temperatures.merge(representatives_frame, on="code_insee", validate="one_to_one")
    commune_xy = communes[["code_insee", "latitude_centre", "longitude_centre"]].to_numpy()
    source_xy = source_points[["latitude_centre", "longitude_centre"]].to_numpy()
    distances = ((commune_xy[:, None, 1:] - source_xy[None, :, 1:]) ** 2).sum(axis=2)
    nearest = source_points.iloc[distances.argmin(axis=1)].reset_index(drop=True)
    nearest["code_insee"] = communes.code_insee.to_numpy()
    temperatures = nearest[["code_insee", "temperature_moyenne_annuelle", "temperature_moyenne_hiver",
                            "temperature_source", "temperature_start", "temperature_end"]]
    data_xy = data[["lat", "lon"]].apply(pd.to_numeric, errors="coerce").to_numpy()
    valid_xy = np.isfinite(data_xy).all(axis=1)
    if not valid_xy.all():
        commune_lookup = communes.set_index("code_insee")[["latitude_centre", "longitude_centre"]]
        fallback_xy = data.loc[~valid_xy, "code_insee_ban"].map(commune_lookup.to_dict("index"))
        if fallback_xy.isna().any():
            raise ValueError("Certaines lignes ne disposent ni de coordonnées ni de commune météo.")
        data_xy[~valid_xy] = np.array([value.values() for value in fallback_xy], dtype=float)
        valid_xy[:] = True
    source_temperature_xy = source_points[["latitude_centre", "longitude_centre"]].to_numpy()
    nearest_data = np.zeros(len(data), dtype=int)
    nearest_data[valid_xy] = (
        ((data_xy[valid_xy, None, :] - source_temperature_xy[None, :, :]) ** 2)
        .sum(axis=2)
        .argmin(axis=1)
    )
    enriched = data.copy()
    enriched["temperature_moyenne_annuelle"] = source_points.iloc[nearest_data].temperature_moyenne_annuelle.to_numpy()
    enriched["temperature_moyenne_hiver"] = source_points.iloc[nearest_data].temperature_moyenne_hiver.to_numpy()
    if enriched[["temperature_moyenne_annuelle", "temperature_moyenne_hiver"]].isna().any().any():
        raise ValueError("Certaines lignes du dataset n'ont pas de température.")
    enriched.to_csv(enriched_path, index=False)
    temperatures.to_csv(temperature_path, index=False)
    manifest = {
        "version": "temperature_v2",
        "source": "Open-Meteo Historical Weather API",
        "endpoint": ARCHIVE_URL,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily_variable": "temperature_2m_mean",
        "communes": len(temperatures),
        "representative_points": len(representatives_frame),
        "assignment": "nearest representative commune on latitude/longitude grid",
        "rows": len(enriched),
        "source_data_sha256": sha256(source_path),
        "communes_sha256": sha256(communes_path),
        "data_sha256": sha256(enriched_path),
        "temperature_sha256": sha256(temperature_path),
        "created_at": date.today().isoformat(),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Dataset v2 écrit : {enriched_path.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, requests.RequestException) as exc:
        sys.exit(f"Échec de l'enrichissement météo : {exc}")
