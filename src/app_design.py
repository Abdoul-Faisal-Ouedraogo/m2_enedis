"""Identité visuelle locale et composants de présentation."""
import streamlit as st
import pandas as pd

from src import project_paths
from src.app_services import LABELS, DPE_COLORS

NAV_LABELS = {"Contexte": "🏡 Accueil", "Exploration": "📊 Exploration", "Carte": "🗺️ Carte", "Prédiction": "✨ Prédiction"}
NAV_LABELS["Interprétation IA"] = "🤖 Interprétation IA"
NAV_LABELS["Gestion des données et modèles"] = "⚙️ Gestion"
SIDEBAR_LABELS = {
    "Contexte": "Accueil",
    "Exploration": "Contexte",
    "Carte": "Cartographie des logements",
    "Prédiction": "Prédiction énergétique",
    "Interprétation IA": "Interprétation IA des résultats",
    "Gestion des données et modèles": "Gestion des données et modèles",
}
PAGE_META = {
    "Contexte": ("Accueil", "Une présentation générale de l’application et de son étude."),
    "Exploration": ("Contexte", "Explorez et visualisez les données disponibles sur les logements."),
    "Carte": ("Cartographier le territoire", "Repérez les logements et leurs classes énergétiques."),
    "Prédiction": ("Estimer la performance", "Obtenez une estimation à partir des caractéristiques du logement."),
    "Gestion des données et modèles": ("Piloter les modèles", "Contrôlez les versions de données et de modèles utilisées."),
}


def number(value, decimals=0):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def styles():
    st.markdown("""<style>
    :root {
        --ink: #172b4d;
        --muted: #64748b;
        --navy: #12233f;
        --navy-soft: #1d3557;
        --accent: #0e7490;
        --accent-light: #e0f2f7;
        --amber: #d97706;
        --surface: #ffffff;
        --canvas: #f4f7fb;
        --line: #dbe4ef;
    }
    .stApp {background:var(--canvas);color:var(--ink);}
    h1,h2,h3 {color:var(--ink);letter-spacing:-.03em;font-weight:750;}
    h1 {font-size:clamp(2rem,4vw,3.15rem);}
    h2 {margin-top:1.7rem;}
    .block-container {max-width:1480px;padding-top:2.2rem;padding-bottom:4rem;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#07516a 0%,#08715e 47%,#20b52d 100%);border-right:0;color:#fff;min-width:255px;}
    [data-testid="stSidebar"] * {color:#e8eef7;}
    [data-testid="stSidebar"] hr {border-color:rgba(5,65,57,.48);margin:1.35rem 0;}
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {display:none;}
    [data-testid="stSidebar"] [data-baseweb="radio"] {gap:0.25rem;}
    [data-testid="stSidebar"] [data-baseweb="radio"] > div {display:block;width:100%;}
    [data-testid="stSidebar"] [data-baseweb="radio"] input {display:none!important;}
    [data-testid="stSidebar"] [data-baseweb="radio"] label {display:flex;align-items:center;min-height:53px;width:100%;box-sizing:border-box;padding:0 19px;margin:6px 0;background:rgba(71,181,173,.38);border-radius:10px;font-weight:650;transition:all .15s ease;cursor:pointer;}
    [data-testid="stSidebar"] [data-baseweb="radio"] label:hover {background:rgba(61,205,177,.6);border-radius:10px;}
    [data-testid="stSidebar"] [data-baseweb="radio"] label:has(input:checked) {background:#117d5b;border-left:4px solid #31e447;border-radius:10px;padding-left:15px;}
    [data-testid="stMetric"] {background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:0 6px 18px rgba(18,35,63,.05);}
    [data-testid="stMetricLabel"] {color:var(--muted);font-weight:650;}
    [data-testid="stMetricValue"] {font-size:clamp(1.5rem,2.3vw,2.25rem);color:var(--navy);font-weight:760;}
    [data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--line);border-radius:18px;background:rgba(255,255,255,.72);}
    .stButton > button {border-radius:10px;border-color:var(--line);font-weight:650;transition:all .15s ease;}
    .stButton > button:hover {border-color:var(--accent);color:var(--accent);transform:translateY(-1px);}
    .stButton > button[kind="primary"] {background:var(--accent);border-color:var(--accent);color:white;}
    .stDownloadButton > button {border-radius:10px;}
    .dpe-scale {display:flex;gap:5px;margin:16px 0 8px;flex-wrap:wrap;}
    .dpe-grade {flex:1;min-width:30px;text-align:center;padding:10px 4px;border-radius:7px;color:#172b4d;font-size:1.1rem;font-weight:750;border:2px solid transparent;}
    .dpe-grade.active {outline:3px solid var(--navy);outline-offset:2px;transform:translateY(-3px);}
    .eyebrow {color:var(--accent);letter-spacing:.14em;font-size:.78rem;font-weight:800;text-transform:uppercase;}
    .sidebar-brand {text-align:center;padding:.1rem 0 .4rem;}
    .sidebar-logo {position:relative;display:grid;place-items:center;width:130px;height:114px;margin:0 auto 1.05rem;border-radius:13px;background:rgba(5,73,78,.78);color:#fff;box-shadow:0 5px 13px rgba(0,40,40,.28);border:1px solid rgba(255,255,255,.28);overflow:hidden;animation:sidebar-rise .55s ease-out both;}
    .sidebar-logo::after {content:"";position:absolute;inset:-80% 35%;background:rgba(255,255,255,.22);transform:rotate(25deg);animation:logo-shine 4s ease-in-out 1s infinite;}
    .sidebar-logo-mark {position:relative;z-index:1;display:grid;place-items:center;width:58px;height:58px;border:5px solid #8ce2b0;border-radius:50%;background:linear-gradient(145deg,#163d79 0 43%,#42bd78 43% 68%,#0d6d69 68%);color:#fff;font-size:1.35rem;font-weight:850;box-shadow:0 0 0 3px rgba(255,255,255,.9),0 4px 10px rgba(0,0,0,.2);animation:logo-float 3.5s ease-in-out infinite;}
    .sidebar-logo-name {font-size:.95rem;font-weight:850;color:#fff!important;letter-spacing:.04em;margin-top:.25rem;}
    .sidebar-title {font-size:1.42rem;font-weight:800;letter-spacing:.01em;margin:.1rem 0 1.25rem;}
    .sidebar-subtitle {font-size:.92rem;font-weight:650;line-height:1.45;margin-bottom:2.1rem;}
    .sidebar-sources {font-size:.84rem;text-align:left;line-height:1.5;}
    .sidebar-sources strong {font-size:.88rem;}
    .sidebar-sources ul {padding-left:1.05rem;margin:.5rem 0 0;}
    [data-testid="stSidebar"] [data-baseweb="radio"] label:nth-child(1) {animation:sidebar-rise .35s .05s ease-out both;}
    [data-testid="stSidebar"] [data-baseweb="radio"] label:nth-child(2) {animation:sidebar-rise .35s .1s ease-out both;}
    [data-testid="stSidebar"] [data-baseweb="radio"] label:nth-child(3) {animation:sidebar-rise .35s .15s ease-out both;}
    [data-testid="stSidebar"] [data-baseweb="radio"] label:nth-child(4) {animation:sidebar-rise .35s .2s ease-out both;}
    [data-testid="stSidebar"] [data-baseweb="radio"] label:nth-child(5) {animation:sidebar-rise .35s .25s ease-out both;}
    @keyframes sidebar-rise {from {opacity:0;transform:translateY(8px);} to {opacity:1;transform:translateY(0);}}
    @keyframes logo-float {0%,100% {transform:translateY(0) rotate(0deg);} 50% {transform:translateY(-3px) rotate(1deg);}}
    @keyframes logo-shine {0%,55% {transform:translateX(-150%) rotate(25deg);} 75%,100% {transform:translateX(220%) rotate(25deg);}}
    .hero-note {padding:12px 16px;border-left:4px solid var(--amber);background:#fffaf0;border-radius:0 10px 10px 0;color:#5b431e;margin:1rem 0 1.5rem;}
    .page-subtitle {color:var(--muted);font-size:1.05rem;margin-top:-.7rem;margin-bottom:1.5rem;}
    .section-kicker {color:var(--accent);font-size:.76rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;margin-top:2.2rem;margin-bottom:-.8rem;}
    .feature-index {display:grid;place-items:center;width:34px;height:34px;border-radius:10px;background:var(--accent-light);color:var(--accent);font-size:.8rem;font-weight:800;margin-bottom:.7rem;}
    .hero-panel {display:flex;align-items:center;justify-content:space-between;min-height:250px;padding:2.4rem 3.2rem;margin:.5rem 0 1.4rem;border-radius:24px;overflow:hidden;background:linear-gradient(115deg,#12233f 0%,#1d3557 65%,#0e7490 100%);box-shadow:0 14px 30px rgba(18,35,63,.16);}
    .hero-copy {max-width:680px;}
    .hero-copy h1 {color:white;margin:0 0 .8rem;line-height:1.08;}
    .hero-copy p {color:#d5e4f2;font-size:1.08rem;max-width:560px;margin:0;line-height:1.6;}
    .hero-symbol {position:relative;color:#6ed1d2;font-size:9rem;font-weight:200;line-height:1;opacity:.8;padding-right:2rem;}
    .hero-symbol span {position:absolute;color:#f5b544;font-size:3rem;right:0;top:-.3rem;}
    @media(max-width:700px) {
        .block-container {padding:1.3rem 1rem 2.5rem;}
        h1 {font-size:2rem;}
        .dpe-grade {padding:8px 2px;}
        [data-testid="stMetric"] {padding:14px;}
        .hero-panel {min-height:220px;padding:1.8rem 1.5rem;}
        .hero-symbol {font-size:5rem;padding-right:0;}
    }
    </style>""", unsafe_allow_html=True)


def scale(label=None):
    pieces = []
    for letter, color in zip("ABCDEFG", DPE_COLORS):
        selected = letter == label
        pieces.append(f'<span class="dpe-grade{" active" if selected else ""}" style="background:{color};color:{"white" if letter in "AG" else "#102a20"}" aria-label="Classe {letter}{", prédite" if selected else ""}">{letter}{" ✓" if selected else ""}</span>')
    st.markdown('<div class="dpe-scale" role="img" aria-label="Échelle DPE de A à G">' + "".join(pieces) + '</div>', unsafe_allow_html=True)
    st.caption(f"Classe prédite : {label}" if label else "A : moins énergivore → G : plus énergivore · gris : classe inconnue sur la carte")


def go(page):
    st.session_state.page = page


def page_header(page):
    title, subtitle = PAGE_META.get(page, (page, "Analyse de la performance énergétique des logements."))
    st.markdown('<p class="eyebrow">App Enedis · performance énergétique</p>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)


def context(df):
    st.markdown('<p class="eyebrow">Observer · Comprendre · Estimer</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-panel"><div class="hero-copy">'
        '<h1>La donnée au service<br>de l’habitat durable</h1>'
        '<p>Explorez les diagnostics énergétiques, identifiez les tendances '
        'et estimez la performance de nouveaux logements.</p></div>'
        '<div class="hero-symbol">⌂<span>+</span></div></div>',
        unsafe_allow_html=True,
    )
    a, b = st.columns(2)
    a.button("Explorer les logements", icon="📊", type="primary", width="stretch", on_click=go, args=("Exploration",))
    b.button("Estimer un logement", icon="✨", width="stretch", on_click=go, args=("Prédiction",))
    if df is not None:
        a, b, c = st.columns(3)
        a.metric("Logements dans l’étude", number(len(df)))
        b.metric("Départements renseignés", df.code_departement_ban.nunique() if "code_departement_ban" in df else "—")
        c.metric("Classes énergétiques", "A à G")
    st.markdown('<p class="section-kicker">Votre espace d’analyse</p>', unsafe_allow_html=True)
    st.subheader("Un parcours simple, trois façons de comprendre")
    for column, title, description in zip(st.columns(3), ["01 · Explorer", "02 · Situer", "03 · Estimer"],
        ["Filtrez les logements et découvrez leurs surfaces, consommations et classes DPE.",
         "Parcourez la carte et consultez les caractéristiques des logements représentés.",
         "Renseignez un logement ou comparez deux profils, puis emportez un résumé PDF."]):
        with column.container(border=True):
            st.markdown(f'<div class="feature-index">{title.split(" · ")[0]}</div>', unsafe_allow_html=True)
            st.subheader(title.split(" · ")[1])
            st.write(description)
    st.markdown('<div class="hero-note"><strong>À garder en tête.</strong> '
                "Cette étude est pédagogique : l’échantillon ne représente pas tout le parc français "
                "et les estimations ne remplacent pas un diagnostic DPE.</div>", unsafe_allow_html=True)
    with st.expander("D’où viennent les données ?"):
        st.write("Les diagnostics ADEME de logements existants et neufs sont enrichis par les références locales "
                 "des communes : altitude moyenne et zones climatiques H1, H2, H3. La géographie BAN permet les rapprochements.")
        st.markdown("[Données ADEME](https://data.ademe.fr/) · [Base Adresse Nationale](https://adresse.data.gouv.fr/)")
        st.write("Les extractions historiques étaient plafonnées à 5 000 lignes par département et par source, "
                 "sans échantillonnage temporel représentatif. Le nettoyage et la part du neuf influencent les distributions.")
    with st.expander("Comprendre les unités et les limites"):
        st.write("La consommation est l’énergie finale totale des cinq usages en kWh/an : chauffage, eau chaude, "
                 "refroidissement, éclairage et auxiliaires. Elle n’est ni une facture ni une consommation par m².")
        st.write("L’âge est référencé à 2026 ; le neuf a reçu un âge nul par imputation. L’altitude est communale, "
                 "ou remplacée par la moyenne départementale des communes du référentiel. Les sous-zones ne sont pas inventées. "
                 "Les positions BAN ne certifient pas l’adresse ; plusieurs logements peuvent se superposer.")
    with st.expander("Détail des données chargées et méthode"):
        from src.version_store import VersionStore
        st.caption("Version de données chargée : " + VersionStore().active()["data"] + ". Aucun appel API, téléchargement ou entraînement au démarrage.")
        if df is not None:
            st.dataframe(pd.DataFrame({"Variable": [LABELS.get(c,c) for c in df], "Colonne technique": df.columns,
                                       "Valeurs absentes": df.isna().sum().values}), hide_index=True, width="stretch")
        st.write("Les modèles finaux sont contrôlés au chargement. Les résultats détaillés et leurs limites sont disponibles dans la page Prédiction.")
    with st.expander("Crédits et travaux du groupe"):
        st.write("Projet de groupe m2_enedis. Sources : ADEME, Enedis, Base Adresse Nationale et référentiel communes-france-2025. "
                 "Contribution : Abdoul Faisal OUEDRAOGO - Mounir BEKKAR - Nouhayla BOUAOUICH")
