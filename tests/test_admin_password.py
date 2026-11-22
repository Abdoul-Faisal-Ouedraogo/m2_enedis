"""Mot de passe de la page Gestion : actif seulement si ENEDIS_ADMIN_PASSWORD est défini."""
from streamlit.testing.v1 import AppTest


def management():
    from src.expert_ui import render_management
    render_management()


ACTION_KEYS = {"collect_data", "validate_data", "activate_data", "rollback_versions", "train_models", "activate_models"}


def page(monkeypatch, tmp_path, password=None):
    monkeypatch.setenv("ENEDIS_RUNTIME", str(tmp_path))
    if password is None:
        monkeypatch.delenv("ENEDIS_ADMIN_PASSWORD", raising=False)
    else:
        monkeypatch.setenv("ENEDIS_ADMIN_PASSWORD", password)
    return AppTest.from_function(management, default_timeout=30).run()


def action_buttons(ui):
    return {b.key for b in ui.button} & ACTION_KEYS


def test_without_variable_actions_are_shown_without_password(monkeypatch, tmp_path):
    ui = page(monkeypatch, tmp_path)
    assert not ui.exception
    assert not [t for t in ui.text_input if t.key == "admin_password"]
    assert {"collect_data", "rollback_versions", "train_models", "activate_models"} <= action_buttons(ui)


def test_password_required_shows_only_read_only_status(monkeypatch, tmp_path):
    ui = page(monkeypatch, tmp_path, "secret-de-test")
    assert not ui.exception
    assert action_buttons(ui) == set()
    assert any("Modèles actifs" in c.value for c in ui.caption)
    assert any("lecture seule" in i.value for i in ui.info)


def test_wrong_password_keeps_actions_hidden(monkeypatch, tmp_path):
    ui = page(monkeypatch, tmp_path, "secret-de-test")
    ui.text_input(key="admin_password").input("mauvais").run()
    assert action_buttons(ui) == set()
    assert any("incorrect" in e.value for e in ui.error)


def test_right_password_unlocks_actions_for_the_session(monkeypatch, tmp_path):
    ui = page(monkeypatch, tmp_path, "secret-de-test")
    ui.text_input(key="admin_password").input("secret-de-test").run()
    assert {"collect_data", "rollback_versions", "train_models", "activate_models"} <= action_buttons(ui)
    ui.run()
    assert {"collect_data", "train_models"} <= action_buttons(ui)
