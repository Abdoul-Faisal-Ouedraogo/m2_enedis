"""Contrôle réel à exécuter DANS l'image construite, sans réseau ni entraînement."""
from pathlib import Path
import argparse
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from streamlit.testing.v1 import AppTest
from src.app_services import read_data, csv_bytes, chart_pngs
from src.app_geography import read_geography, commune_proposal

paths = [ROOT / "output/cleaned_data.csv",ROOT/"output/cleaned_data_metadata.csv",ROOT/"data/communes-france-2025.csv",
         ROOT/"output/temperature_v2/temperatures_communes.csv",
         *sorted((ROOT / "MLmodels/final_geo_v1").glob("*")),
         *sorted((ROOT / "MLmodels/final_geo_v2_temperature").glob("*"))]
def hashes():
    return {str(p): hashlib.file_digest(p.open("rb"), "sha256").hexdigest() for p in paths if p.is_file()}
before = hashes()
parser=argparse.ArgumentParser()
parser.add_argument("--api-url",default=None)
args=parser.parse_args()
app = AppTest.from_file(str(ROOT / "home.py"), default_timeout=120).run()
for page in ["Contexte", "Exploration", "Carte", "Prédiction", "Gestion des données et modèles"]:
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception, app.exception
app.sidebar.radio[0].set_value("Prédiction").run()
app.button(key="single_calculate").click().run()
assert not app.exception and app.metric[0].value.endswith("kWh/an")
assert app.get("download_button")
reference = read_geography(ROOT / "data/communes-france-2025.csv", ROOT / "Notebooks_Api_Traitement/1_data_preparation.ipynb")
assert commune_proposal(reference, "69381", "69")["altitude"] == 237
proposal = commune_proposal(reference, "69381", "69")
assert proposal["temperature_moyenne_annuelle"] is not None
assert proposal["temperature_moyenne_hiver"] is not None
app.radio(key="single_geo_mode").set_value("Choisir une commune").run()
app.selectbox(key="single_department").set_value("69").run()
app.selectbox(key="single_commune_69").set_value("69123").run()
app.button(key="single_apply_geo").click().run()
assert not app.exception and app.number_input(key="single_altitude").value==237
data = read_data(ROOT / "output/cleaned_data.csv").head(500)
assert csv_bytes(data).startswith(b"\xef\xbb\xbf")
assert len(chart_pngs(data, "conso_5_usages_ef")) == 4
assert before == hashes()
if args.api_url:
    import urllib.request,json
    assert json.loads(urllib.request.urlopen(args.api_url+"/health",timeout=10).read())["status"]=="ok"
    values=app.session_state.get("single_result",{}).get("values")
    if not values:
        app.button(key="single_calculate").click().run()
        values=app.session_state["single_result"]["values"]
    request=urllib.request.Request(args.api_url+"/predict",data=json.dumps(values).encode(),headers={"Content-Type":"application/json"},method="POST")
    assert json.loads(urllib.request.urlopen(request,timeout=10).read())["units"]["consumption"]=="kWh/an"
print("OK smoke : pages initiales + gestion, prediction, commune, exports et empreintes.")
