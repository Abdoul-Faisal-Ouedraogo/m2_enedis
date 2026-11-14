"""Artefacts éditables et contraintes de pagination réellement rendues."""
from pathlib import Path
from xml.etree import ElementTree as ET
import json
import pytest

from scripts.render_submission_docs import render
from src.project_paths import ROOT


@pytest.mark.parametrize("name,pages",[("guide_utilisateur",2),("documentation_a_voir",2),("rapport_ml_final",5)])
def test_markdown_page_counts(name,pages,tmp_path):
    assert render(ROOT/"doc"/(name+".md"),tmp_path/(name+".pdf"))==pages


def test_drawio_is_uncompressed_editable_xml_with_valid_edges():
    root=ET.parse(ROOT/"doc/architecture.drawio").getroot()
    assert root.tag=="mxfile" and root.find(".//mxGraphModel") is not None
    cells=root.findall(".//mxCell")
    ids={cell.attrib["id"] for cell in cells}
    assert len(ids)==len(cells)
    for edge in [c for c in cells if c.get("edge")=="1"]:
        assert edge.get("source") in ids and edge.get("target") in ids


def test_report_key_scores_are_real_saved_results():
    results=json.loads((ROOT/"MLmodels/final_geo_v1/results.json").read_text(encoding="utf-8"))
    text=(ROOT/"doc/rapport_ml_final.md").read_text(encoding="utf-8")
    assert f"{results['classification']['accuracy']*100:.2f}".replace(".",",") in text
    assert f"{results['regression']['mae']:,.2f}".replace(","," ").replace(".",",") in text
    assert "38,70 %" in text and "5,82 %" in text
