"""Branding and backward-compatibility regression tests, with no real user Vault."""
from __future__ import annotations

from importlib import metadata
from pathlib import Path

from typer.testing import CliRunner

import syvrio
import quiet_memo
from syvrio.app.cli import app
from syvrio.infra.config import default_config_path, default_vault_path


def test_brand_package_and_legacy_namespace():
    assert syvrio.__version__ == quiet_memo.__version__
    assert syvrio.__version__ == "0.3.3"


def test_console_scripts_keep_legacy_aliases():
    scripts = {entry.name: entry.value for entry in metadata.entry_points(group="console_scripts")}
    for name in ("syvrio", "qm", "quietmemo"):
        assert scripts[name] == "syvrio.app.cli:main"


def test_version_option():
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert "Syvrio 0.3.3" in result.output


def test_old_config_and_vault_env_still_work(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("SYVRIO_CONFIG", raising=False)
    monkeypatch.delenv("SYVRIO_VAULT", raising=False)
    monkeypatch.setenv("QUIET_MEMO_CONFIG", str(tmp_path / "quiet-memo.toml"))
    monkeypatch.setenv("QUIET_MEMO_VAULT", str(tmp_path / "old-vault"))
    assert default_config_path() == tmp_path / "quiet-memo.toml"
    assert default_vault_path() == tmp_path / "old-vault"


def test_new_env_overrides_legacy_env(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("QUIET_MEMO_CONFIG", str(tmp_path / "old.toml"))
    monkeypatch.setenv("SYVRIO_CONFIG", str(tmp_path / "new.toml"))
    monkeypatch.setenv("QUIET_MEMO_VAULT", str(tmp_path / "old-vault"))
    monkeypatch.setenv("SYVRIO_VAULT", str(tmp_path / "new-vault"))
    assert default_config_path() == tmp_path / "new.toml"
    assert default_vault_path() == tmp_path / "new-vault"


def test_existing_default_vault_location_is_preserved(monkeypatch, tmp_path: Path):
    for key in ("SYVRIO_VAULT", "QUIET_MEMO_VAULT"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert default_vault_path() == tmp_path / ".quiet-memo" / "vault"
