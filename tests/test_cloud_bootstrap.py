"""Démarrage sans données (Streamlit Cloud) : téléchargement unique, rien si tout est présent."""
import sys
import types
from pathlib import Path
from unittest.mock import patch

from src import streamlit_app
from src.project_paths import ROOT


def fake_download(root, calls):
    def main():
        calls.append(1)
        for relative in streamlit_app.REQUIRED_DATA:
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text("x")
    return types.SimpleNamespace(main=main)


def test_missing_files_trigger_one_download(tmp_path):
    calls = []
    with patch.object(streamlit_app.project_paths, "ROOT", tmp_path), \
         patch.dict(sys.modules, {"scripts.download_data": fake_download(tmp_path, calls)}):
        streamlit_app.ensure_data()
        streamlit_app.ensure_data()
        assert streamlit_app.missing_data() == []
    assert calls == [1]


def test_present_files_never_import_download(tmp_path):
    for relative in streamlit_app.REQUIRED_DATA:
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / relative).write_text("x")
    with patch.object(streamlit_app.project_paths, "ROOT", tmp_path), \
         patch.dict(sys.modules, {"scripts.download_data": None}):
        streamlit_app.ensure_data()  # un import déclencherait ImportError


def test_cloud_requirements_point_to_application_dependencies():
    lines = (ROOT / "deploy/streamlit_cloud/requirements.txt").read_text(encoding="utf-8").splitlines()
    includes = [line for line in lines if line and not line.startswith("#")]
    assert includes == ["-r ../../requirements-app.txt"]
    assert (ROOT / "deploy/streamlit_cloud" / "../../requirements-app.txt").resolve().is_file()
