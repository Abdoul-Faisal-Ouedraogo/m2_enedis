"""Interface française des niveaux Standard et Intermédiaire."""
import logging
import json

import pandas as pd
import streamlit as st

from src import project_paths
from src.final_model_loader import load_final_bundle
from src.app_design import context, styles, scale, page_header, NAV_LABELS, SIDEBAR_LABELS
from src.app_prediction_ui import render_prediction
from src.ai_interpretation import get_interpretation
from src.app_map import camera_for_selection, MAP_HEIGHT
from src.version_store import VersionStore
from src.expert_ui import render_management
from src.model_registry import load_model_version
from src.app_services import (LABELS, read_data, filter_data, csv_bytes, chart_pngs,
                              map_points, build_map)


def number(value, decimals=0):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


@st.cache_data(show_spinner="Lecture des données locales…", max_entries=2)
def cached_data(path, stamp, expected=None):
    if expected:
        from src.preparation_geography import sha256
        if sha256(path) != expected:
            raise ValueError("Données actives altérées")
    return read_data(path)


@st.cache_resource(show_spinner="Contrôle et chargement des deux modèles finaux…", max_entries=1)
def cached_bundle(stamps, version="final_geo_v1"):
    return load_model_version(version)


@st.cache_data(show_spinner="Préparation des graphiques…", max_entries=8)
def cached_charts(data, measure, percent):
    return chart_pngs(data, measure, percent)


@st.cache_data(show_spinner="Préparation du CSV…", max_entries=2)
def cached_csv(data):
    return csv_bytes(data)


def bundle():
    root = project_paths.ROOT
    store = VersionStore()
    version = store.active()["model"]
    if version == "final_geo_v2_temperature":
        folder = root / "MLmodels/final_geo_v2_temperature"
        stamps = tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in sorted(folder.glob("*")) if p.is_file())
        return cached_bundle(stamps,version)
    if version != "final_geo_v1":
        folder = store.folder("models",version)
        stamps = tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in sorted(folder.glob("*")) if p.is_file())
        return cached_bundle(stamps,version)
    paths = [root / "MLmodels/final_models.json", *sorted((root / "MLmodels/final_geo_v1").glob("*"))]
    stamps = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths if p.is_file())
    return cached_bundle(stamps,version)


def load_frame():
    try:
        store = VersionStore()
        version = store.active()["data"]
        path = project_paths.DATA_PATH if version == "initial" else store.data_paths(version, check=False)[0]
        expected = None if version == "initial" else store.manifest("datasets", version)["hashes"]["data.csv"]
        frame = cached_data(str(path), (path.stat().st_mtime_ns, path.stat().st_size), expected)
        if frame.empty:
            st.warning("Le fichier local est vide. Fournissez le CSV préparé par le groupe.")
        return frame
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        logging.getLogger(__name__).warning("Lecture impossible : %s", exc)
        st.error("Données locales absentes ou illisibles. "
                 "Récupérez le jeu préparé auprès du groupe. Aucun téléchargement automatique.")
        return None


def reset_filters():
    for key in list(st.session_state):
        if key.startswith("filter_"):
            del st.session_state[key]


def filters(df):
    st.sidebar.divider()
    st.sidebar.subheader("Affiner les logements")
    st.sidebar.caption("Liste vide = toutes les valeurs. Les choix suivants s’adaptent aux choix précédents.")
    st.sidebar.button("Réinitialiser les filtres", on_click=reset_filters)
    selections = {}
    facet = df
    for col in ["code_departement_ban", "etiquette_dpe", "type_batiment", "type_energie_principale_chauffage"]:
        if col not in df:
            st.sidebar.caption(f"{LABELS[col]} : colonne absente")
            continue
        options = sorted(facet[col].dropna().unique().tolist())
        key = "filter_" + col
        if key in st.session_state:
            st.session_state[key] = [v for v in st.session_state[key] if v in options]
        selections[col] = st.sidebar.multiselect(LABELS[col], options, key=key)
        if selections[col]:
            facet = facet[facet[col].isin(selections[col])]
    surface = None
    include = True
    if "surface_habitable_logement" in df:
        values = df.surface_habitable_logement.dropna()
        if len(values):
            low, high = float(values.min()), float(values.max())
            if low < high:
                surface = st.sidebar.slider("Surface habitable (m²)", low, high, (low, high), key="filter_surface")
            else:
                st.sidebar.caption(f"Surface unique : {number(low, 1)} m²")
            include = st.sidebar.checkbox("Inclure les surfaces non renseignées", value=True, key="filter_missing")
    result = filter_data(df, selections, surface, include)
    st.sidebar.caption(f"{number(len(result))} / {number(len(df))} logements retenus")
    active = [LABELS[col] + " : " + ", ".join(values) for col, values in selections.items() if values]
    if surface and (surface[0] > low or surface[1] < high):
        active.append(f"Surface : {number(surface[0], 1)} à {number(surface[1], 1)} m²")
    if not include:
        active.append("Surfaces non renseignées exclues")
    with st.container(border=True):
        st.markdown("**Filtres actifs**")
        st.write(" · ".join(active) if active else "Tous les logements · aucun filtre restrictif")
        st.button("Effacer les filtres actifs", on_click=reset_filters)
    return result


def exploration(df):
    page_header("Exploration")
    st.caption("Les indicateurs, tableaux et exports suivent tous les filtres de la barre latérale.")
    subset = filters(df)
    if subset.empty:
        st.info("Aucun logement ne correspond à ces filtres. Élargissez la surface ou réinitialisez les filtres.")
        return
    a, b, c, d = st.columns(4)
    a.metric("Logements retenus", number(len(subset)))
    b.metric("Surface moyenne", number(subset.surface_habitable_logement.mean(), 1) + " m²"
             if "surface_habitable_logement" in subset and subset.surface_habitable_logement.notna().any() else "—")
    c.metric("Consommation moyenne", number(subset.conso_5_usages_ef.mean()) + " kWh/an"
             if "conso_5_usages_ef" in subset and subset.conso_5_usages_ef.notna().any() else "—")
    d.metric("Part F et G", number(subset.etiquette_dpe.isin(["F", "G"]).mean() * 100, 1) + " %"
             if "etiquette_dpe" in subset else "—")
    st.caption("Moyennes sur les valeurs renseignées. Part F/G calculée sur tous les logements filtrés.")
    measures = [c for c in ["conso_5_usages_ef", "surface_habitable_logement"] if c in subset]
    if measures:
        measure = st.radio("Grandeur à explorer", measures, format_func=LABELS.get, horizontal=True)
        percent = st.checkbox("Afficher les barres en pourcentage")
        required = [c for c in ["etiquette_dpe", "conso_5_usages_ef", "surface_habitable_logement"] if c in subset]
        charts = cached_charts(subset[required], measure, percent)
        columns = st.columns(2)
        for i, (name, png) in enumerate(charts.items()):
            with columns[i % 2]:
                st.image(png, width="stretch")
                st.download_button("📥 Exporter ce graphique en PNG", png, f"dpe_{name}.png", "image/png", key="png_"+name)
        if len(charts) < 4:
            st.warning("Certains graphiques sont indisponibles : colonnes ou valeurs nécessaires absentes.")
        st.caption("Barres, histogramme et quartiles : toutes les lignes filtrées renseignées. "
                   "Boîtes : points extrêmes masqués, valeurs conservées dans les calculs. "
                   "Nuage : au plus 5 000 logements filtrés, tirage fixe (graine 42), effectif inscrit sur le graphique.")
    else:
        st.warning("Les colonnes de consommation et de surface sont absentes ; les graphiques ne peuvent pas être construits.")
    st.subheader("Détail de la sélection")
    st.dataframe(subset.head(500).rename(columns=LABELS), hide_index=True, width="stretch")
    st.caption(f"Aperçu : {number(min(500, len(subset)))} lignes. Le CSV contient les {number(len(subset))} lignes filtrées, toutes les colonnes et les noms d’origine.")
    # L’export complet est calculé seulement sur demande et ne persiste pas après changement des filtres.
    if st.button("Préparer l’export CSV filtré"):
        st.download_button("📥 Télécharger les données filtrées", cached_csv(subset), "logements_filtres.csv",
                           "text/csv", on_click="ignore")


def carte(df):
    page_header("Carte")
    subset = filters(df)
    if subset.empty:
        st.session_state.pop("map_camera", None)
        st.info("Aucun logement ne correspond à ces filtres. Élargissez-les pour afficher la carte.")
        return
    limit = st.select_slider("Nombre maximal de marqueurs", options=[1000, 2500, 5000, 10000], value=5000)
    basemap = st.checkbox("Afficher le fond de carte en ligne (CARTO)", value=False)
    st.caption("Le fond CARTO est facultatif et nécessite Internet. Sans ce fond, les marqueurs restent navigables sur un canevas local.")
    points, valid = map_points(subset, limit)
    a, b, c = st.columns(3)
    a.metric("Logements filtrés", number(len(subset)))
    b.metric("Coordonnées admissibles", number(valid))
    c.metric("Logements représentés", number(len(points)))
    st.caption(f"{number(len(subset) - valid)} coordonnées absentes ou hors emprise écartées. "
               "Contrôle : valeurs finies, latitude de 41 à 51,5°, longitude de −5,5 à 10° (métropole et Corse). "
               "Les points géographiquement plausibles ne sont pas certifiés à l’adresse.")
    if points.empty:
        st.session_state.pop("map_camera", None)
        st.warning("Aucune coordonnée admissible. Les colonnes lat/lon doivent être présentes et renseignées.")
        return
    st.info(f"{number(len(points))} logements représentés sur {number(valid)} géolocalisables : "
            + ("échantillon aléatoire déterministe (graine 42), sans pondération." if len(points) < valid else "affichage complet de la sélection géolocalisable."))
    scale()
    view, map_key = camera_for_selection(subset)
    st.pydeck_chart(build_map(points, basemap, view=view), height=MAP_HEIGHT, width="stretch",
                    key=map_key, on_select="rerun")
    st.caption("Survolez un marqueur pour lire ses informations. Déplacez et zoomez avec la souris. "
               "Couleurs : A vert → G rouge ; inconnu gris. Plusieurs logements à une adresse peuvent se superposer.")


def prediction(df):
    page_header("Prédiction")
    try:
        models = bundle()
    except Exception:
        logging.getLogger(__name__).exception("Échec du chargement des modèles finaux")
        st.error("Les modèles finaux sont indisponibles ou leur contrôle a échoué. Contactez le groupe pour restaurer les artefacts locaux compatibles.")
        return
    render_prediction(models, df)


def ai_interpretation():
    page_header("Interprétation IA")
    st.write("Obtenez une lecture pédagogique du résultat de votre modèle, sans envoyer votre jeu de données complet.")
    st.info("L'IA explique l'estimation ; elle ne remplace pas un DPE réglementaire et ne modifie jamais le résultat du modèle.")
    candidates = []
    for key, title in [("single_result", "Votre logement"), ("housing_a_result", "Logement A"),
                       ("housing_b_result", "Logement B")]:
        result = st.session_state.get(key)
        if result:
            candidates.append((key, title, result))
    if not candidates:
        st.warning("Calculez d'abord une estimation dans l'onglet « Prédiction énergétique ».")
        return
    selected = st.selectbox("Résultat à interpréter", candidates, format_func=lambda item: item[1],
                            key="ai_result_selection")
    if st.button("Générer l'interprétation IA", type="primary", width="stretch"):
        try:
            with st.spinner("Analyse pédagogique en cours…"):
                st.session_state.ai_interpretation = get_interpretation(selected[2])
            st.session_state.ai_interpretation_source = selected[0]
        except (RuntimeError, OSError) as exc:
            st.session_state.pop("ai_interpretation", None)
            st.error(f"Impossible de générer l'interprétation : {exc}")
    interpretation = st.session_state.get("ai_interpretation")
    if interpretation and st.session_state.get("ai_interpretation_source") == selected[0]:
        with st.container(border=True):
            st.subheader("Analyse de votre résultat")
            st.markdown(interpretation)


def run():
    styles()
    st.sidebar.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-logo"><div class="sidebar-logo-mark">EF</div>'
        '<div class="sidebar-logo-name">ENERGIE FRANCE</div></div>'
        '<div class="sidebar-title">Énergie France</div>'
        '<div class="sidebar-subtitle">Analyse &amp; Prédiction<br>Énergétique</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    try:
        revision = VersionStore().active()["revision"]
        if st.session_state.get("active_revision", revision) != revision:
            for key in list(st.session_state):
                if key.endswith("_result") or key.endswith("_dirty") or key == "map_camera" or key.startswith("filter_"):
                    del st.session_state[key]
        st.session_state.active_revision = revision
    except (OSError, ValueError, KeyError):
        st.error("Le registre actif est illisible. Restaurer le registre local avant de continuer.")
        return
    page = st.sidebar.radio("Navigation", list(NAV_LABELS), key="page",
                            format_func=lambda value: SIDEBAR_LABELS.get(value, value))
    df = load_frame()
    if page == "Contexte":
        context(df)
    elif page == "Prédiction":
        prediction(df)
    elif page == "Interprétation IA":
        ai_interpretation()
    elif page == "Gestion des données et modèles":
        page_header(page)
        render_management()
    elif df is not None and not df.empty:
        {"Exploration": exploration, "Carte": carte}[page](df)
    st.sidebar.divider()
    st.sidebar.markdown(
        '<div class="sidebar-sources"><strong>Sources de données :</strong>'
        '<ul><li>ADEME – Diagnostics DPE</li>'
        '<li>Enedis – Consommations de la France</li></ul></div>',
        unsafe_allow_html=True,
    )
