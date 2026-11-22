"""Application locale : aucun entraînement ; téléchargement des données seulement si elles manquent."""
import streamlit as st
from src.streamlit_app import ensure_data, run

st.set_page_config(page_title="Habitat & énergie", page_icon="🏡", layout="wide")
ensure_data()
run()
