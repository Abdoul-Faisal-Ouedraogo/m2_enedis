"""API locale : même chargeur et même prédiction que Streamlit, aucun fit au lancement."""
from src.resource_limits import configure
configure()

from functools import lru_cache
from threading import Lock
import logging
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.version_store import VersionStore
from src.model_registry import load_model_version
from src.app_services import predict
from src.project_paths import ROOT

app = FastAPI(title="Habitat & énergie — API locale",version="1.0.0",
              description="Estimation pédagogique, sans valeur réglementaire. Aucun intervalle de confiance individuel.")
_prediction_lock = Lock()


@app.exception_handler(RequestValidationError)
async def invalid_request(request,exc):
    # Ne pas réinjecter les entrées non finies (NaN/Infinity) dans une réponse JSON.
    return JSONResponse(status_code=422,content={"detail":[
        {"loc":list(error["loc"]),"msg":error["msg"],"type":error["type"]} for error in exc.errors()]})


class Housing(BaseModel):
    model_config = ConfigDict(extra="forbid",allow_inf_nan=False,strict=True)
    surface_habitable_logement: float = Field(gt=0,le=10000,description="Surface habitable en m²")
    nombre_niveau_logement: int = Field(ge=1,le=100,description="Nombre entier de niveaux du logement")
    age_batiment: float = Field(ge=0,le=1000,description="2026 moins l'année de construction ; neuf imputé à zéro")
    altitude_moyenne: float = Field(ge=-500,le=5000,description="Altitude communale ou repli départemental en mètres")
    temperature_moyenne_annuelle: float | None = Field(default=None, ge=10, le=16)
    temperature_moyenne_hiver: float | None = Field(default=None, ge=3, le=9)
    type_energie_principale_chauffage: str
    type_batiment: str
    zone_climatique: Literal["H1","H2","H3"]

    @field_validator("age_batiment")
    @classmethod
    def whole_age(cls,value):
        if value != int(value):
            raise ValueError("Âge attendu en années entières, référence 2026")
        return value


class Estimation(BaseModel):
    consumption: float
    estimated_dpe: str
    units: dict[str,str]
    model_version: str
    data_version: str
    reference_year: int
    limitation: str


@lru_cache(maxsize=3)
def _cached_model(version,runtime,stamps):
    return load_model_version(version,VersionStore(runtime))


def active_bundle():
    store=VersionStore()
    active=store.active()
    folder = (ROOT / "MLmodels/final_geo_v1" if active["model"] == "final_geo_v1"
              else ROOT / "MLmodels/final_geo_v2_temperature" if active["model"] == "final_geo_v2_temperature"
              else store.folder("models",active["model"]))
    paths=list(folder.glob("*"))
    if active["model"]=="final_geo_v1":
        paths.append(ROOT/"MLmodels/final_models.json")
    stamps=tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in sorted(paths) if p.is_file())
    return active,_cached_model(active["model"],str(store.root),stamps)


def available_bundle():
    try:
        return active_bundle()
    except Exception as exc:
        logging.getLogger(__name__).warning("Modèles indisponibles : %s",type(exc).__name__)
        raise HTTPException(503,"Modèles actifs indisponibles, altérés ou incompatibles") from exc


@app.get("/health")
def health():
    active,bundle=available_bundle()
    return {"status":"ok","model_version":bundle["version"],"data_version":active["data"],"reference_year":2026}


@app.post("/predict",response_model=Estimation)
def prediction(housing:Housing):
    active,bundle=available_bundle()
    try:
        with _prediction_lock:
            consumption,label=predict(bundle,housing.model_dump())
    except (ValueError,TypeError,KeyError) as exc:
        raise HTTPException(422,str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503,"Calcul indisponible ; modèles actifs à vérifier") from exc
    return {"consumption":consumption,"estimated_dpe":label,"units":{"consumption":"kWh/an","surface":"m²","altitude":"m"},
            "model_version":bundle["version"],"data_version":active["data"],"reference_year":2026,
            "limitation":"Estimation pédagogique, sans DPE réglementaire. Fiabilité limitée sur l'existant et F/G ; pas de confiance individuelle."}
