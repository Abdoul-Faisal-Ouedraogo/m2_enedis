"""Contrôles locaux réels : UI Streamlit, contrats ML, carte et exports."""
from io import BytesIO
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

from src import project_paths
from src.app_services import (read_data, filter_data, chart_pngs, csv_bytes, map_points,
                              build_map, predict, category_options)
from src.final_model_loader import load_final_bundle

ROOT = project_paths.ROOT


@pytest.fixture(scope="session")
def data():
    return read_data(project_paths.DATA_PATH)


@pytest.fixture(scope="session")
def models():
    return load_final_bundle()


def app(page="Contexte"):
    result = AppTest.from_file(str(ROOT / "home.py"), default_timeout=90).run()
    if page != "Contexte":
        result.sidebar.radio[0].set_value(page).run()
    assert not result.exception
    return result


def test_four_pages_real_data():
    ui = app()
    assert ui.metric[0].value == "616 057"
    for page in ["Exploration", "Carte", "Prédiction"]:
        ui.sidebar.radio[0].set_value(page).run()
        assert not ui.exception
        assert not ui.error
        if page == "Exploration":
            assert len(ui.get("download_button")) == 5
        elif page == "Carte":
            assert ui.metric[2].value == "5 000"
            assert len(ui.get("deck_gl_json_chart")) == 1


def test_combined_filters_and_ui_exports(data):
    ui = app("Exploration")
    selected = {}
    columns = ["code_departement_ban", "etiquette_dpe", "type_batiment", "type_energie_principale_chauffage"]
    values = ["69", "C", "appartement"]
    for i, col in enumerate(columns):
        widget = ui.sidebar.multiselect[i]
        value = values[i] if i < 3 else widget.options[0]
        selected[col] = [value]
        widget.set_value([value]).run()
        assert not ui.exception
    ui.sidebar.slider[0].set_value((40.0, 100.0)).run()
    expected = filter_data(data, selected, (40, 100))
    assert len(expected) > 0
    assert ui.metric[0].value == f"{len(expected):,}".replace(",", " ")
    ui.sidebar.radio[0].set_value("Carte").run()
    assert not ui.exception
    assert ui.metric[0].value == f"{len(expected):,}".replace(",", " ")
    ui.select_slider[0].set_value(1000).run()
    assert int(ui.metric[2].value.replace(" ", "")) <= 1000
    ui.sidebar.radio[0].set_value("Exploration").run()
    assert ui.metric[0].value == f"{len(expected):,}".replace(",", " ")
    [w for w in ui.checkbox if w.label == "Afficher les barres en pourcentage"][0].check().run()
    [w for w in ui.radio if w.label == "Grandeur à explorer"][0].set_value("surface_habitable_logement").run()
    assert not ui.exception
    # Le bouton de préparation produit un cinquième téléchargement (CSV).
    [b for b in ui.button if b.label == "Préparer l’export CSV filtré"][0].click().run()
    assert len(ui.get("download_button")) == 6
    # Une surface située dans une lacune observée, à l'intérieur des bornes du curseur.
    surfaces = sorted(data.surface_habitable_logement.dropna().unique())
    gap = max(zip(surfaces, surfaces[1:]), key=lambda pair: pair[1] - pair[0])
    empty_surface = round((gap[0] + gap[1]) / 2, 2)
    ui.sidebar.slider[0].set_value((empty_surface, empty_surface)).run()
    assert not ui.exception
    assert any("Aucun logement" in v.value for v in ui.info)
    assert len(ui.get("download_button")) == 0
    ui.sidebar.button[0].click().run()
    assert ui.metric[0].value == "616 057"


def test_csv_and_four_png_files_are_valid_and_filtered(data, tmp_path):
    subset = filter_data(data, {"code_departement_ban": ["69"], "etiquette_dpe": ["C"]}, (40, 100))
    exported = csv_bytes(subset)
    actual = pd.read_csv(BytesIO(exported), sep=";", decimal=",", dtype={"code_departement_ban": str})
    assert len(actual) == len(subset)
    assert actual.code_departement_ban.eq("69").all()
    assert actual.etiquette_dpe.eq("C").all()
    assert actual.surface_habitable_logement.between(40, 100).all()
    assert list(actual) == list(subset)
    charts = chart_pngs(subset, "conso_5_usages_ef")
    assert set(charts) == {"barres", "histogramme", "boites", "nuage"}
    for name, binary in charts.items():
        assert binary.startswith(b"\x89PNG\r\n\x1a\n")
        Image.open(BytesIO(binary)).verify()
        (tmp_path / f"{name}.png").write_bytes(binary)
    assert chart_pngs(subset.head(10), "surface_habitable_logement", True)["barres"] != charts["barres"]


def test_map_full_data_determinism_and_filtering(data):
    points, valid = map_points(data, 5000)
    assert len(points) == 5000 and valid > 5000
    pd.testing.assert_frame_equal(points, map_points(data, 5000)[0])
    selected = data[data.etiquette_dpe.eq("G") & data.code_departement_ban.eq("69")]
    filtered, count = map_points(selected, 10000)
    assert len(filtered) == count
    assert filtered.etiquette_dpe.eq("G").all()
    deck = json.loads(build_map(filtered).to_json())
    assert len(deck["layers"][0]["data"]) == count
    assert deck["layers"][0]["pickable"]
    assert deck["mapStyle"] == "__MAP_STYLE__"
    assert "mapProvider" not in deck


def test_invalid_coordinates_and_missing_columns():
    df = pd.DataFrame({"lat": [48, np.nan, np.inf, 0, 95, 48, 42],
                       "lon": [2, 2, 2, 0, 2, 150, 9],
                       "nom_commune_ban": ["<script>"] * 7})
    points, count = map_points(df)
    assert count == len(points) == 2
    assert points.nom_commune_ban.eq("<script>").all()  # Affiché comme texte, jamais comme HTML.
    assert map_points(df.drop(columns="lat"))[0].empty
    # Surfaces manquantes explicitement incluses ou exclues, zéro résultat accepté.
    frame = pd.DataFrame({"surface_habitable_logement": [50, np.nan, 100]})
    assert len(filter_data(frame, {}, (40, 60), True)) == 2
    assert len(filter_data(frame, {}, (40, 60), False)) == 1
    assert filter_data(frame, {}, (1, 2), False).empty


def test_tooltip_plain_text_preserves_apostrophes_and_accents():
    names = ["Marcy-l'Étoile", "L’Haÿ-les-Roses", '<script>alert("x")</script> & texte']
    frame = pd.DataFrame({"lat": [48.0] * 3, "lon": [2.0] * 3, "nom_commune_ban": names})
    points, _ = map_points(frame)
    pd.testing.assert_series_equal(points.nom_commune_ban.sort_index(), frame.nom_commune_ban)
    deck = build_map(points)
    assert "text" in deck._tooltip and "html" not in deck._tooltip
    assert "{nom_commune_ban}" in deck._tooltip["text"]
    assert "&#x27;" not in deck.to_json()


def test_map_basemap_toggle_keeps_markers():
    ui = app("Carte")
    layers = []
    for enabled in [False, True, False]:
        checkbox = [w for w in ui.checkbox if w.label.startswith("Afficher le fond")][0]
        checkbox.set_value(enabled).run()
        assert not ui.exception
        chart = ui.get("deck_gl_json_chart")[0].proto
        spec = json.loads(chart.json)
        if enabled:
            assert spec["mapProvider"] == "carto"
            assert spec["mapStyle"] == "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
        else:
            # Une absence de mapStyle provoquerait le retour automatique de CARTO.
            assert spec["mapStyle"] == "__MAP_STYLE__"
            assert "mapProvider" not in spec
            assert "cartocdn" not in chart.json
        assert len(spec["layers"][0]["data"]) == 5000
        assert spec["layers"][0]["pickable"]
        tooltip = json.loads(chart.tooltip)
        assert "text" in tooltip and "html" not in tooltip
        layers.append(spec["layers"])
    assert layers[0] == layers[1] == layers[2]


def test_prediction_exact_reload_fixture(models):
    fixture = json.loads((ROOT / "MLmodels/final_geo_v1/reload_check.json").read_text(encoding="utf-8"))
    # Prédictions de développement seulement : aucun nouvel appel sur le lot réservé.
    for i in [0, 4, 15, 31]:
        consumption, label = predict(models, fixture["features"][i])
        assert consumption == pytest.approx(fixture["regression"][i], rel=1e-12)
        assert label == fixture["classification"][i]
    options = category_options(models)
    assert options["zone_climatique"] == ["H1", "H2", "H3"]
    assert models["variables"]["classification"]["reference_year"] == 2026


@pytest.mark.parametrize("key,value", [("surface_habitable_logement", 0), ("age_batiment", -1),
    ("altitude_moyenne", float("inf")), ("nombre_niveau_logement", 1.5),
    ("type_batiment", "inconnu"), ("zone_climatique", "H1a")])
def test_invalid_prediction_inputs(models, key, value):
    fixture = json.loads((ROOT / "MLmodels/final_geo_v1/reload_check.json").read_text(encoding="utf-8"))
    values = dict(fixture["features"][0], **{key: value})
    with pytest.raises(ValueError):
        predict(models, values)


def test_prediction_ui_real_models():
    ui = app("Prédiction")
    assert len(ui.number_input) == 4 and len(ui.selectbox) == 3
    ui.number_input[0].set_value(10000.0)
    ui.number_input[2].set_value(0)
    ui.selectbox[2].set_value("H3")
    ui.button[0].click().run()
    assert not ui.exception
    assert ui.metric[0].value.endswith("kWh/an") and ui.metric[1].value in list("ABCDEFG")
    assert any("hors du domaine" in v.value for v in ui.warning)
    assert ui.metric[2].value == "55,41 %"
    assert ui.metric[4].value == "1 814,68 kWh/an"


def test_missing_data_does_not_disable_prediction():
    with patch.object(project_paths, "DATA_PATH", ROOT / "output/inexistant_test_app.csv"):
        ui = app()
        assert any("absentes" in e.value for e in ui.error)
        ui.sidebar.radio[0].set_value("Prédiction").run()
        ui.button[0].click().run()
        assert not ui.exception
        assert ui.metric[0].value.endswith("kWh/an")


def test_missing_models_clear_error():
    with patch("src.streamlit_app.bundle", side_effect=FileNotFoundError("test")):
        ui = app("Prédiction")
        assert len(ui.error) == 1
        assert "modèles finaux" in ui.error[0].value


def test_partial_data_and_no_geolocation():
    with patch("src.streamlit_app.cached_data", return_value=pd.DataFrame({"autre": [1, 2]})):
        ui = app("Exploration")
        assert ui.warning
        ui.sidebar.radio[0].set_value("Carte").run()
        assert not ui.exception
        assert any("Aucune coordonnée" in w.value for w in ui.warning)


def test_empty_file_message():
    with patch("src.streamlit_app.cached_data", return_value=pd.DataFrame()):
        ui = app()
        assert any("vide" in w.value for w in ui.warning)
