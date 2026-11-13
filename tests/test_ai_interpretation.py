from unittest.mock import patch

from src.ai_interpretation import get_interpretation


RESULT = {
    "values": {
        "surface_habitable_logement": 80,
        "nombre_niveau_logement": 1,
        "age_batiment": 30,
        "altitude_moyenne": 150,
        "type_energie_principale_chauffage": "Gaz",
        "type_batiment": "Maison",
        "zone_climatique": "H2",
    },
    "consumption": 12000,
    "label": "D",
    "location": "Lyon (69)",
}


def test_gemini_interpretation_request():
    response = type("Response", (), {
        "status_code": 200,
        "json": lambda self: {"candidates": [{
            "content": {"parts": [{"text": "Analyse"}]}
        }]},
        "raise_for_status": lambda self: None,
    })()
    with patch("src.ai_interpretation.api_key", return_value="test-key"), \
         patch("src.ai_interpretation.requests.post", return_value=response) as post:
        assert get_interpretation(RESULT) == "Analyse"
    request = post.call_args
    assert request.args[0].endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert request.kwargs["headers"]["x-goog-api-key"] == "test-key"
    assert request.kwargs["json"]["contents"][0]["role"] == "user"
