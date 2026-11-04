from __future__ import annotations

from importlib import metadata
from pathlib import Path

import syvrio
from syvrio.app.chat_widgets import ASSISTANT_NAME
from syvrio.infra.config import (
    CONFIG_FILENAME,
    KEYRING_SERVICE,
    default_config_path,
    default_vault_path,
)
from syvrio.memory.extractor import StaticExtractor
from syvrio.memory.models import ExtractionResult
from syvrio.memory.service import MemoryService
from syvrio.infra.config import Config, LLMConfig, RetrievalConfig


def test_only_syvrio_console_script():
    scripts = {
        entry.name: entry.value
        for entry in metadata.entry_points(group="console_scripts")
    }
    assert scripts["syvrio"] == "syvrio.app.cli:main"
    assert "qm" not in scripts
    assert "quietmemo" not in scripts


def test_version_and_assistant_branding():
    assert syvrio.__version__ == "0.3.3"
    assert ASSISTANT_NAME == "Syvrio"


def test_default_paths_are_syvrio(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("SYVRIO_CONFIG", raising=False)
    monkeypatch.delenv("SYVRIO_VAULT", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.chdir(tmp_path)
    assert default_config_path() == tmp_path / "xdg" / "syvrio" / "syvrio.toml"
    assert default_vault_path() == tmp_path / ".syvrio" / "vault"
    assert CONFIG_FILENAME == "syvrio.toml"


def test_setup_defaults_to_config_directory(monkeypatch, tmp_path: Path):
    from syvrio.infra.providers import resolve_config_path

    monkeypatch.delenv("SYVRIO_CONFIG", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.chdir(tmp_path)
    assert resolve_config_path(None) == tmp_path / "xdg" / "syvrio" / "syvrio.toml"


def test_keyring_service_name():
    assert KEYRING_SERVICE == "syvrio"


def test_runtime_metadata_uses_syvrio_directory(tmp_path: Path):
    config = Config(
        vault=tmp_path / "vault",
        llm=LLMConfig(),
        retrieval=RetrievalConfig(method="keyword"),
    )
    service = MemoryService(config, extractor=StaticExtractor(ExtractionResult(memories=[])))
    service.init_vault()
    assert (config.vault / ".syvrio").is_dir()
    service.note("品牌测试条目", topic="misc")
    assert (config.vault / "memories" / "misc.md").exists()
