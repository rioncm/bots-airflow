import sys
from pathlib import Path

from bots_airflow import _runtime_support
from bots_airflow._core_discovery import find_local_botscore_checkout
from bots_airflow.bootstrap import _resolve_core_runtime


def test_find_local_botscore_checkout_prefers_standalone_src(tmp_path):
    project_root = tmp_path / 'bots_airflow'
    project_root.mkdir()

    standalone_package = tmp_path / 'bots_edi' / 'botscore' / 'src' / 'botscore'
    standalone_package.mkdir(parents=True)
    (standalone_package / '__init__.py').write_text('', encoding='utf-8')

    legacy_package = tmp_path / 'bots_edi' / 'bots' / 'botscore'
    legacy_package.mkdir(parents=True)
    (legacy_package / '__init__.py').write_text('', encoding='utf-8')

    resolved = find_local_botscore_checkout(project_root)

    assert resolved == (
        standalone_package.parent.resolve(),
        standalone_package.resolve(),
    )


def test_runtime_support_uses_sibling_standalone_checkout(monkeypatch, tmp_path):
    project_root = tmp_path / 'bots_airflow'
    project_root.mkdir()

    standalone_root = tmp_path / 'bots_edi' / 'botscore' / 'src'
    standalone_package = standalone_root / 'botscore'
    standalone_package.mkdir(parents=True)
    (standalone_package / '__init__.py').write_text('', encoding='utf-8')

    original_path = list(sys.path)
    monkeypatch.setattr(_runtime_support, '_resolve_project_root', lambda: project_root)
    monkeypatch.setattr(
        _runtime_support.importlib.util,
        'find_spec',
        lambda _name: None,
    )
    monkeypatch.setattr(sys, 'path', [path for path in original_path if path != str(standalone_root)])

    _runtime_support.ensure_botscore_importable()

    assert sys.path[0] == str(standalone_root.resolve())


def test_bootstrap_resolves_sibling_standalone_checkout(monkeypatch, tmp_path):
    project_root = tmp_path / 'bots_airflow'
    project_root.mkdir()

    standalone_root = tmp_path / 'bots_edi' / 'botscore' / 'src'
    standalone_package = standalone_root / 'botscore'
    standalone_package.mkdir(parents=True)
    (standalone_package / '__init__.py').write_text('', encoding='utf-8')

    monkeypatch.setattr(
        'bots_airflow.bootstrap.importlib.util.find_spec',
        lambda _name: None,
    )

    resolved_root, resolved_package = _resolve_core_runtime(project_root)

    assert resolved_root == standalone_root.resolve()
    assert resolved_package == standalone_package.resolve()
