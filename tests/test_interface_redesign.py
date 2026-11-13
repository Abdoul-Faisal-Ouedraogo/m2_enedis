"""Régressions de la refonte : navigation, saisies réactives, géographie et PDF."""
from io import BytesIO
from unittest.mock import patch
import json

import numpy as np
import pandas as pd
import pytest
from pypdf import PdfReader
from streamlit.testing.v1 import AppTest

from src.project_paths import ROOT
from src.app_geography import read_geography, commune_proposal
from src.app_services import map_view
from src.app_pdf import estimation_pdf


def app_prediction():
    ui = AppTest.from_file(str(ROOT / "home.py"), default_timeout=90).run()
    ui.sidebar.radio[0].set_value("Prédiction").run()
    assert not ui.exception
    return ui


def test_home_calls_to_action():
    ui = AppTest.from_file(str(ROOT / "home.py"), default_timeout=90).run()
    [b for b in ui.button if b.label == "Explorer les logements"][0].click().run()
    assert not ui.exception and ui.sidebar.radio[0].value == "Exploration"
    ui.sidebar.radio[0].set_value("Contexte").run()
    [b for b in ui.button if b.label == "Estimer un logement"][0].click().run()
    assert ui.sidebar.radio[0].value == "Prédiction" and not ui.exception


def test_changed_inputs_remove_result_and_pdf_until_recalculation():
    ui = app_prediction()
    ui.button(key="single_calculate").click().run()
    assert len(ui.get("download_button")) == 1
    first = ui.session_state["single_result"]
    ui.number_input(key="single_surface").set_value(125.0).run()
    assert not ui.exception
    assert len(ui.get("download_button")) == 0
    assert all(m.label != "Lettre DPE estimée" for m in ui.metric)
    assert any("Saisies modifiées" in i.value for i in ui.info)
    # Revenir aux valeurs originales ne ressuscite pas un résultat déjà invalidé.
    ui.number_input(key="single_surface").set_value(80.0).run()
    assert len(ui.get("download_button")) == 0
    ui.button(key="single_calculate").click().run()
    # La réduction parallèle des arbres peut varier de quelques ULP selon
    # l'ordre des additions. 1e-12 relatif (~1e-8 kWh/an ici) reste très
    # inférieur à la précision affichée et ne tolère pas une dérive métier.
    assert ui.session_state["single_result"]["consumption"] == pytest.approx(
        first["consumption"], rel=1e-12, abs=1e-9
    )
    assert len(ui.get("download_button")) == 1


def test_two_independent_profiles_comparison_and_invalidation():
    ui = app_prediction()
    ui.radio(key="prediction_mode").set_value("Comparer deux logements").run()
    ui.number_input(key="housing_b_surface").set_value(120.0).run()
    ui.button(key="housing_a_calculate").click().run()
    assert len(ui.get("download_button")) == 1
    ui.button(key="housing_b_calculate").click().run()
    assert not ui.exception and len(ui.get("download_button")) == 3
    a, b = ui.session_state["housing_a_result"], ui.session_state["housing_b_result"]
    assert a["values"]["surface_habitable_logement"] == 80
    assert b["values"]["surface_habitable_logement"] == 120
    metric = [m for m in ui.metric if m.label.startswith("Écart")][0]
    expected = f"{b['consumption'] - a['consumption']:,.0f}".replace(",", " ") + " kWh/an"
    assert metric.value == expected
    ui.selectbox(key="housing_a_zone").set_value("H3").run()
    assert not ui.exception and len(ui.get("download_button")) == 1
    assert ui.session_state["housing_b_result"] == b
    assert not [m for m in ui.metric if m.label.startswith("Écart")]


@pytest.fixture(scope="module")
def reference():
    return read_geography(ROOT / "data/communes-france-2025.csv", ROOT / "Notebooks_Api_Traitement/1_data_preparation.ipynb")


def test_reference_rules_corrections_and_departmental_fallback(reference):
    assert len(reference["cities"]) == 34935
    lyon = commune_proposal(reference, "69381", "69")
    pierre = commune_proposal(reference, "69152", "69")
    assert lyon["reference_code"] == "69123" and lyon["altitude"] == 237 and lyon["zone"] == "H1"
    assert pierre["reference_code"] == "69149" and pierre["altitude"] == 194 and pierre["corrected"]
    fallback = commune_proposal(reference, "69999", "69")
    mean = reference["cities"].loc[lambda d: d.dep_code.eq("69"), "altitude_moyenne"].mean()
    assert fallback["altitude"] == pytest.approx(mean)
    assert "Remplacement" in fallback["source"]
    missing = commune_proposal(reference, "99999", "99")
    assert missing["altitude"] is None and missing["zone"] is None
    assert reference["zones"]["13"] == "H3" and reference["zones"]["33"] == "H2"
    # Aucun rapprochement inventé entre la Corse 2A/2B du référentiel et le code 20 du notebook.
    assert reference["zones"].get("2A") is None


def test_commune_selection_applies_values_and_manual_override():
    ui = app_prediction()
    ui.button(key="single_calculate").click().run()
    ui.radio(key="single_geo_mode").set_value("Choisir une commune").run()
    assert len(ui.get("download_button")) == 0
    ui.selectbox(key="single_department").set_value("69").run()
    ui.selectbox(key="single_commune_69").set_value("69123").run()
    assert not ui.exception
    assert ui.number_input(key="single_altitude").value == 237
    assert ui.selectbox(key="single_zone").value == "H1"
    ui.button(key="single_calculate").click().run()
    assert "communale" in ui.session_state["single_result"]["location"]
    ui.number_input(key="single_altitude").set_value(200.0).run()
    assert len(ui.get("download_button")) == 0
    ui.button(key="single_calculate").click().run()
    assert "manuelle ajustée" in ui.session_state["single_result"]["location"]
    ui.selectbox(key="single_department").set_value("13").run()
    assert ui.selectbox(key="single_commune_13").value is None
    assert len(ui.get("download_button")) == 0


def test_missing_reference_preserves_manual_inputs():
    with patch("src.app_prediction_ui.geography", side_effect=FileNotFoundError()):
        ui = app_prediction()
        ui.radio(key="single_geo_mode").set_value("Choisir une commune").run()
        assert any("référentiel communal local est indisponible" in v.value for v in ui.info)
        ui.button(key="single_calculate").click().run()
        assert not ui.exception and len(ui.get("download_button")) == 1


def test_map_framing_follows_selection():
    country = pd.DataFrame({"lat": [42, 51], "lon": [-5, 9]})
    rhone = pd.DataFrame({"lat": [45.5, 46], "lon": [4.5, 5]})
    town = pd.DataFrame({"lat": [45.7, 45.7], "lon": [4.8, 4.8]})
    assert map_view(country).zoom < map_view(rhone).zoom < map_view(town).zoom
    assert map_view(rhone).longitude == pytest.approx(4.75)
    assert 45.5 < map_view(rhone).latitude < 46
    assert np.isfinite(map_view(town).zoom)
    with pytest.raises(ValueError):
        map_view(pd.DataFrame({"lat": [999], "lon": [0]}))


def test_pdf_contains_snapshot_inputs_units_date_version_and_limits():
    ui = app_prediction()
    ui.button(key="single_calculate").click().run()
    record = ui.session_state["single_result"]
    pdf = estimation_pdf([record])
    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    for expected in ["Surface habitable", "80", "kWh/an", "m²", "2026", "Europe/Paris", "final_geo_v1",
                     "DPE réglementaire", "F/G", "intervalles de confiance individuels"]:
        assert expected in text
    assert record["label"] in text
    second = dict(record, name="Logement B", consumption=record["consumption"] + 1000)
    comparison = PdfReader(BytesIO(estimation_pdf([dict(record, name="Logement A"), second])))
    assert len(comparison.pages) == 2
    assert "1 000 kWh/an" in comparison.pages[0].extract_text()
    assert "preuve causale" in comparison.pages[0].extract_text()
    assert "Logement B" in comparison.pages[1].extract_text()
    # Le PDF reprend le résultat figé, sans nouvel appel aux modèles.
    with patch("src.app_services.predict", side_effect=AssertionError("pas de recalcul")):
        assert estimation_pdf([record]).startswith(b"%PDF")
