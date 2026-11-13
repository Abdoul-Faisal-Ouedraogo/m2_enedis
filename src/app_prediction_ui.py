"""Saisies indépendantes et résultats figés, invalidés à chaque modification."""
from datetime import datetime
from zoneinfo import ZoneInfo
import json

import pandas as pd
import streamlit as st

from src import project_paths
from src.app_geography import read_geography, commune_proposal
from src.app_services import LABELS, category_options, predict
from src.app_design import number, scale
from src.app_pdf import estimation_pdf, COMPARISON_LIMIT


@st.cache_data(show_spinner=False, max_entries=2)
def cached_geography(cities_path, notebook_path, stamps):
    return read_geography(cities_path, notebook_path)


def geography():
    paths = [project_paths.ROOT / "data/communes-france-2025.csv",
             project_paths.ROOT / "Notebooks_Api_Traitement/1_data_preparation.ipynb"]
    return cached_geography(*(str(p) for p in paths), tuple((p.stat().st_mtime_ns, p.stat().st_size) for p in paths))


def geographical_help(prefix):
    mode = st.radio("Localisation", ["Saisie manuelle", "Choisir une commune"], key=prefix+"_geo_mode", horizontal=True)
    if mode == "Saisie manuelle":
        return "manuel"
    try:
        reference = geography()
    except (OSError, ValueError, KeyError):
        st.info("Le référentiel communal local est indisponible. Vous pouvez renseigner l’altitude et la zone manuellement.")
        return "référentiel indisponible"
    cities = reference["cities"]
    departments = cities[["dep_code", "dep_nom"]].drop_duplicates("dep_code").set_index("dep_code").dep_nom.to_dict()
    department = st.selectbox("Département du logement", sorted(departments), index=None,
                              format_func=lambda v: f"{v} · {departments[v]}", key=prefix+"_department", placeholder="Choisir un département")
    if department is None:
        return "département non choisi"
    towns = cities.loc[cities.dep_code.eq(department)].sort_values("nom_standard")
    names = towns.set_index("code_insee").nom_standard.to_dict()
    code = st.selectbox("Commune du logement", list(names), index=None, format_func=lambda v: f"{names[v]} ({v})",
                        key=prefix+"_commune_"+department, placeholder="Choisir une commune")
    if code is None:
        return department
    proposal = commune_proposal(reference, code, department)
    missing = [label for key, label in [
        ("altitude", "altitude"), ("zone", "zone climatique"),
        ("temperature_moyenne_annuelle", "température moyenne annuelle"),
        ("temperature_moyenne_hiver", "température moyenne hivernale"),
    ] if proposal.get(key) is None]
    if missing:
        st.warning("Donnée(s) indisponible(s) pour cette commune : " + ", ".join(missing) +
                   ". Les valeurs disponibles sont appliquées ; complétez le reste manuellement.")
    else:
        st.caption(
            f"Proposition : {number(proposal['altitude'], 1)} m · {proposal['zone']} · "
            f"{number(proposal['temperature_moyenne_annuelle'], 1)} °C en moyenne annuelle · "
            f"{number(proposal['temperature_moyenne_hiver'], 1)} °C en hiver. "
            f"{proposal['source']} Températures : Open-Meteo 2015–2024."
        )
    applied = st.session_state.get(prefix+"_applied_geo")
    selected_context = (proposal["department"], proposal["original_code"])
    applied_context = (
        (applied.get("department"), applied.get("original_code"))
        if applied else None
    )
    if applied_context != selected_context:
        for key, value in {
            prefix+"_altitude": proposal["altitude"],
            prefix+"_zone": proposal["zone"],
            prefix+"_temperature_annual": proposal["temperature_moyenne_annuelle"],
            prefix+"_temperature_winter": proposal["temperature_moyenne_hiver"],
        }.items():
            if value is not None:
                st.session_state[key] = value
        st.session_state[prefix+"_applied_geo"] = proposal
    return f"{department}/{code}"


def location_description(prefix, values, geo_context):
    applied = st.session_state.get(prefix+"_applied_geo")
    if applied and geo_context == f"{applied['department']}/{applied['original_code']}":
        geo_values = ["altitude_moyenne", "zone_climatique"]
        if "temperature_moyenne_annuelle" in values:
            geo_values += ["temperature_moyenne_annuelle", "temperature_moyenne_hiver"]
        expected = {
            "altitude_moyenne": applied["altitude"],
            "zone_climatique": applied["zone"],
            "temperature_moyenne_annuelle": applied.get("temperature_moyenne_annuelle"),
            "temperature_moyenne_hiver": applied.get("temperature_moyenne_hiver"),
        }
        if all(values[key] == expected[key] for key in geo_values):
            return f"{applied['commune']} ({applied['department']}) - {applied['source']} ; zone {applied['zone']}"
        return f"Saisie manuelle ajustée après proposition pour {applied['commune']}"
    return "Saisie manuelle de l’altitude et de la zone climatique"


def input_panel(prefix, title, models, df):
    contract = models["variables"]["classification"]
    options = category_options(models)
    with st.container(border=True):
        st.subheader(title)
        st.caption("1 · Situer le logement")
        geo_context = geographical_help(prefix)
        st.caption("2 · Décrire le logement")
        a, b = st.columns(2)
        surface = a.number_input("Surface habitable (m²)", min_value=.1, max_value=10000.0, value=80.0, step=1.0,
                                 key=prefix+"_surface", help="La surface du logement, sans les espaces non habitables.")
        levels = b.number_input("Nombre de niveaux du logement", min_value=1, max_value=100, value=1, step=1,
                                key=prefix+"_levels", help="Un appartement sur un seul étage compte un niveau.")
        age = st.number_input("Âge du bâtiment en 2026 (années)", min_value=0, max_value=1000, value=30, step=1,
                              key=prefix+"_age", help="2026 moins l’année de construction. Pour le neuf, le modèle utilise un âge nul imputé.")
        energy = st.selectbox("Énergie de chauffage", options["type_energie_principale_chauffage"], key=prefix+"_energy",
                              help="Énergie principale. « Autre » reprend le regroupement de la préparation.")
        building = st.selectbox("Type de bâtiment", options["type_batiment"], key=prefix+"_building")
        st.caption("3 · Préciser l’environnement")
        st.session_state.setdefault(prefix+"_altitude", 150.0)
        altitude = st.number_input("Altitude moyenne de la commune (m)", min_value=-500.0, max_value=5000.0,
                                   step=1.0, key=prefix+"_altitude", help="Altitude communale ou remplacement départemental, pas l’étage du logement.")
        zone = st.selectbox("Zone climatique", options["zone_climatique"], key=prefix+"_zone",
                            help="H1 : froide ; H2 : tempérée ; H3 : méditerranéenne. Aucune sous-zone n’est utilisée.")
        values = {
            "surface_habitable_logement": surface, "nombre_niveau_logement": levels,
            "age_batiment": age, "altitude_moyenne": altitude,
            "type_energie_principale_chauffage": energy, "type_batiment": building,
            "zone_climatique": zone,
        }
        if "temperature_moyenne_annuelle" in contract["features"]:
            defaults = {"H1": (11.5, 4.5), "H2": (12.5, 5.5), "H3": (14.0, 7.0)}
            annual_default, winter_default = defaults[zone]
            st.session_state.setdefault(prefix+"_temperature_annual", annual_default)
            st.session_state.setdefault(prefix+"_temperature_winter", winter_default)
            st.caption("Températures OpenData utilisées par la v2 (valeurs ajustables selon la commune).")
            temp_a, temp_b = st.columns(2)
            values["temperature_moyenne_annuelle"] = temp_a.number_input(
                "Température moyenne annuelle (°C)", min_value=10.0, max_value=16.0,
                step=.1, key=prefix+"_temperature_annual")
            values["temperature_moyenne_hiver"] = temp_b.number_input(
                "Température moyenne hivernale (°C)", min_value=3.0, max_value=9.0,
                step=.1, key=prefix+"_temperature_winter")
        values = {feature: values[feature] for feature in contract["features"]}
        location = location_description(prefix, values, geo_context)
        st.caption(location)
        signature = json.dumps({"values": values, "geography": geo_context, "location": location,
                                "models": models["version"]}, sort_keys=True, ensure_ascii=False)
        result_key = prefix+"_result"
        previous = st.session_state.get(result_key)
        if previous and previous["signature"] != signature:
            del st.session_state[result_key]
            st.session_state[prefix+"_dirty"] = True
        if st.button("Calculer les estimations", type="primary", width="stretch", key=prefix+"_calculate"):
            try:
                consumption, label = predict(models, values)
                st.session_state[result_key] = {"signature": signature, "name": title, "values": values,
                    "consumption": consumption, "label": label, "location": location,
                    "model_version": models["version"], "calculated_at": datetime.now(ZoneInfo("Europe/Paris")).isoformat()}
                st.session_state[prefix+"_dirty"] = False
            except (ValueError, TypeError, KeyError):
                st.session_state.pop(result_key, None)
                st.error("Vérifiez les caractéristiques saisies : une valeur n’est pas compatible avec le modèle.")
        if st.session_state.get(prefix+"_dirty"):
            st.info("Saisies modifiées : relancez le calcul pour afficher un résultat à jour.")
        result = st.session_state.get(result_key)
        if result and df is not None:
            outside = [LABELS[col] for col in contract["quantitative_features"] if col in df
                       and df[col].notna().any() and not df[col].min() <= values[col] <= df[col].max()]
            if outside:
                st.warning("Valeur hors du domaine observé : " + ", ".join(outside) + ". Estimation extrapolée, particulièrement incertaine.")
    return result


def result_panel(result, key):
    with st.container(border=True):
        st.subheader(result["name"] + " · résultat")
        st.metric("Consommation finale estimée · cinq usages", number(result["consumption"]) + " kWh/an")
        st.metric("Lettre DPE estimée", result["label"])
        scale(result["label"])
        st.caption("Calculé le " + datetime.fromisoformat(result["calculated_at"]).strftime("%d/%m/%Y à %H:%M") + " · les caractéristiques saisies sont reprises dans le PDF.")
        st.download_button("Télécharger le résumé PDF", estimation_pdf([result]), key+".pdf", "application/pdf", key=key+"_pdf", on_click="ignore", width="stretch")


def model_details(models):
    results = models["results"]
    with st.expander("Comprendre les résultats des modèles et leurs limites"):
        st.write("La lettre vient du classificateur, indépendamment de la consommation estimée. "
                 "Les scores ci-dessous décrivent un groupe, jamais la confiance dans une estimation individuelle.")
        a, b, c = st.columns(3)
        a.metric("DPE correctement classés", number(results["classification"]["accuracy"] * 100, 2) + " %")
        b.metric("F1 macro A–G", number(results["classification"]["f1_macro"], 4))
        c.metric("Erreur absolue moyenne", number(results["regression"]["mae"], 2) + " kWh/an")
        st.caption(f"Lot réservé interne de {number(results['classification']['rows'])} logements. Ce n’est pas une validation externe indépendante.")
        if "by_source" not in results:
            st.caption("Évaluation sur le lot réservé de la v2 enrichie avec les températures OpenData.")
            st.caption("Source température : " + models["protocol"].get("temperature_source", "non précisée"))
            return
        rows = []
        for source, scores in results["by_source"].items():
            rows.append({"Population": source, "Logements": scores["classification"]["rows"],
                         "DPE corrects (%)": round(scores["classification"]["accuracy"] * 100, 2),
                         "F1 macro": scores["classification"]["f1_macro"],
                         "Erreur absolue moyenne (kWh/an)": scores["regression"]["mae"],
                         "Erreur quadratique (kWh/an)": scores["regression"]["rmse"], "R²": scores["regression"]["r2"]})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        report = pd.DataFrame({k: results["classification"]["report"][k] for k in "ABCDEFG"}).T
        st.dataframe(report.rename(columns={"precision":"Précision", "recall":"Rappel", "f1-score":"F1", "support":"Logements"}), width="stretch")
        st.dataframe(pd.DataFrame(results["regression_by_dpe"]).T.rename(columns={"rows":"Logements", "mae":"Erreur absolue moyenne (kWh/an)", "rmse":"Erreur quadratique (kWh/an)", "r2":"R²"}), width="stretch")
        if "existant" in results["by_source"]:
            existing = results["by_source"]["existant"]
            st.write(f"Sur l’existant : {number(existing['classification']['accuracy']*100,2)} % de DPE corrects ; erreur absolue moyenne {number(existing['regression']['mae'])} kWh/an.")
        for label in "FG":
            entry = results["classification"]["report"][label]
            st.write(f"Classe {label} : précision {number(entry['precision']*100,2)} %, {number(entry['support'])} logements réservés. Interprétation prudente, notamment en cas de faible effectif.")
        st.write("Référence d’âge : 2026, avec âge nul imputé au neuf. Séparation temporelle avec groupes communs exclus ; "
                 "distributions différentes entre périodes. Nettoyage IQR et regroupements d’énergies effectués globalement : "
                 "la chaîne complète n’est pas validée sans fuite. Évaluation externe encore nécessaire.")
        st.caption("Version des modèles : " + models["version"])


def render_prediction(models, df):
    st.title("✨ Estimer et comparer")
    count = len(models["variables"]["classification"]["features"])
    st.write(f"Décrivez un logement en {count} caractéristiques. Vous pouvez aussi comparer deux profils et télécharger leurs résumés.")
    st.warning("Estimation pédagogique, sans valeur de DPE réglementaire. Prudence sur l’existant et les classes F/G ; aucune confiance individuelle n’est fournie.")
    mode = st.radio("Votre projet", ["Un logement", "Comparer deux logements"], horizontal=True, key="prediction_mode")
    if mode == "Un logement":
        entry, output = st.columns([1.15, 1])
        with entry:
            result = input_panel("single", "Votre logement", models, df)
        with output:
            if result:
                result_panel(result, "estimation")
            else:
                with st.container(border=True):
                    st.subheader("Votre estimation apparaîtra ici")
                    st.write("Renseignez les caractéristiques, puis lancez le calcul. Aucun résultat précédent ne sera conservé si vous modifiez les saisies.")
                    scale()
    else:
        results = []
        for col, prefix, title in zip(st.columns(2), ["housing_a", "housing_b"], ["Logement A", "Logement B"]):
            with col:
                results.append(input_panel(prefix, title, models, df))
        for col, result, key in zip(st.columns(2), results, ["estimation_a", "estimation_b"]):
            with col:
                if result:
                    result_panel(result, key)
                else:
                    st.info("Calculez ce logement pour afficher son résultat.")
        st.caption(COMPARISON_LIMIT)
        if all(results):
            st.metric("Écart de consommation estimée · B − A", number(results[1]["consumption"] - results[0]["consumption"]) + " kWh/an")
            st.download_button("Télécharger la comparaison PDF", estimation_pdf(results), "comparaison_logements.pdf", "application/pdf", key="comparison_pdf", on_click="ignore", width="stretch")
    st.caption("Consommation finale totale en kWh/an, pour les cinq usages. La MAE n’est pas un intervalle de confiance individuel.")
    model_details(models)
