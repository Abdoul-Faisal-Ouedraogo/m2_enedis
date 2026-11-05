"""Actions Expert uniquement sur clic et confirmation explicites."""
from datetime import date, datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

from src.data_requesters.ademe import Ademe_API_requester
from src.expert_data import prepare_version, PreparationRejected, audit_existing_version
from src.preparation_audit import DUPLICATE_CODES
from src.project_paths import ROOT
from src.version_store import VersionStore


@st.cache_data(show_spinner="Analyse du bilan historique…",max_entries=8)
def historical_summary(version,runtime,stamps):
    return audit_existing_version(version,VersionStore(runtime))


def data_summary(info):
    duplicates=int(info.get("duplicates",0))
    rejected=int(info["rejected"])-duplicates
    for col,label,value in zip(st.columns(5),["Reçus","Conservés","Doublons","Remplacés","Rejetés"],
                               [info["received"],info["kept_new"],duplicates,info.get("replaced_base",0),rejected]):
        col.metric(label,f"{value:,}".replace(","," "))
    st.caption("Reçus = conservés + doublons + rejetés. Les doublons ne sont pas recomptés dans les rejets. "
               "Remplacés : anciens diagnostics écartés de cette copie, sans supprimer les originaux.")
    audit=info.get("audit")
    if audit:
        reasons=[{"Type":"Doublon" if code in DUPLICATE_CODES else "Rejet","Raison":audit["labels"][code],"Effectif":count}
                 for code,count in audit["primary_counts"].items() if count]
        if reasons:
            st.markdown("**Pourquoi certaines lignes ne sont pas conservées ?**")
            st.dataframe(pd.DataFrame(reasons),hide_index=True,width="stretch")
            st.caption("Un motif principal par ligne, selon l’ordre des contrôles. D’autres champs peuvent aussi manquer sur la même ligne ; les détails techniques donnent les motifs cumulés, non additionnables.")
        else:
            st.success("Toutes les lignes reçues ont été conservées.")
    else:
        st.warning("Ce bilan ancien ne contient pas de motifs détaillés reproductibles. Aucun motif n’est inventé.")
    if info.get("audit_read_only"):
        st.info("Bilan historique analysé en lecture seule : la copie préparée n’a pas été modifiée ni activée.")
    if "stable_comparison" in info:
        alternative=info["stable_comparison"]
        st.caption(f"Avec les bornes initiales figées, ce lot aurait {alternative['kept_new']} lignes conservées et {alternative['rejected']} non conservées. Cette comparaison ne crée ni n’active de version.")
    with st.expander("Détails techniques du bilan (JSON)",expanded=False):
        st.json(info)


def render_management():
    st.title("⚙️ Gestion des données et modèles")
    st.write("Préparer une version ne l’active pas. Les fichiers d’origine et les modèles de référence sont conservés.")
    store = VersionStore()
    active = store.active()
    st.caption(f"Données actives : {active['data']} · Modèles actifs : {active['model']}")
    with st.expander("Recevoir de nouveaux diagnostics", expanded=True):
        a, b = st.columns(2)
        dep = a.text_input("Département à actualiser", value="69", key="collect_department")
        source = b.selectbox("Source ADEME", ["existant", "neuf"])
        start = a.date_input("Réception à partir du", value=date(2025, 1, 1))
        end = b.date_input("Réception jusqu’au", value=datetime.now(ZoneInfo("Europe/Paris")).date())
        limit = st.number_input("Volume maximal reçu", min_value=1, max_value=5000, value=500, step=100)
        approved = st.checkbox("Je souhaite lancer cette collecte réseau bornée et préparer une copie locale.")
        if st.button("Collecter et préparer une version", disabled=not approved, key="collect_data"):
            try:
                progress = st.progress(0, text="Réception ADEME…")
                raw = Ademe_API_requester(size=500).bounded_lines_by_date(dep.strip(), start, end, int(limit),
                    neuf=source == "neuf", progress=lambda done,total: progress.progress(min(done/total,1.0), text=f"{done} / {total} lignes reçues"))
                info = prepare_version(raw, source, store)
                st.session_state.last_prepared = info["id"]
                st.session_state.review_data_version=info["id"]
                st.success("Nouvelle version préparée, non activée.")
            except PreparationRejected as exc:
                st.warning("Aucune version créée : toutes les lignes sont des doublons ou des rejets.")
                data_summary(exc.summary)
            except Exception as exc:
                st.error(f"Actualisation interrompue : {exc}. Les versions actives sont conservées.")
    with st.expander("Valider et activer des données", expanded=True):
        entries = store.list_versions("datasets")
        if entries:
            version = st.selectbox("Version de données à examiner", [x["id"] for x in entries],key="review_data_version")
            info = store.manifest("datasets", version)
            if "audit" not in info:
                try:
                    paths=[store.folder("datasets",version)/name for name in ["manifest.json","data.csv","metadata.csv","received.json"]]
                    paths+=list(store.data_paths(info["base"],check=False))
                    paths+=[ROOT/"data/communes-france-2025.csv",ROOT/"config/preparation_initial_geo_v1.json"]
                    stamps=tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in paths)
                    info=historical_summary(version,str(store.root),stamps)
                except (OSError,ValueError,KeyError) as exc:
                    st.warning(f"Audit historique indisponible : {exc}")
            data_summary(info)
            confirm = st.checkbox("J’ai vérifié le bilan, les rejets et les limites de cette version.")
            if st.button("Valider cette version de données", disabled=not confirm, key="validate_data"):
                try:
                    store.validate_data(version)
                    st.success("Version validée ; activation encore séparée.")
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.info("Aucune nouvelle version préparée. Les données initiales restent disponibles.")
        choices = ["initial"] + [x["id"] for x in store.list_versions("datasets") if x["status"] == "validated"]
        selected = st.selectbox("Données à rendre actives", choices)
        confirm_active = st.checkbox("Je confirme le changement des données actives.")
        if st.button("Activer les données choisies", disabled=not confirm_active, key="activate_data"):
            try:
                store.activate(data=selected)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    if st.button("Revenir à la sélection précédente", disabled=not active.get("previous"), key="rollback_versions"):
        try:
            store.rollback()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    with st.expander("Entraîner deux nouveaux modèles", expanded=False):
        st.write("Deux forêts, deux threads. Réglages finaux conservés, sans recherche sur le test. Réceptions avant 2024 : entraînement ; 2024 : validation ; depuis 2025 : réservé. Les nouveautés récentes ne sont donc pas apprises avec ce protocole fixe.")
        st.caption("Le calcul peut être long sur toute la base. Aucun modèle actif n’est remplacé automatiquement.")
        choices = ["initial"] + [x["id"] for x in store.list_versions("datasets") if x["status"]=="validated"]
        training_data = st.selectbox("Version validée pour l’entraînement",choices)
        approved_training = st.checkbox("Je confirme l’entraînement explicite des deux modèles sur cette version.")
        if st.button("Entraîner une nouvelle version",disabled=not approved_training,key="train_models"):
            from src.expert_training import train_version
            progress = st.progress(0,text="Préparation de l’entraînement…")
            try:
                result = train_version(training_data,store,progress=lambda value,text:progress.progress(value,text=text))
                st.success("Nouvelle version prête, non activée.")
                with st.expander("Détails techniques de l’entraînement (JSON)",expanded=False):
                    st.json(result)
            except Exception as exc:
                st.error(f"Entraînement échoué : {exc}. Consulter le journal de version ; les modèles actifs sont conservés.")
    with st.expander("Choisir les modèles actifs", expanded=True):
        entries = store.list_versions("models")
        for item in entries:
            st.caption(f"{item['id']} · {item['status']}" + (" · " + item.get("error","") if item["status"]=="failed" else ""))
        choices = ["final_geo_v1", "final_geo_v2_temperature"] + [x["id"] for x in entries if x["status"]=="ready"]
        selected_model = st.selectbox("Version de modèles compatible à activer",choices)
        confirm_model = st.checkbox("Je confirme le changement des modèles actifs et l’invalidation des anciens résultats.")
        if st.button("Activer les modèles choisis",disabled=not confirm_model,key="activate_models"):
            try:
                store.activate(model=selected_model)
                st.rerun()
            except Exception as exc:
                st.error(f"Activation refusée : {exc}")
