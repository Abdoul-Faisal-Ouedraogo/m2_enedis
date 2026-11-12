"""Stabilité par composition du lot, traçabilité et bilan UI ; aucun fit/activation."""
from unittest.mock import patch

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.project_paths import ROOT
from src.app_geography import read_geography
from src.preparation_audit import prepare_audited, stable_policy


@pytest.fixture(scope="module")
def reference():
    return read_geography(ROOT/"data/communes-france-2025.csv",ROOT/"Notebooks_Api_Traitement/1_data_preparation.ipynb")


def row(number="target",**changes):
    return dict(numero_dpe=number,date_reception_dpe="2025-01-02",date_etablissement_dpe="2024-12-20",
                annee_construction=2000,cout_total_5_usages=1000,surface_habitable_logement=80,
                nombre_niveau_logement=1,conso_5_usages_ef=6000,code_insee_ban="69123",code_departement_ban="69",
                etiquette_dpe="D",type_batiment="maison",type_energie_principale_chauffage="Électricité")|changes


def test_historical_counts_primary_vs_overlapping_reasons(reference):
    raw=[row(str(i),annee_construction=None) for i in range(14)]
    raw[0].update(surface_habitable_logement=None,nombre_niveau_logement=None)
    raw += [row("missing",surface_habitable_logement=None,nombre_niveau_logement=None)]
    raw += [row("kept"+str(i),cout_total_5_usages=950+i*20,surface_habitable_logement=50+i*2) for i in range(5)]
    kept,audit=prepare_audited(raw,"existant",reference,{"id":"legacy_batch_iqr_v1","mode":"batch_iqr"})
    assert len(kept)==5
    assert audit["primary_counts"]=={"construction_missing":14,"surface_missing":1}
    assert audit["all_reason_counts"]=={"construction_missing":14,"surface_missing":2,"levels_missing":2}
    assert sum(audit["primary_counts"].values())==15
    assert audit["rows"][14]["reasons"]==["surface_missing","levels_missing"]


def test_same_record_has_same_admission_with_frozen_policy(reference):
    target=row(cout_total_5_usages=2000,surface_habitable_logement=130)
    neighbours=[row("near"+str(i)) for i in range(4)]
    alone,one=prepare_audited([target],"existant",reference)
    together,many=prepare_audited([target]+neighbours,"existant",reference)
    assert "target" in set(alone.numero_dpe) and "target" in set(together.numero_dpe)
    assert {k:(v["lower"],v["upper"]) for k,v in one["thresholds"].items()}=={k:(v["lower"],v["upper"]) for k,v in many["thresholds"].items()}
    _,legacy_one=prepare_audited([target],"existant",reference,{"id":"legacy","mode":"batch_iqr"})
    legacy_together,legacy_many=prepare_audited([target]+neighbours,"existant",reference,{"id":"legacy","mode":"batch_iqr"})
    assert legacy_one["kept"]==1 and "target" not in set(legacy_together.numero_dpe)
    assert legacy_many["primary_counts"]=={"cost_iqr":1}


@pytest.mark.parametrize("changes,reason",[
    ({"cout_total_5_usages":4000},"cost_iqr"),({"surface_habitable_logement":200},"surface_iqr"),
    ({"nombre_niveau_logement":None},"levels_missing"),({"annee_construction":None},"construction_missing")])
def test_frozen_bounds_and_missing_fields_remain_enforced(reference,changes,reason):
    kept,audit=prepare_audited([row(**changes)],"existant",reference)
    assert kept.empty and audit["primary_counts"]=={reason:1}


def test_frozen_profile_matches_initial_population_without_recalibration():
    policy=stable_policy()
    assert policy["bounds"]["cout_total_5_usages"]["upper"]==3019.7
    assert policy["bounds"]["surface_habitable_logement"]["upper"]==164
    assert policy["verified_initial_rows"]==616057
    data=pd.read_csv(ROOT/"output/cleaned_data.csv",usecols=list(policy["bounds"]))
    assert all(data[col].between(b["lower"],b["upper"]).all() for col,b in policy["bounds"].items())


def render_summary(info):
    from src.expert_ui import data_summary
    data_summary(info)


def test_simple_ui_counts_and_collapsed_json(reference):
    _,audit=prepare_audited([row("bad",annee_construction=None),row("ok")],"existant",reference)
    info={"received":2,"kept_new":1,"duplicates":0,"replaced_base":0,"rejected":1,"audit":audit}
    ui=AppTest.from_function(render_summary,args=(info,)).run()
    assert not ui.exception
    assert [(m.label,m.value) for m in ui.metric]==[("Reçus","2"),("Conservés","1"),("Doublons","0"),("Remplacés","0"),("Rejetés","1")]
    assert list(ui.dataframe[0].value["Effectif"])==[1]
    assert ui.expander[0].label=="Détails techniques du bilan (JSON)" and not ui.expander[0].proto.expanded


def test_duplicate_metric_is_not_double_counted_in_rejections():
    info={"received":3,"kept_new":1,"duplicates":1,"replaced_base":2,"rejected":2}
    ui=AppTest.from_function(render_summary,args=(info,)).run()
    assert [m.value for m in ui.metric]==["3","1","1","2","1"]


def test_menu_description_and_no_automatic_expert_actions():
    with patch("src.version_store.VersionStore.activate",side_effect=AssertionError("activation interdite")), \
         patch("src.expert_training.train_version",side_effect=AssertionError("entraînement interdit")):
        ui=AppTest.from_file(str(ROOT/"home.py"),default_timeout=90).run()
        ui.sidebar.radio[0].set_value("Gestion des données et modèles").run()
        assert not ui.exception
        # La légende « sur confirmation » a été remplacée par le bloc Sources (refonte 8944d9c) ;
        # les confirmations sont désormais portées par les cases à cocher de la page Gestion.
        captions=" ".join(c.value for c in ui.sidebar.caption)
        assert "sans extraction ni réentraînement" not in captions
