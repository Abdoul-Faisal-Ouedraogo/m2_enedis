"""Point d'entrée Streamlit Community Cloud : exécute home.py depuis la racine du dépôt."""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT / "home.py"), run_name="__main__")
