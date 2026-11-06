"""依赖边界：Application 纯 Python，核心层不反向依赖它。"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "syvrio"
FORBIDDEN_APP = ("textual", "rich", "typer", "syvrio.app")
CORE = ("agent", "memory", "retrieval", "llm", "infra")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
            # 相对导入的模块名（level 暂不展开，核心层反向导入必然出现 application）。
            if node.level and node.module:
                names.add(node.module)
    return names


def test_application_does_not_import_frontends():
    violations = []
    for path in (ROOT / "application").rglob("*.py"):
        for name in _imports(path):
            if name.startswith(FORBIDDEN_APP):
                violations.append(f"{path.name}: {name}")
    assert not violations, violations


def test_core_does_not_import_application():
    violations = []
    for package in CORE:
        for path in (ROOT / package).rglob("*.py"):
            for name in _imports(path):
                if name == "application" or name.startswith("syvrio.application"):
                    violations.append(f"{path.relative_to(ROOT)}: {name}")
    assert not violations, violations


def test_application_imports_without_textual_or_app():
    import importlib

    for name in (
        "syvrio.application",
        "syvrio.application.conversation",
        "syvrio.application.memory",
        "syvrio.application.settings",
        "syvrio.application.reflection",
        "syvrio.application.git",
        "syvrio.application.service",
    ):
        importlib.import_module(name)