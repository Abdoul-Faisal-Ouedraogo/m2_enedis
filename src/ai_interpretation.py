"""Interprétation optionnelle des résultats avec Google Gemini."""
import os
import time

import requests
import streamlit as st


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_MODEL = "gemini-3.5-flash-lite"


def api_key():
    """Read the key from Streamlit secrets first, then the process environment."""
    try:
        secret = st.secrets.get("GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, TypeError):
        secret = None
    return secret or os.getenv("GEMINI_API_KEY")


def interpretation_prompt(result):
    values = result["values"]
    return (
        "Tu es un conseiller pédagogique spécialisé dans la performance énergétique "
        "des logements en France. Interprète uniquement les données fournies ci-dessous. "
        "Réponds en français, avec les sections : Analyse, Points forts et faibles, "
        "Pistes d'amélioration, Conclusion. Ne présente pas cette réponse comme un DPE "
        "réglementaire, ne donne pas de prix précis et n'invente aucune donnée.\n\n"
        f"Localisation : {result.get('location', 'non renseignée')}\n"
        f"Surface habitable : {values['surface_habitable_logement']} m²\n"
        f"Nombre de niveaux : {values['nombre_niveau_logement']}\n"
        f"Âge du bâtiment en 2026 : {values['age_batiment']} ans\n"
        f"Altitude communale : {values['altitude_moyenne']} m\n"
        f"Énergie de chauffage : {values['type_energie_principale_chauffage']}\n"
        f"Type de bâtiment : {values['type_batiment']}\n"
        f"Zone climatique : {values['zone_climatique']}\n"
        f"Consommation estimée : {result['consumption']} kWh/an\n"
        f"Classe DPE estimée par le modèle : {result['label']}\n"
    )


def get_interpretation(result):
    key = api_key()
    if not key:
        raise RuntimeError(
            "Clé Gemini absente. Configurez GEMINI_API_KEY dans "
            ".streamlit/secrets.toml ou dans les variables d'environnement."
        )
    payload = {
        "systemInstruction": {
            "parts": [{"text": "Tu produis des analyses énergétiques prudentes et compréhensibles."}]
        },
        "contents": [
            {"role": "user", "parts": [{"text": interpretation_prompt(result)}]},
        ],
        "generationConfig": {"temperature": 0.3},
    }
    response = None
    model = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
    for attempt in range(3):
        try:
            response = requests.post(
                GEMINI_URL.format(model=model),
                headers={"Content-Type": "application/json", "x-goog-api-key": key},
                json=payload,
                timeout=120,
            )
        except requests.Timeout as exc:
            if attempt == 2:
                raise RuntimeError("Le délai de réponse de Gemini a été dépassé.") from exc
            time.sleep(2 ** attempt)
            continue
        except requests.RequestException as exc:
            raise RuntimeError("Impossible de joindre l'API Gemini.") from exc
        if response.status_code not in (429, 500, 502, 503, 504) or attempt == 2:
            break
        time.sleep(2 ** attempt)
    if response is None:
        raise RuntimeError("Gemini n'a fourni aucune réponse.")
    if response.status_code in (400, 401, 403):
        raise RuntimeError("La clé Gemini est invalide, désactivée ou sans autorisation API.")
    if response.status_code == 404:
        raise RuntimeError(f"Le modèle Gemini demandé ({model}) est indisponible pour cette clé. "
                           "Définissez GEMINI_MODEL avec un modèle autorisé par votre projet.")
    if response.status_code == 429:
        raise RuntimeError("Limite temporaire de l'API Gemini atteinte. Réessayez plus tard.")
    if response.status_code in (500, 502, 503, 504):
        raise RuntimeError("Le service Gemini est temporairement indisponible. Réessayez dans quelques minutes.")
    try:
        response.raise_for_status()
        payload = response.json()
        candidates = payload.get("candidates", [])
        if not candidates:
            feedback = payload.get("promptFeedback", {})
            reason = feedback.get("blockReason") or "réponse absente"
            raise RuntimeError(f"Gemini n'a pas généré de contenu ({reason}).")
        content = candidates[0]["content"]["parts"][0]["text"]
    except requests.RequestException as exc:
        raise RuntimeError(f"Impossible de joindre l'API Gemini : {exc}") from exc
    except (ValueError, KeyError, IndexError) as exc:
        raise RuntimeError("Gemini a renvoyé une réponse dans un format inattendu.") from exc
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Gemini a renvoyé une réponse vide.")
    return content.strip()
