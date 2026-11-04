from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "migrate_to_syvrio.py"
_spec = importlib.util.spec_from_file_location("migrate_to_syvrio", SCRIPT)
migrate_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules["migrate_to_syvrio"] = migrate_mod
_spec.loader.exec_module(migrate_mod)


def make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "memories").mkdir(parents=True)
    (vault / "sessions").mkdir()
    meta = vault / ".quiet-memo"
    meta.mkdir()
    (meta / "pending.jsonl").write_text('{"id": "p1"}\n', encoding="utf-8")
    (meta / "audit.jsonl").write_text('{"event": "a1"}\n', encoding="utf-8")
    (meta / "vectors.npz").write_bytes(b"cache")
    (meta / "vault.lock").write_bytes(b"")
    (vault / "sessions" / "s-1.jsonl").write_text('{"type": "meta"}\n', encoding="utf-8")
    (vault / "memories" / "01-test.md").write_text(
        "---\ntopic: test\ntitle: Test\ncreated: 2026-01-01\nupdated: 2026-01-01\n---\n"
        "- 2026-01-01T00:00:00 — 普通条目 `id=e1` `status=active`\n"
        "- 2026-01-01T00:00:01 — 特殊条目 `id=e2` "
        "`source=~qm-escaped~a%60b%0A` `note=~qm-escaped~x%7Ey`\n",
        encoding="utf-8",
    )
    return vault


def make_config(tmp_path: Path) -> Path:
    config = tmp_path / "quiet-memo.toml"
    config.write_text('vault = "~/vault"\n', encoding="utf-8")
    return config


def run(vault: Path, config: Path, new_config: Path, *, apply: bool, keyring: bool = False):
    return migrate_mod.migrate(
        vault, config, new_config, apply=apply,
        backup_root=vault.parent, keyring=keyring,
    )


def test_dry_run_does_not_touch_data(tmp_path):
    vault = make_vault(tmp_path)
    config = make_config(tmp_path)
    new_config = tmp_path / "config" / "syvrio.toml"
    report = run(vault, config, new_config, apply=False)
    assert report["tag_values"] == 2
    assert (vault / ".quiet-memo").exists()
    assert not (vault / ".syvrio").exists()
    assert not new_config.exists()
    assert "~qm-escaped~" in (vault / "memories" / "01-test.md").read_text(encoding="utf-8")


def test_apply_migrates_metadata_tags_and_config(tmp_path):
    vault = make_vault(tmp_path)
    config = make_config(tmp_path)
    new_config = tmp_path / "config" / "syvrio.toml"
    report = run(vault, config, new_config, apply=True)
    assert not (vault / ".quiet-memo").exists()
    assert (vault / ".syvrio" / "pending.jsonl").exists()
    assert (vault / ".syvrio" / "audit.jsonl").exists()
    assert not (vault / ".syvrio" / "vectors.npz").exists()
    assert not (vault / ".syvrio" / "vault.lock").exists()
    text = (vault / "memories" / "01-test.md").read_text(encoding="utf-8")
    assert "~qm-escaped~" not in text
    assert text.count("~syvrio-escaped~") == 2
    assert "`id=e1`" in text and "`id=e2`" in text
    assert json.loads((vault / ".syvrio" / "pending.jsonl").read_text())["id"] == "p1"
    assert new_config.exists()
    if sys.platform != "win32":
        assert (new_config.stat().st_mode & 0o777) == 0o600
    assert Path(report["backup"]).exists()
    assert (Path(report["backup"]) / ".quiet-memo" / "pending.jsonl").exists()


def test_repeat_apply_is_idempotent(tmp_path):
    vault = make_vault(tmp_path)
    config = make_config(tmp_path)
    new_config = tmp_path / "config" / "syvrio.toml"
    run(vault, config, new_config, apply=True)
    before = (vault / ".syvrio" / "pending.jsonl").read_bytes()
    report = run(vault, config, new_config, apply=True)
    assert report["already_migrated"] is True
    assert (vault / ".syvrio" / "pending.jsonl").read_bytes() == before
    assert not (vault / ".quiet-memo").exists()


def test_conflicting_metadata_directories_stop(tmp_path):
    vault = make_vault(tmp_path)
    (vault / ".syvrio").mkdir()
    with pytest.raises(migrate_mod.MigrationError, match="同时存在"):
        run(vault, make_config(tmp_path), tmp_path / "new.toml", apply=False)


def test_failure_keeps_old_metadata(tmp_path):
    vault = make_vault(tmp_path)
    (vault / ".quiet-memo" / "unexpected-dir").mkdir()
    with pytest.raises(migrate_mod.MigrationError, match="子目录"):
        run(vault, make_config(tmp_path), tmp_path / "new.toml", apply=True)
    assert (vault / ".quiet-memo" / "pending.jsonl").exists()
    assert not (vault / ".syvrio").exists()


def test_middle_jsonl_corruption_stops(tmp_path):
    vault = make_vault(tmp_path)
    (vault / ".quiet-memo" / "pending.jsonl").write_text(
        '{"id": "p1"}\nnot-json\n{"id": "p2"}\n', encoding="utf-8"
    )
    with pytest.raises(migrate_mod.MigrationError, match="中间行损坏"):
        run(vault, make_config(tmp_path), tmp_path / "new.toml", apply=False)


def test_config_conflict_stops(tmp_path):
    vault = make_vault(tmp_path)
    old = make_config(tmp_path)
    new = tmp_path / "syvrio.toml"
    new.write_text('vault = "other"\n', encoding="utf-8")
    with pytest.raises(migrate_mod.MigrationError, match="内容不同"):
        run(vault, old, new, apply=False)


class _Backend:
    def __init__(self, store):
        self.store = store


def fake_keyring(monkeypatch):
    store = {("quiet-memo", "DEEPSEEK_API_KEY"): "synthetic-secret"}
    module = SimpleNamespace(
        store=store,
        get_keyring=lambda: _Backend(store),
        get_password=lambda service, name: store.get((service, name)),
        set_password=lambda service, name, value: store.__setitem__((service, name), value),
        delete_password=lambda service, name: store.pop((service, name), None),
    )
    monkeypatch.setitem(__import__("sys").modules, "keyring", module)
    return module


def test_keyring_dry_run_and_apply(tmp_path, monkeypatch):
    fake = fake_keyring(monkeypatch)
    assert "1" in migrate_mod._migrate_keyring(False)
    assert ("syvrio", "DEEPSEEK_API_KEY") not in fake.store
    text = migrate_mod._migrate_keyring(True)
    assert "1" in text
    assert fake.store[("syvrio", "DEEPSEEK_API_KEY")] == "synthetic-secret"
    assert ("quiet-memo", "DEEPSEEK_API_KEY") not in fake.store
    assert "synthetic-secret" not in text


def test_keyring_conflict_stops(tmp_path, monkeypatch):
    fake = fake_keyring(monkeypatch)
    fake.store[("syvrio", "DEEPSEEK_API_KEY")] = "different"
    with pytest.raises(migrate_mod.MigrationError, match="不同值"):
        migrate_mod._migrate_keyring(False)
