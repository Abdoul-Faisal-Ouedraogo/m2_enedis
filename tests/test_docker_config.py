"""Configuration seulement : ces tests ne prétendent pas construire une image."""
import json
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]


def test_compose_local_ports_and_read_only_mounts():
    if not shutil.which("docker"):
        pytest.skip("Client Docker absent : validation Compose bloquée")
    result=subprocess.run(["docker","compose","config","--format","json"],cwd=ROOT,capture_output=True,text=True,check=True)
    compose=json.loads(result.stdout)
    for name in ["application","api"]:
        service=compose["services"][name]
        assert service["read_only"]
        assert all(port["host_ip"]=="127.0.0.1" for port in service["ports"])
        binds=[v for v in service["volumes"] if v["type"]=="bind"]
        assert len(binds)==4 and all(v["read_only"] for v in binds)
        assert all(not v["bind"].get("create_host_path", False) for v in binds)
        assert not any("ademe_data" in v["source"] for v in binds)


def test_docker_context_default_deny_and_no_raw_data_copy():
    lines=(ROOT/".dockerignore").read_text().splitlines()
    assert "**" in lines and "**/*.csv" in lines and "**/*.pdf" in lines
    assert "**/.env*" in lines and "**/*secret*" in lines
    assert not any(line.startswith("!data") or line.startswith("!runtime") or line.startswith("!output") for line in lines)
    dockerfile=(ROOT/"Dockerfile").read_text()
    assert "COPY . " not in dockerfile
    assert "USER app" in dockerfile
    assert "COPY MLmodels/final_geo_v1/" in dockerfile
    assert "pip install" in dockerfile and "train_" not in dockerfile


def test_test_override_does_not_publish_nominal_ports_or_widen_interface():
    if not shutil.which("docker"):
        pytest.skip("Client Docker absent")
    result=subprocess.run(["docker","compose","-f","compose.yaml","-f","compose.test.yaml","config","--format","json"],
                          cwd=ROOT,capture_output=True,text=True,check=True)
    services=json.loads(result.stdout)["services"]
    assert len(services["application"]["ports"])==1 and services["application"]["ports"][0]["published"]=="18501"
    assert len(services["api"]["ports"])==1 and services["api"]["ports"][0]["published"]=="18000"
    assert all(port["host_ip"]=="127.0.0.1" for service in services.values() for port in service["ports"])
