"""Comparer code/références/modèles de l'image locale aux fichiers hôtes, sans volume."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
CODE="""
import hashlib,json
from pathlib import Path
root=Path('/app')
paths=list((root/'src').rglob('*.py'))+list((root/'assets').rglob('*'))+list((root/'MLmodels/final_geo_v1').glob('*'))
paths += list((root/'MLmodels/final_geo_v2_temperature').glob('*'))
paths += [root/name for name in ['home.py','requirements-app.txt','.streamlit/config.toml','config/preparation_initial_geo_v1.json','MLmodels/final_models.json','Notebooks_Api_Traitement/1_data_preparation.ipynb','scripts/smoke_container.py']]
print(json.dumps({p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}))
"""

if __name__=="__main__":
    result=subprocess.check_output(['docker','run','--rm','--read-only','--entrypoint','python','habitat-energie:local','-c',CODE],text=True)
    image=json.loads(result)
    for relative,digest in image.items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
    assert {p.relative_to(ROOT).as_posix() for p in (ROOT/'src').rglob('*.py')}.issubset(image)
    assert "MLmodels/final_geo_v2_temperature/classification.joblib" in image
    print(f"OK : {len(image)} fichiers code, references et modeles identiques entre image et hote.")
