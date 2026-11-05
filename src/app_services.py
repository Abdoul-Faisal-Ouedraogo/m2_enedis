"""Consultation et prédiction sans modifier les données ou artefacts."""
from io import BytesIO
import numpy as np
import pandas as pd
import pydeck as pdk
from matplotlib.figure import Figure
from threadpoolctl import threadpool_limits

LABELS = {
    "code_departement_ban": "Département", "etiquette_dpe": "Classe DPE",
    "type_batiment": "Type de bâtiment", "type_energie_principale_chauffage": "Énergie de chauffage",
    "surface_habitable_logement": "Surface habitable (m²)",
    "conso_5_usages_ef": "Consommation finale (kWh/an)", "nom_commune_ban": "Commune",
    "nombre_niveau_logement": "Nombre de niveaux", "age_batiment": "Âge en 2026 (années)",
    "altitude_moyenne": "Altitude communale (m)", "zone_climatique": "Zone climatique",
    "temperature_moyenne_annuelle": "Température moyenne annuelle (°C)",
    "temperature_moyenne_hiver": "Température moyenne hivernale (°C)",
    "cout_total_5_usages": "Coût des cinq usages (€)", "code_insee_ban": "Code INSEE",
    "code_postal_ban": "Code postal", "lat": "Latitude (°)", "lon": "Longitude (°)",
}
DPE_COLORS = ["#16845b", "#57a653", "#a5bf48", "#e9cf42", "#eaa23e", "#dd6c3f", "#bb4148"]


def read_data(path):
    df = pd.read_csv(path, dtype={"code_departement_ban": "string", "code_insee_ban": "string",
                                 "code_postal_ban": "string"}, low_memory=False)
    for col in ["lat", "lon", "surface_habitable_logement", "conso_5_usages_ef",
                "nombre_niveau_logement", "age_batiment", "altitude_moyenne"]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
    return df


def filter_data(df, selections, surface=None, include_missing=True):
    mask = pd.Series(True, index=df.index)
    for col, selected in selections.items():
        if col in df and selected:
            mask &= df[col].isin(selected)
    if surface is not None and "surface_habitable_logement" in df:
        values = df.surface_habitable_logement
        mask &= values.between(*surface) | (values.isna() & include_missing)
    return df.loc[mask]


def csv_bytes(df):
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def chart_pngs(df, measure, percent=False):
    """Agrégats exacts ; seul le nuage est limité à 5 000 lignes filtrées."""
    charts = {}
    def save(name, title, draw):
        fig = Figure(figsize=(9, 5.4), layout="constrained", facecolor="#ffffff")
        ax = fig.subplots()
        ax.set_title(title, loc="left", fontsize=14, pad=18, color="#172b4d", wrap=True)
        ax.tick_params(labelsize=12)
        draw(ax)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.15)
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=140)
        charts[name] = buffer.getvalue()
        fig.clear()
    if "etiquette_dpe" in df:
        counts = df.etiquette_dpe.value_counts().reindex(list("ABCDEFG"), fill_value=0)
        unknown = len(df) - int(counts.sum())
        values = counts / max(len(df), 1) * 100 if percent else counts
        def bars(ax):
            ax.bar(values.index, values, color=DPE_COLORS)
            ax.set_ylabel("Part des logements filtrés (%)" if percent else "Nombre de logements")
        count_text = f"{len(df):,}".replace(",", " ")
        save("barres", f"Classes DPE · {count_text} logements · {unknown} sans classe A–G", bars)
    if measure in df and df[measure].notna().any():
        def histogram(ax):
            ax.hist(df[measure].dropna(), bins=40, color="#0e7490", edgecolor="white")
            ax.set_xlabel(LABELS[measure]); ax.set_ylabel("Nombre de logements")
        save("histogramme", "Distribution · " + LABELS[measure], histogram)
        if "etiquette_dpe" in df:
            groups = [(label, df.loc[df.etiquette_dpe.eq(label), measure].dropna()) for label in "ABCDEFG"]
            groups = [(label, values) for label, values in groups if len(values)]
            if groups:
                def boxes(ax):
                    ax.boxplot([v for _, v in groups], tick_labels=[k for k, _ in groups], showfliers=False)
                    ax.set_xlabel("Classe DPE"); ax.set_ylabel(LABELS[measure])
                save("boites", "Dispersion par DPE · valeurs extrêmes masquées", boxes)
    cols = ["surface_habitable_logement", "conso_5_usages_ef"]
    if all(c in df for c in cols):
        points = df.dropna(subset=cols)
        points = points.sample(min(5000, len(points)), random_state=42)
        if len(points):
            def scatter(ax):
                ax.scatter(points[cols[0]], points[cols[1]], s=7, alpha=.3, color="#0e7490", rasterized=True)
                ax.set_xlabel(LABELS[cols[0]]); ax.set_ylabel(LABELS[cols[1]])
            count_text = f"{len(points):,}".replace(",", " ")
            save("nuage", f"Surface et consommation · {count_text} logements représentés", scatter)
    return charts


def map_points(df, limit=5000):
    if not {"lat", "lon"}.issubset(df.columns):
        return pd.DataFrame(), 0
    lat, lon = pd.to_numeric(df.lat, errors="coerce"), pd.to_numeric(df.lon, errors="coerce")
    valid = np.isfinite(lat) & np.isfinite(lon) & lat.between(41, 51.5) & lon.between(-5.5, 10)
    points = df.loc[valid].sample(n=min(limit, int(valid.sum())), random_state=42).copy()
    points["lat"], points["lon"] = lat.loc[points.index], lon.loc[points.index]
    for column, fallback in [("nom_commune_ban", "Inconnue"), ("etiquette_dpe", "?"),
                             ("type_batiment", "Inconnu"), ("type_energie_principale_chauffage", "Inconnue")]:
        # Infobulle en texte brut : conserver accents/apostrophes sans pré-échappement HTML.
        points[column] = points[column].fillna(fallback).astype(str) if column in points else fallback
    for col in ["surface_habitable_logement", "conso_5_usages_ef"]:
        points[col] = points[col].round(1).astype(object).where(points[col].notna(), "Inconnue") if col in points else "Inconnue"
    colors = dict(zip("ABCDEFG", [[22,132,91], [87,166,83], [165,191,72], [233,207,66],
                                  [234,162,62], [221,108,63], [187,65,72]]))
    points["color"] = points.etiquette_dpe.map(lambda v: colors.get(v, [120,120,120]))
    keep = ["lat", "lon", "color", "nom_commune_ban", "etiquette_dpe", "type_batiment",
            "type_energie_principale_chauffage", "surface_habitable_logement", "conso_5_usages_ef"]
    return points[keep], int(valid.sum())


def map_view(frame, width=1000, height=700, padding=.08):
    """Cadrer toutes les coordonnées admissibles de la sélection, avant échantillonnage."""
    lat, lon = pd.to_numeric(frame.lat, errors="coerce"), pd.to_numeric(frame.lon, errors="coerce")
    valid = np.isfinite(lat) & np.isfinite(lon) & lat.between(41, 51.5) & lon.between(-5.5, 10)
    lat, lon = lat[valid], lon[valid]
    if not len(lat):
        raise ValueError("Aucune coordonnée pour cadrer la carte")
    if not np.isfinite([width, height, padding]).all() or width <= 0 or height <= 0 or not 0 <= padding < .5:
        raise ValueError("Dimensions ou marge de carte invalides")
    # Coordonnées en degrés Mercator : à zoom 0, le monde mesure 512 pixels.
    south, north = np.degrees(np.arcsinh(np.tan(np.radians([lat.min(), lat.max()]))))
    span_x = max(float(lon.max() - lon.min()), 1e-9)
    span_y = max(float(north - south), 1e-9)
    usable_width, usable_height = width * (1 - 2 * padding), height * (1 - 2 * padding)
    zoom_x = np.log2(usable_width * 360 / (512 * span_x))
    zoom_y = np.log2(usable_height * 360 / (512 * span_y))
    zoom = float(min(zoom_x, zoom_y, 14))
    center_lat = float(np.degrees(np.arctan(np.sinh(np.radians((south + north) / 2)))))
    return pdk.ViewState(latitude=center_lat, longitude=float((lon.min() + lon.max()) / 2), zoom=zoom, pitch=0)


def build_map(points, basemap=False, framing=None, view=None):
    layer = pdk.Layer("ScatterplotLayer", id="logements", data=points, get_position="[lon, lat]", get_fill_color="color",
                      get_radius=90, radius_min_pixels=4, radius_max_pixels=12, pickable=True, auto_highlight=True)
    # Ne pas passer map_style=None : PyDeck omet alors mapStyle du JSON et Streamlit
    # rétablit CARTO. Sans fournisseur ni argument de style, PyDeck émet la sentinelle
    # __MAP_STYLE__, reconnue par Streamlit 1.66.1 comme une désactivation explicite.
    style = {"map_style": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"} if basemap else {}
    return pdk.Deck(layers=[layer], map_provider="carto" if basemap else None, **style,
                    initial_view_state=view if view is not None else map_view(points if framing is None else framing),
                    tooltip={"text": "{nom_commune_ban} · DPE {etiquette_dpe}\n"
                             "{type_batiment} · {surface_habitable_logement} m²\n"
                             "Chauffage : {type_energie_principale_chauffage}\n"
                             "Consommation : {conso_5_usages_ef} kWh/an"})


def category_options(bundle):
    encoder = bundle["classification"].named_steps["preprocessor"].named_transformers_["encoder"]
    columns = bundle["variables"]["classification"]["qualitative_features"]
    return dict(zip(columns, [list(values) for values in encoder.categories_]))


def predict(bundle, values):
    contract = bundle["variables"]["classification"]
    for col in contract["quantitative_features"]:
        if not np.isfinite(values[col]):
            raise ValueError(f"{LABELS[col]} : valeur non finie.")
    if values["surface_habitable_logement"] <= 0 or values["nombre_niveau_logement"] < 1:
        raise ValueError("La surface doit être positive et le nombre de niveaux au moins égal à 1.")
    if values["nombre_niveau_logement"] != int(values["nombre_niveau_logement"]) or values["age_batiment"] < 0:
        raise ValueError("Le nombre de niveaux doit être entier et l’âge positif ou nul.")
    if (values["surface_habitable_logement"] > 10000 or values["nombre_niveau_logement"] > 100
            or values["age_batiment"] > 1000 or values["age_batiment"] != int(values["age_batiment"])
            or not -500 <= values["altitude_moyenne"] <= 5000):
        raise ValueError("Valeurs hors des bornes de saisie communes ; âge attendu en années entières référencées à 2026.")
    for col, options in category_options(bundle).items():
        if values[col] not in options:
            raise ValueError(f"{LABELS[col]} : catégorie non reconnue par le modèle.")
    row = pd.DataFrame([values])[contract["features"]]
    with threadpool_limits(limits=2):
        consumption = float(bundle["regression"].predict(row)[0])
        label = str(bundle["classification"].predict(row)[0])
    if not np.isfinite(consumption) or consumption < 0 or label not in "ABCDEFG":
        raise ValueError("Résultat du modèle invalide.")
    return consumption, label
